from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
import sys
import os
import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from recommender import recommender
from database import get_db, init_db, User, SearchHistory, Favorite

app = FastAPI(title="PageSpark Book Recommendation API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Init DB on startup ───────────────────────────────
@app.on_event("startup")
def startup():
    init_db()

# ── Schemas ───────────────────────────────────────────
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=4)

class LoginRequest(BaseModel):
    username: str
    password: str

class RecommendationRequest(BaseModel):
    description: str = Field(default="")
    top_n: int = Field(default=5, ge=1, le=50)
    genre_filter: Optional[str] = None
    min_rating: Optional[float] = Field(default=None, ge=0, le=5)
    user_id: Optional[int] = None

class ChangePasswordRequest(BaseModel):
    user_id: int
    old_password: str
    new_password: str = Field(..., min_length=4)

class FavoriteRequest(BaseModel):
    user_id: int
    book_title: str
    book_author: Optional[str] = None
    book_url: Optional[str] = None
    book_rating: Optional[float] = None

# ── Auth Endpoints ────────────────────────────────────
@app.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(400, "Username already exists")
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(400, "Email already exists")
    user = User(username=req.username, email=req.email, password=hash_password(req.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Registration successful", "user": {
        "id": user.id, "username": user.username, "email": user.email, "role": user.role
    }}

@app.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or user.password != hash_password(req.password):
        raise HTTPException(401, "Invalid username or password")
    if not user.is_active:
        raise HTTPException(403, "Account is deactivated")
    return {"message": "Login successful", "user": {
        "id": user.id, "username": user.username, "email": user.email, "role": user.role
    }}

@app.put("/admin/users/{user_id}/reset-password")
def admin_reset_password(user_id: int, admin_id: int = Query(...), db: Session = Depends(get_db)):
    admin = db.query(User).filter(User.id == admin_id, User.role == "admin").first()
    if not admin:
        raise HTTPException(403, "Admin access required")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    user.password = hash_password("123456")
    db.commit()
    return {"message": "Password reset to 123456"}

@app.put("/users/change-password")
def change_password(req: ChangePasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == req.user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.password != hash_password(req.old_password):
        raise HTTPException(400, "Mật khẩu cũ không chính xác")
    user.password = hash_password(req.new_password)
    db.commit()
    return {"message": "Password updated successfully"}

# ── Recommend ─────────────────────────────────────────
@app.post("/recommend")
def get_recommendations(req: RecommendationRequest, db: Session = Depends(get_db)):
    try:
        results = recommender.recommend(req.description, req.top_n, req.genre_filter, req.min_rating)
        # Save search history if user_id provided
        if req.user_id:
            history = SearchHistory(
                user_id=req.user_id,
                query=req.description,
                genre_filter=req.genre_filter,
                results_count=len(results)
            )
            db.add(history)
            db.commit()
        return {"recommendations": results, "total": len(results), "query": req.description}
    except Exception as e:
        raise HTTPException(500, str(e))

# ── Favorites ─────────────────────────────────────────
@app.post("/favorites")
def add_favorite(req: FavoriteRequest, db: Session = Depends(get_db)):
    # Check if already exists
    existing = db.query(Favorite).filter(
        Favorite.user_id == req.user_id, 
        Favorite.book_title == req.book_title
    ).first()
    if existing:
        return {"message": "Already in favorites", "favorite_id": existing.id}
    
    fav = Favorite(
        user_id=req.user_id,
        book_title=req.book_title,
        book_author=req.book_author,
        book_url=req.book_url,
        book_rating=req.book_rating
    )
    db.add(fav)
    db.commit()
    db.refresh(fav)
    return {"message": "Added to favorites", "favorite_id": fav.id}

@app.get("/favorites/{user_id}")
def get_favorites(user_id: int, db: Session = Depends(get_db)):
    favs = db.query(Favorite).filter(Favorite.user_id == user_id).order_by(Favorite.created_at.desc()).all()
    return {"favorites": [
        {
            "id": f.id,
            "book_title": f.book_title,
            "book_author": f.book_author,
            "book_url": f.book_url,
            "book_rating": f.book_rating,
            "created_at": f.created_at
        } for f in favs
    ]}

@app.delete("/favorites/{fav_id}")
def remove_favorite(fav_id: int, db: Session = Depends(get_db)):
    fav = db.query(Favorite).filter(Favorite.id == fav_id).first()
    if not fav:
        raise HTTPException(404, "Favorite not found")
    db.delete(fav)
    db.commit()
    return {"message": "Favorite removed"}

# ── User Profile Stats ────────────────────────────────
@app.get("/users/{user_id}/stats")
def get_user_stats(user_id: int, db: Session = Depends(get_db)):
    search_count = db.query(SearchHistory).filter(SearchHistory.user_id == user_id).count()
    fav_count = db.query(Favorite).filter(Favorite.user_id == user_id).count()
    return {
        "search_count": search_count,
        "favorite_count": fav_count
    }

# ── Categories ────────────────────────────────────────
@app.get("/categories")
def get_categories():
    return {"categories": recommender.get_genres()}

# ── Admin Endpoints ───────────────────────────────────
@app.get("/admin/users")
def admin_get_users(admin_id: int = Query(...), db: Session = Depends(get_db)):
    admin = db.query(User).filter(User.id == admin_id, User.role == "admin").first()
    if not admin:
        raise HTTPException(403, "Admin access required")
    users = db.query(User).all()
    return {"users": [{
        "id": u.id, "username": u.username, "email": u.email,
        "role": u.role, "is_active": u.is_active,
        "created_at": u.created_at.isoformat() + "Z" if u.created_at else None
    } for u in users]}

@app.get("/admin/history")
def admin_get_history(admin_id: int = Query(...), db: Session = Depends(get_db)):
    admin = db.query(User).filter(User.id == admin_id, User.role == "admin").first()
    if not admin:
        raise HTTPException(403, "Admin access required")
    records = db.query(SearchHistory).order_by(SearchHistory.created_at.desc()).limit(100).all()
    result = []
    for r in records:
        user = db.query(User).filter(User.id == r.user_id).first()
        result.append({
            "id": r.id, "username": user.username if user else "Unknown",
            "query": r.query, "genre_filter": r.genre_filter,
            "results_count": r.results_count,
            "created_at": r.created_at.isoformat() + "Z" if r.created_at else None
        })
    return {"history": result}

@app.delete("/admin/users/{user_id}")
def admin_toggle_user(user_id: int, admin_id: int = Query(...), db: Session = Depends(get_db)):
    admin = db.query(User).filter(User.id == admin_id, User.role == "admin").first()
    if not admin:
        raise HTTPException(403, "Admin access required")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    user.is_active = not user.is_active
    db.commit()
    return {"message": f"User {'activated' if user.is_active else 'deactivated'}", "is_active": user.is_active}

@app.get("/admin/stats")
def admin_stats(admin_id: int = Query(...), db: Session = Depends(get_db)):
    admin = db.query(User).filter(User.id == admin_id, User.role == "admin").first()
    if not admin:
        raise HTTPException(403, "Admin access required")
    total_users = db.query(User).count()
    total_searches = db.query(SearchHistory).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    return {
        "total_users": total_users,
        "total_searches": total_searches,
        "active_users": active_users,
        "total_books": len(recommender.df) if recommender.df is not None else 0
    }

@app.get("/health")
def health_check():
    return {"status": "ok", "data_loaded": recommender.df is not None,
            "total_books": len(recommender.df) if recommender.df is not None else 0}

@app.get("/api")
def root():
    return {"message": "PageSpark API v3.0"}

# Mount frontend at root for single-deployment on Render
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

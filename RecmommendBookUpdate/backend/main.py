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
import pandas as pd

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from recommender import recommender
from database import get_db, init_db, User, SearchHistory, Favorite, UploadedBook

def append_book_to_csv(book):
    try:
        csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'goodreads_data.csv')
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            
            # Tránh trùng lặp sách trong CSV
            exists = ((df['Book'].str.lower().str.strip() == book.title.lower().strip()) & 
                      (df['Author'].str.lower().str.strip() == book.author.lower().strip())).any()
            if exists:
                print(f"[INFO] Book '{book.title}' by '{book.author}' already exists in CSV. Skipping append.")
                return
                
            next_idx = int(df['Unnamed: 0'].max() + 1) if 'Unnamed: 0' in df.columns and not df.empty else len(df)
            
            # Định dạng thể loại khớp với định dạng list trong Goodreads CSV: "['Genre1', 'Genre2']"
            genres_raw = book.genres or ''
            formatted_genres = ""
            if genres_raw:
                if not genres_raw.strip().startswith('['):
                    genres_list = [g.strip() for g in genres_raw.split(',') if g.strip()]
                    formatted_genres = str(genres_list)
                else:
                    formatted_genres = genres_raw.strip()

            new_row = {
                'Unnamed: 0': next_idx,
                'Book': book.title,
                'Author': book.author,
                'Description': book.description or '',
                'Genres': formatted_genres,
                'Avg_Rating': book.avg_rating or 0.0,
                'Num_Ratings': 0,
                'URL': book.url or '#',
                'Image_URL': book.image_url or ''
            }
            
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(csv_path, index=False)
            print(f"[INFO] Successfully appended book '{book.title}' to CSV at index {next_idx}.")
    except Exception as e:
        print(f"[ERROR] Failed to append book to CSV: {e}")

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

class BookUploadRequest(BaseModel):
    user_id: int
    title: str = Field(..., min_length=1, max_length=255)
    author: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=3000)
    genres: Optional[str] = Field(default=None, max_length=500)
    avg_rating: Optional[float] = Field(default=0.0, ge=0, le=5)
    url: Optional[str] = Field(default="#", max_length=500)
    image_url: Optional[str] = Field(default=None, max_length=500)

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

# ── User Search History ────────────────────────────────
@app.get("/users/{user_id}/history")
def get_user_history(user_id: int, db: Session = Depends(get_db)):
    records = db.query(SearchHistory).filter(SearchHistory.user_id == user_id).order_by(SearchHistory.created_at.desc()).limit(20).all()
    return {"history": [
        {
            "id": r.id,
            "query": r.query,
            "genre_filter": r.genre_filter,
            "results_count": r.results_count,
            "created_at": r.created_at
        } for r in records
    ]}

@app.delete("/users/{user_id}/history")
def clear_user_history(user_id: int, db: Session = Depends(get_db)):
    db.query(SearchHistory).filter(SearchHistory.user_id == user_id).delete(synchronize_session=False)
    db.commit()
    return {"message": "Search history cleared"}

# ── Categories ────────────────────────────────────
@app.get("/categories")
def get_categories():
    return {"categories": recommender.get_genres()}

# ── Book Upload & Approval ─────────────────────────────
@app.post("/books/upload")
def upload_book(req: BookUploadRequest, db: Session = Depends(get_db)):
    """Người dùng hoặc Admin đóng góp sách mới. Admin tự động được duyệt, User cần chờ duyệt."""
    user = db.query(User).filter(User.id == req.user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(404, "User not found or account is deactivated")

    is_admin = user.role == "admin"
    status = "approved" if is_admin else "pending"

    book = UploadedBook(
        title=req.title,
        author=req.author,
        description=req.description,
        genres=req.genres,
        avg_rating=req.avg_rating or 0.0,
        url=req.url or "#",
        image_url=req.image_url,
        status=status,
        uploaded_by_id=req.user_id,
        reviewed_at=datetime.utcnow() if is_admin else None
    )
    db.add(book)
    db.commit()
    db.refresh(book)

    # Nếu Admin thêm sách thì cập nhật ngay mô hình TF-IDF và ghi vào CSV
    if is_admin:
        append_book_to_csv(book)
        try:
            recommender.reload_data()
        except Exception as e:
            print(f"[WARNING] Recommender reload failed: {e}")

    return {
        "message": "Sách đã được thêm!" if is_admin else "Sách đã gửi! Vui lòng chờ Admin duyệt.",
        "book_id": book.id,
        "status": book.status
    }

@app.get("/users/{user_id}/uploads")
def get_user_uploads(user_id: int, db: Session = Depends(get_db)):
    """Lấy danh sách sách người dùng đã đóng góp kèm trạng thái duyệt."""
    books = db.query(UploadedBook).filter(
        UploadedBook.uploaded_by_id == user_id
    ).order_by(UploadedBook.created_at.desc()).all()
    return {"uploads": [{
        "id": b.id,
        "title": b.title,
        "author": b.author,
        "genres": b.genres,
        "avg_rating": b.avg_rating,
        "status": b.status,
        "rejection_reason": b.rejection_reason,
        "created_at": b.created_at,
        "reviewed_at": b.reviewed_at
    } for b in books]}

@app.get("/admin/pending-books")
def admin_get_pending_books(admin_id: int = Query(...), db: Session = Depends(get_db)):
    """Lấy danh sách sách đang chờ duyệt. Chỉ Admin."""
    admin = db.query(User).filter(User.id == admin_id, User.role == "admin").first()
    if not admin:
        raise HTTPException(403, "Admin access required")
    books = db.query(UploadedBook).order_by(UploadedBook.created_at.desc()).all()
    result = []
    for b in books:
        uploader = db.query(User).filter(User.id == b.uploaded_by_id).first()
        result.append({
            "id": b.id,
            "title": b.title,
            "author": b.author,
            "description": b.description,
            "genres": b.genres,
            "avg_rating": b.avg_rating,
            "url": b.url,
            "image_url": b.image_url,
            "status": b.status,
            "rejection_reason": b.rejection_reason,
            "uploaded_by": uploader.username if uploader else "Unknown",
            "created_at": b.created_at.isoformat() + "Z" if b.created_at else None,
            "reviewed_at": b.reviewed_at.isoformat() + "Z" if b.reviewed_at else None
        })
    return {"books": result, "pending_count": sum(1 for b in result if b["status"] == "pending")}

@app.put("/admin/books/{book_id}/approve")
def admin_approve_book(book_id: int, admin_id: int = Query(...), db: Session = Depends(get_db)):
    """Admin duyệt sách đóng góp. Sau khi duyệt sẽ cập nhật ngay mô hình AI."""
    admin = db.query(User).filter(User.id == admin_id, User.role == "admin").first()
    if not admin:
        raise HTTPException(403, "Admin access required")
    book = db.query(UploadedBook).filter(UploadedBook.id == book_id).first()
    if not book:
        raise HTTPException(404, "Book not found")
    book.status = "approved"
    book.reviewed_at = datetime.utcnow()
    db.commit()
    # Ghi vào file CSV
    append_book_to_csv(book)
    # Cập nhật mô hình TF-IDF ngay lập tức
    try:
        recommender.reload_data()
    except Exception as e:
        print(f"[WARNING] Recommender reload failed: {e}")
    return {"message": f"Sách '{book.title}' đã được duyệt và đưa vào hệ thống gợi ý!"}

@app.put("/admin/books/{book_id}/reject")
def admin_reject_book(book_id: int, admin_id: int = Query(...), reason: Optional[str] = Query(default=None), db: Session = Depends(get_db)):
    """Admin từ chối sách đóng góp."""
    admin = db.query(User).filter(User.id == admin_id, User.role == "admin").first()
    if not admin:
        raise HTTPException(403, "Admin access required")
    book = db.query(UploadedBook).filter(UploadedBook.id == book_id).first()
    if not book:
        raise HTTPException(404, "Book not found")
    book.status = "rejected"
    book.rejection_reason = reason
    book.reviewed_at = datetime.utcnow()
    db.commit()
    return {"message": f"Sách '{book.title}' đã bị từ chối."}

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

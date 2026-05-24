# 📚 PageSpark — AI Book Recommendation System

> **Content-based book recommendation system** sử dụng TF-IDF và Cosine Similarity, tích hợp hệ thống đăng nhập/đăng ký và Admin Dashboard.

---

## 🎯 Giới thiệu

**PageSpark** là ứng dụng web gợi ý sách thông minh. Người dùng mô tả loại sách mong muốn bằng ngôn ngữ tự nhiên, hệ thống phân tích ngữ nghĩa bằng **TF-IDF + Cosine Similarity** và trả về kết quả phù hợp nhất từ **~10,000 cuốn sách** Goodreads.

---

## 🏗️ Cấu trúc dự án

```
RecmommendBookUpdate/
├── backend/
│   ├── main.py              # FastAPI server & API endpoints
│   ├── recommender.py       # ML engine (TF-IDF + Cosine Similarity)
│   ├── database.py          # SQLAlchemy models (User, SearchHistory, Favorite)
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── index.html           # Trang đăng nhập / đăng ký
│   ├── app.html             # Trang tìm kiếm sách (sau đăng nhập)
│   ├── admin.html           # Admin Dashboard
│   ├── style.css            # CSS (Glassmorphism, dark mode)
│   └── script.js            # Client-side logic
├── data/
│   └── goodreads_data.csv   # Dataset sách từ Goodreads
├── README.md
└── PROPOSAL.md
```

---

## ⚙️ Công nghệ sử dụng

| Thành phần | Công nghệ |co
|---|---|
| **Backend** | Python, FastAPI, Uvicorn |
| **Database** | SQLite + SQLAlchemy ORM |
| **Machine Learning** | Scikit-learn (TF-IDF, Cosine Similarity), Pickle (Caching) |
| **Data Processing** | Pandas, NumPy |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript, Chart.js |
| **Security** | Built-in hashlib (SHA-256 Password Hashing) |
| **UI Design** | Glassmorphism, Lucide Icons, Google Fonts (Outfit) |

---

## 🚀 Hướng dẫn cài đặt & chạy

### 1. Yêu cầu
- Python 3.9+
- Trình duyệt web hiện đại

### 2. Cài đặt dependencies

```bash
cd backend
python -m pip install -r requirements.txt
py -m pip install -r requirements.txt(nếu trên lỗi thì gõ lệnh này)
```

### 3. Khởi động Backend

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
py -m uvicorn main:app --host 0.0.0.0 --port 8000(nếu trên lỗi thì gõ lệnh này)
```

> - API: `http://localhost:8000`
> - Swagger Docs: `http://localhost:8000/docs`
> - Admin mặc định: `admin` / `admin123`

### 4. Mở Frontend

Mở `frontend/index.html` trong trình duyệt hoặc dùng Live Server (VS Code).

---
1️⃣ Install Script
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1 Nếu bị chặn script: Set-ExecutionPolicy -Scope Process Bypass.\scripts\install.ps1 The script will:

Create a Python virtual environment.
Install backend dependencies from backend/requirements.txt.
Initialise the SQLite database (creates a default admin account).
Start the FastAPI backend on http://localhost:8000.
Open the frontend (frontend/index.html) in your default browser.
2️⃣ Test Accounts
Role	Username	Password
Admin	admin	admin123
Demo User Pun	1478

## 📡 API Endpoints

| Method | Endpoint | Mô tả |
|---|---|---|
| `POST` | `/register` | Đăng ký tài khoản |
| `POST` | `/login` | Đăng nhập |
| `PUT` | `/users/change-password` | Người dùng tự đổi mật khẩu |
| `PUT` | `/admin/users/{user_id}/reset-password` | Admin reset mật khẩu người dùng về `123456` |
| `POST` | `/recommend` | Gợi ý sách AI (ghi lịch sử nếu có user_id) |
| `GET` | `/categories` | Danh sách thể loại sách |
| `GET` | `/health` | Kiểm tra trạng thái API |
| `POST` | `/favorites` | Lưu sách vào danh sách yêu thích |
| `GET` | `/favorites/{user_id}` | Xem danh sách sách yêu thích của người dùng |
| `DELETE` | `/favorites/{fav_id}` | Xóa sách yêu thích |
| `GET` | `/users/{user_id}/stats` | Thống kê cá nhân (số lượt tìm kiếm và số sách yêu thích) |
| `GET` | `/admin/stats` | Thống kê hệ thống toàn diện (admin) |
| `GET` | `/admin/users` | Xem danh sách người dùng (admin) |
| `GET` | `/admin/history` | Xem lịch sử tìm kiếm toàn hệ thống (admin) |
| `DELETE` | `/admin/users/{id}` | Kích hoạt hoặc vô hiệu hóa tài khoản (admin) |

---

## ✨ Tính năng chính

- 🔐 **Bảo mật** — Mã hóa mật khẩu bằng thuật toán SHA-256
- 🔄 **Quản lý mật khẩu** — Admin có quyền Reset mật khẩu, User có thể tự Đổi mật khẩu
- 👑 **Admin Dashboard** — Quản lý users, xem lịch sử, biểu đồ thống kê (Chart.js), xuất dữ liệu (Export CSV)
- 🚀 **Tối ưu hiệu năng** — Hệ thống tự động cache ma trận TF-IDF (Pickle) giúp khởi động cực nhanh
- 🔍 **Tìm kiếm AI** — Phân tích ngữ nghĩa mô tả bằng TF-IDF & Cosine Similarity
- 🏷️ **Tìm kiếm linh hoạt** — Hỗ trợ tìm theo bộ lọc (Thể loại, Rating) ngay cả khi không nhập mô tả
- 🛡️ **Xử lý ngoại lệ** — Tự động lọc bỏ các truy vấn vô nghĩa để đảm bảo chất lượng kết quả
- 📊 **Sắp xếp kết quả** — Theo độ khớp, rating, hoặc A-Z
- 📖 **Modal chi tiết** — Click vào sách để xem thông tin đầy đủ
- 📜 **Lịch sử tìm kiếm** — Tự động lưu mỗi lần search
- ❤️ **Thư viện yêu thích (My Library)** — Người dùng có thể đánh dấu yêu thích sách (Heart) và xem lại trong Thư viện cá nhân
- 📊 **Thống kê cá nhân** — Hiển thị trực quan số lần tìm kiếm bằng AI và số sách đã lưu trong Thư viện cá nhân
- 🎨 **Giao diện premium** — Glassmorphism, dark mode, animations
- 📱 **Responsive** — Tương thích mọi kích thước màn hình

---

## 👥 Thành viên nhóm

| STT | Họ tên | MSSV | Vai trò |
|---|---|---|---|
| 1 | | | Backend & ML |
| 2 | | | Frontend & UI |

---

## 📄 Giấy phép

Dự án phục vụ học tập — Môn **Phát triển ứng dụng** — Năm học 2025-2026.

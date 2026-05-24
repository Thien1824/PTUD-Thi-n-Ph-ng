# 📚 PageSpark — AI Book Recommendation System

> **Content-based book recommendation system** sử dụng mô hình tìm kiếm lai Hybrid Search (TF-IDF + Keyword Boosting), tích hợp hệ thống đóng góp sách cộng đồng (User Contribution), phê duyệt thông minh (Admin Approval) và Admin Dashboard trực quan sinh động.

---

## 🎯 Giới thiệu

**PageSpark** là ứng dụng gợi ý sách thông minh đột phá. Độc giả chỉ cần mô tả cuốn sách mong muốn bằng ngôn ngữ tự nhiên, hệ thống phân tích ngữ nghĩa kết hợp tìm kiếm từ khóa nâng cao và trả về kết quả tối ưu nhất từ thư viện **hơn 10,000 cuốn sách** Goodreads. 

Dữ liệu sách liên tục được mở rộng thông qua tính năng **đóng góp sách từ cộng đồng** đã qua kiểm duyệt của Admin, tự động đồng bộ vào file CSV gốc và cập nhật thời gian thực vào mô hình học máy mà không cần khởi động lại máy chủ.

---

## 🏗️ Cấu trúc dự án

```
RecmommendBookUpdate/
├── backend/
│   ├── main.py              # FastAPI server & API endpoints (Đăng ký, gợi ý, đóng góp, phê duyệt)
│   ├── recommender.py       # ML Engine (Hybrid Search: TF-IDF + Keyword Boost, Chuẩn hóa Tiếng Việt)
│   ├── database.py          # SQLite + SQLAlchemy Models (User, SearchHistory, Favorite, UploadedBook)
│   └── requirements.txt     # Các thư viện Python cần thiết
├── frontend/
│   ├── index.html           # Trang Đăng nhập / Đăng ký tài khoản
│   ├── app.html             # Trang Tìm kiếm & Gợi ý Sách, Đóng góp Sách (User)
│   ├── admin.html           # Admin Dashboard (Quản lý User, Lịch sử, Phê duyệt Đóng góp, Đăng sách)
│   ├── style.css            # CSS thiết kế Glassmorphism & Dark Mode cao cấp
│   └── script.js            # Xử lý Logic Client-side & Tích hợp API
├── data/
│   └── goodreads_data.csv   # Dataset gốc hơn 10,000 cuốn sách từ Goodreads
├── scripts/
│   └── install.ps1          # PowerShell Script tự động hóa cài đặt venv, database & khởi chạy
├── README.md
└── PROPOSAL.md
```

---

## ⚙️ Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| **Backend** | Python, FastAPI, Uvicorn |
| **Cơ sở dữ liệu** | SQLite + SQLAlchemy ORM, File dữ liệu CSV |
| **Machine Learning** | Scikit-learn (TF-IDF, Cosine Similarity), Pandas, NumPy |
| **Thuật toán Tìm kiếm** | **Hybrid Search Model** (Cosine Similarity kết hợp Keyword Boosting và Regex Word Boundary `\b`) |
| **Tiền xử lý Ngôn ngữ** | `unicodedata` (NFKD normalization) hỗ trợ tìm kiếm Tiếng Việt không dấu / có dấu |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript, Chart.js |
| **Bảo mật** | Mã hóa mật khẩu SHA-256 (hashlib) |
| **UI Design** | Glassmorphism hiện đại, Dark Mode, Lucide Icons, Google Fonts (Outfit), Micro-animations |

---

## 🚀 Hướng dẫn cài đặt & chạy nhanh

### Cách 1: Chạy tự động bằng PowerShell Script (Khuyên dùng trên Windows)
Chỉ với 1 dòng lệnh duy nhất, script sẽ tự động tạo Virtual Environment, cài dependencies, tạo database, add tài khoản Admin mặc định, khởi động server backend và mở giao diện web:

1. Mở PowerShell tại thư mục dự án và chạy:
   ```powershell
   Set-ExecutionPolicy -Scope Process Bypass; .\scripts\install.ps1
   ```
2. Trang web sẽ tự động mở ra trên trình duyệt của bạn tại địa chỉ: `http://localhost:8000`.

### Cách 2: Cài đặt thủ công từng bước

#### 1. Cài đặt các thư viện Python:
```bash
cd backend
python -m pip install -r requirements.txt
```

#### 2. Khởi tạo Database (Tạo bảng SQLite & nạp Admin mặc định):
```bash
python -c "from database import init_db; init_db()"
```

#### 3. Khởi động Backend Server:
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```
> Server sẽ chạy tại: `http://localhost:8000`
> Tài liệu API Swagger: `http://localhost:8000/docs`

#### 4. Mở Frontend:
Chỉ cần mở file `frontend/index.html` trong trình duyệt web của bạn.

---

## 🔑 Tài khoản dùng thử mặc định

| Vai trò | Tên đăng nhập (Username) | Mật khẩu (Password) |
| :--- | :--- | :--- |
| **Quản trị viên (Admin)** | `admin` | `admin123` |
| **Người dùng Demo (User)** | `Pun` | `1478` |

---

## 📡 Danh sách API Endpoints

### 🔐 Hệ thống Xác thực & Người dùng
* `POST` | `/register` | Đăng ký tài khoản người dùng mới.
* `POST` | `/login` | Đăng nhập hệ thống (Mật khẩu kiểm tra bằng SHA-256).
* `PUT` | `/users/change-password` | Người dùng tự đổi mật khẩu cá nhân.
* `PUT` | `/admin/users/{user_id}/reset-password` | Admin reset mật khẩu người dùng về mặc định `123456`.

### 🔍 Tìm kiếm & Gợi ý Sách (AI + Hybrid)
* `POST` | `/recommend` | Gợi ý sách thông minh Hybrid Search (TF-IDF + Cosine Similarity kết hợp lọc Thể loại, Rating tối thiểu). Lưu lịch sử tự động.
* `GET` | `/categories` | Lấy danh sách thể loại sách tải động từ hệ thống.
* `GET` | `/health` | Kiểm tra trạng thái hệ thống và số lượng sách hiện tại.

### ❤️ Quản lý Thư viện yêu thích
* `POST` | `/favorites` | Lưu sách vào danh sách yêu thích.
* `GET` | `/favorites/{user_id}` | Xem danh sách sách yêu thích của người dùng.
* `DELETE` | `/favorites/{fav_id}` | Xóa sách khỏi danh sách yêu thích.

### 📚 Hệ thống Đóng góp & Phê duyệt Sách
* `POST` | `/books/upload` | User đóng góp sách mới (ở trạng thái `pending`). Admin đăng sách sẽ được duyệt ngay (`approved`).
* `GET` | `/users/{user_id}/uploads` | Xem lịch sử và trạng thái các sách đã đóng góp của cá nhân.
* `GET` | `/admin/pending-books` | Lấy danh sách toàn bộ sách chờ duyệt trên hệ thống (Chỉ Admin).
* `PUT` | `/admin/books/{book_id}/approve` | Admin duyệt sách đóng góp, ghi đè vào CSV gốc, reload mô hình AI thời gian thực (Chỉ Admin).
* `PUT` | `/admin/books/{book_id}/reject` | Admin từ chối sách đóng góp kèm lý do phản hồi (Chỉ Admin).

### 👑 Quản trị hệ thống (Admin Dashboard)
* `GET` | `/admin/stats` | Lấy các số liệu thống kê tổng quan hệ thống (tổng user, tổng sách, tổng lượt tìm kiếm) để vẽ biểu đồ Chart.js.
* `GET` | `/admin/users` | Lấy danh sách người dùng.
* `DELETE` | `/admin/users/{user_id}` | Vô hiệu hóa hoặc Kích hoạt lại tài khoản người dùng.
* `GET` | `/admin/history` | Xem lịch sử tìm kiếm của toàn bộ hệ thống.

---

## ✨ Các tính năng nâng cấp nổi bật

1. **Mô hình Tìm kiếm Lai (Hybrid Search Engine):**
   * Giải quyết hoàn hảo lỗi OOV (Out-Of-Vocabulary) của TF-IDF khi tìm các tên riêng hoặc nhân vật hư cấu hiếm gặp (Ví dụ: "Boruto", "Shin-chan", "Conan").
   * Kết hợp điểm tương đồng cosine và **Keyword Boost Score** (sử dụng regex `\b` định giới từ chính xác, tránh trùng substring sai như tìm từ "chan" bị dính "change").
   * **Tìm kiếm Tiếng Việt không dấu:** Sử dụng module `unicodedata` chuẩn hóa NFKD để loại bỏ dấu tiếng Việt trong cả truy vấn của người dùng và kho sách, giúp tìm "cau be but chi" ra chính xác "Cậu bé bút chì".

2. **Hot Reloading & Đồng bộ CSV thông minh:**
   * Ngay sau khi Admin nhấn **Duyệt sách** hoặc **Đăng sách trực tiếp**, hệ thống tự động ghi thêm (append) sách đó vào file CSV `data/goodreads_data.csv` gốc.
   * Chỉ số ID (`Unnamed: 0`) được tính nối tiếp tự động chính xác để bảo toàn dữ liệu gốc. 
   * Cơ chế tự động bỏ qua nếu phát hiện sách bị trùng tiêu đề + tác giả để tránh rác cơ sở dữ liệu.
   * Máy chủ tự động chạy `recommender.reload_data()` để tính lại ma trận vector hóa TF-IDF ngay lập tức. Người dùng có thể tìm thấy cuốn sách mới vừa duyệt ngay trên giao diện mà không cần restart server FastAPI!

3. **Giao diện Dashboard Quản lý cao cấp:**
   * Thêm các Tab mới trên **Admin Dashboard** để theo dõi và xử lý phê duyệt sách chờ duyệt trong 1-click hoặc từ chối kèm nhập lý do trực quan.
   * Thêm biểu mẫu đăng sách trực tiếp siêu nhanh cho Admin.
   * Bộ lọc Thể loại trên trang chủ User được tải động trực tiếp từ CSV giúp tự động hiển thị thể loại mới khi sách mới có thể loại đặc biệt được phê duyệt.
   * Trang Lịch sử đóng góp sách hiển thị trực quan các tag trạng thái Glassmorphism: `Chờ duyệt` (Vàng), `Đã duyệt` (Xanh lá), `Từ chối` (Đỏ kèm lý do di chuột xem chi tiết).

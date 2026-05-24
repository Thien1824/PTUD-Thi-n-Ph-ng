# 📝 BẢN ĐỀ XUẤT DỰ ÁN & KỊCH BẢN DEMO
**Tên dự án:** PageSpark — AI Book Recommendation System
**Môn học:** Phát triển ứng dụng
**Năm học:** 2025 - 2026

---

## 1. 🎯 Bối cảnh & Lý do chọn đề tài
- **Vấn đề (Problem):** Khi đứng trước hàng ngàn cuốn sách, độc giả thường bối rối không biết nên chọn sách nào. Các hệ thống tìm kiếm truyền thống chỉ cho phép lọc theo "từ khóa cứng" (như tên tác giả, thể loại), gây khó khăn khi người đọc chỉ có một "cảm xúc" hoặc "ý tưởng" về nội dung muốn đọc.
- **Giải pháp (Solution):** Xây dựng **PageSpark** - hệ thống gợi ý sách thông minh cho phép người dùng tìm kiếm bằng **ngôn ngữ tự nhiên** (VD: "Tôi đang buồn và muốn đọc một cuốn sách chữa lành về cuộc sống"). Hệ thống sử dụng Machine Learning để phân tích ngữ nghĩa và trả về những cuốn sách có nội dung tương đồng nhất.

---

## 2. ⚙️ Kiến trúc hệ thống & Công nghệ
Hệ thống được thiết kế tối ưu với mô hình Client-Server hiện đại:
- **Backend:** Python, FastAPI (Tốc độ cao, hỗ trợ bất đồng bộ).
- **Cơ sở dữ liệu:** SQLite + SQLAlchemy ORM (Gọn nhẹ, dễ triển khai).
- **Trí tuệ nhân tạo (AI/ML):** Sử dụng `TfidfVectorizer` để chuyển đổi ngôn ngữ thành vector và `cosine_similarity` từ thư viện Scikit-learn để đo lường độ tương đồng. Áp dụng `pickle` để cache mô hình, giúp server khởi động siêu tốc.
- **Frontend:** HTML5, CSS3, Vanilla JavaScript, Chart.js (Thiết kế Glassmorphism hiện đại).

---

## 3. 👥 Thành viên & Phân công công việc
- **Thành viên 1 (Backend & Machine Learning):** Thiết kế database, tiền xử lý dữ liệu (~10.000 sách từ Goodreads), huấn luyện mô hình (TF-IDF), và xây dựng toàn bộ hệ thống API bằng FastAPI.
- **Thành viên 2 (Frontend & UI/UX):** Thiết kế giao diện (UI/UX) theo phong cách hiện đại (Glassmorphism, Dark mode), lập trình Frontend, tích hợp API và tối ưu hóa trải nghiệm người dùng.

---

## 4. ✨ Các chức năng nổi bật của PageSpark
### 👤 Phía Người dùng (User)
1. **Tìm kiếm bằng AI:** Phân tích ngữ nghĩa mô tả của người dùng để gợi ý sách. Hỗ trợ tự động dịch truy vấn tiếng Việt sang tiếng Anh.
2. **Khám phá linh hoạt:** Tìm kiếm kết hợp bộ lọc (Thể loại, Đánh giá tối thiểu).
3. **Thư viện cá nhân (My Library):** Lưu các cuốn sách yêu thích.
4. **Bảo mật:** Đăng nhập/Đăng ký an toàn với mật khẩu mã hóa SHA-256. Có chức năng đổi mật khẩu.

### 👑 Phía Quản trị viên (Admin)
1. **Admin Dashboard:** Bảng điều khiển tổng quan với biểu đồ thống kê (Chart.js).
2. **Quản lý hệ thống:** Xem danh sách tài khoản, vô hiệu hóa tài khoản, reset mật khẩu người dùng.
3. **Phân tích dữ liệu:** Theo dõi lịch sử tìm kiếm để nắm bắt xu hướng người đọc, xuất dữ liệu ra file CSV.


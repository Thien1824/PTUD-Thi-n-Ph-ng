# 📝 BẢN ĐỀ XUẤT DỰ ÁN & KỊCH BẢN DEMO
**Tên dự án:** PageSpark — AI Book Recommendation System
**Môn học:** Phát triển ứng dụng
**Năm học:** 2025 - 2026

---

## 1. 🎯 Bối cảnh & Lý do chọn đề tài
- **Vấn đề (Problem):** Khi đứng trước hàng ngàn cuốn sách, độc giả thường bối rối không biết nên chọn sách nào. Các hệ thống tìm kiếm truyền thống chỉ cho phép lọc theo "từ khóa cứng" (như tên tác giả, thể loại), gây khó khăn khi người đọc chỉ có một "cảm xúc" hoặc "ý tưởng" về nội dung muốn đọc. Đồng thời, dữ liệu sách cần được cập nhật liên tục từ cộng đồng đọc giả nhưng vẫn phải đảm bảo tính kiểm duyệt của quản trị viên.
- **Giải pháp (Solution):** Xây dựng **PageSpark** - hệ thống gợi ý sách thông minh cho phép người dùng tìm kiếm bằng **ngôn ngữ tự nhiên** kết hợp **từ khóa thông minh**. Đặc biệt phát triển tính năng **Đóng góp sách cộng đồng** và **Duyệt sách thời gian thực**, tự động cập nhật vào cơ sở dữ liệu lớn mà không làm gián đoạn hệ thống.

---

## 2. ⚙️ Kiến trúc hệ thống & Công nghệ
Hệ thống được thiết kế tối ưu với mô hình Client-Server hiện đại:
- **Backend:** Python, FastAPI (Tốc độ cao, hỗ trợ bất đồng bộ).
- **Cơ sở dữ liệu:** SQLite + SQLAlchemy ORM (Gọn nhẹ, dễ triển khai) kết hợp lưu trữ file dữ liệu lớn dạng **CSV** (`goodreads_data.csv`) đồng bộ thời gian thực.
- **Trí tuệ nhân tạo (AI/ML):**
  - **Mô hình Hybrid Search Model nâng cao:** Kết hợp điểm tương đồng ngữ nghĩa **TF-IDF + Cosine Similarity** từ Scikit-learn cùng cơ chế **Keyword Boosting** (sử dụng regex `\b` định giới từ chính xác).
  - **Chuẩn hóa tiếng Việt không dấu:** Sử dụng thư viện `unicodedata` để đưa các truy vấn tiếng Việt có dấu/không dấu về dạng chuẩn hóa, giúp độc giả dễ dàng tìm kiếm sách tiếng Việt và tiếng Anh.
  - **Hot Reloading:** Cơ chế tự động chạy `recommender.reload_data()` để tính toán lại ma trận TF-IDF ngay khi sách mới được Admin duyệt thành công mà không cần khởi động lại máy chủ.
- **Frontend:** HTML5, CSS3, Vanilla JavaScript, Chart.js (Thiết kế phong cách **Glassmorphism & Dark Mode** hiện đại, mượt mà với các hiệu ứng micro-animations).

---

## 3. 👥 Thành viên & Phân công công việc
- **Thành viên 1 (Backend & Machine Learning):** Thiết kế database mở rộng, phát triển cơ chế đồng bộ CSV an toàn, xây dựng thuật toán tìm kiếm lai Hybrid Search tối ưu hóa OOV (Out-of-vocabulary) và chuẩn hóa ngôn ngữ, phát triển các API đóng góp sách & phê duyệt.
- **Thành viên 2 (Frontend & UI/UX):** Thiết kế giao diện Dashboard quản lý đóng góp sách của Admin, giao diện đóng góp và xem lịch sử trạng thái duyệt của User, tối ưu hóa bộ lọc thể loại động (dynamic genres) và tích hợp các API mượt mà.

---

## 4. ✨ Các chức năng nổi bật của PageSpark

### 👤 Phía Người dùng (User)
1. **Tìm kiếm bằng AI & Từ khóa Lai (Hybrid Search):** Tìm kiếm sách thông minh bằng cả mô tả ngữ nghĩa và từ khóa đặc biệt (như tên nhân vật "Boruto", "Shin-chan"). Tự động tìm kiếm không dấu tiếng Việt.
2. **Khám phá linh hoạt:** Bộ lọc Thể loại động (tự động cập nhật theo các thể loại sách mới được duyệt) và bộ lọc Đánh giá tối thiểu.
3. **Đóng góp sách mới (Book Contribution):** Người dùng có thể điền thông tin sách để đóng góp vào thư viện chung. Trạng thái sách sẽ hiển thị ở dạng Chờ duyệt (`pending`), Đã duyệt (`approved`), hoặc Bị từ chối (`rejected` kèm lý do rõ ràng).
4. **Thư viện cá nhân (My Library):** Lưu các cuốn sách yêu thích để đọc sau.
5. **Bảo mật:** Đăng nhập/Đăng ký an toàn với mật khẩu mã hóa SHA-256. Có chức năng đổi mật khẩu.

### 👑 Phía Quản trị viên (Admin)
1. **Admin Dashboard:** Bảng điều khiển trực quan sinh động với biểu đồ thống kê tương tác (Chart.js), theo dõi tổng số sách thời gian thực.
2. **Duyệt sách đóng góp (Approval System):** Xem danh sách sách chờ duyệt, phê duyệt để đưa sách vào cơ sở dữ liệu ngay lập tức, hoặc từ chối kèm phản hồi lý do cho người dùng.
3. **Đăng sách trực tiếp (Direct Upload):** Admin có thể upload sách trực tiếp, tự động duyệt và đồng bộ vào hệ thống gợi ý ngay lập tức.
4. **Quản lý hệ thống:** Quản lý tài khoản người dùng (vô hiệu hóa/kích hoạt), reset mật khẩu người dùng về mật khẩu mặc định `123456`.
5. **Phân tích dữ liệu:** Theo dõi lịch sử tìm kiếm toàn hệ thống và xuất báo cáo CSV.



THÔNG TIN ĐỀ TÀI
Mã lớp: ABDA433708
Mã nhóm: 24126058
Tên đề tài: TikiLens – Hệ thống hỗ trợ phân tích và ra quyết định cho thương mại điện tử Tiki

CẤU TRÚC
source-code: mã nguồn ứng dụng, cấu hình mẫu và kiểm thử.
reports: báo cáo quy trình, báo cáo kỹ thuật, báo cáo thành viên 1 và tài liệu chỉnh chương 4–5.
dataset: dữ liệu tham chiếu dự báo được cung cấp kèm dự án.
refs: tài liệu tham khảo của dự án (bổ sung danh mục riêng nếu giảng viên yêu cầu).
libs: danh sách thư viện Python trong requirements.txt.

CÀI ĐẶT VÀ CHẠY
1. Cài Python tương thích.
2. Mở PowerShell trong thư mục source-code.
3. Chạy: python -m venv .venv
4. Chạy: .\.venv\Scripts\Activate.ps1
5. Chạy: pip install -r ..\libs\requirements.txt
6. Tạo .streamlit\secrets.toml từ secrets.toml.example và tự cấu hình MongoDB URI cùng khóa thiết lập Admin. Không chia sẻ secrets.toml.
7. Chạy: streamlit run app.py

DỮ LIỆU VÀ BẢO MẬT
Ứng dụng sử dụng dữ liệu MongoDB Atlas của nhóm; bộ dữ liệu thô không được đóng gói trong repo này. Tệp secrets.toml, tài khoản cục bộ và dữ liệu cá nhân không nằm trong bộ nộp. Không đưa thông tin kết nối hoặc mật khẩu lên GitHub.

THÀNH VIÊN
Nguyễn Đại Hào – MSSV 24126053.
Thông tin thành viên còn lại: nhóm bổ sung theo danh sách chính thức.

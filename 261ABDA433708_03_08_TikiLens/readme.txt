THÔNG TIN ĐỀ TÀI
Môn học: Ứng dụng Phân tích Dữ liệu lớn trong Kinh doanh (Big Data)
Mã lớp môn học: 261ABDA433708_03
Học kỳ: HK 1, năm học 2026–2027
Đề tài: Nghiên cứu và xây dựng hệ thống phân tích hiệu quả kinh doanh và hỗ trợ ra quyết định trên sàn thương mại điện tử Tiki Việt Nam.

THÔNG TIN NHÓM
STT nhóm: 08
Tên thư mục: 261ABDA433708_03_08_TikiLens

THÀNH VIÊN NHÓM
STT 01: Trần Quốc Hảo (NT) – MSSV 24126058 – Hoàn thành 100%
STT 02: Trần Minh Chiến – MSSV 24126026 – Hoàn thành 100%
STT 03: Vũ Trần Chiến – MSSV 24126027 – Hoàn thành 100%
STT 04: Nguyễn Đại Hào – MSSV 24126053 – Hoàn thành 100%
STT 05: Hồ Quân Bảo – MSSV 24126014 – Hoàn thành 100%
Trưởng nhóm: Trần Quốc Hảo – MSSV 24126058 – SĐT 0905851593 – Email hao056878@gmail.com.

CẤU TRÚC THƯ MỤC
source-code: toàn bộ mã nguồn và kiểm thử chương trình.
reports: bảng tự chấm LabF hiện có.
dataset: dữ liệu tham chiếu dự báo dùng trong chương trình.
refs: ghi chú vị trí danh mục tài liệu tham khảo.
libs: danh sách phần mềm và thư viện trong requirements.txt.
readme.txt: thông tin đề tài và nhóm.

CÀI ĐẶT VÀ CHẠY
Từ thư mục gốc repo, cài thư viện bằng pip install -r 261ABDA433708_03_08_TikiLens/libs/requirements.txt, cấu hình .streamlit/secrets.toml từ tệp mẫu ở gốc repo, rồi chạy streamlit run app.py.

DỮ LIỆU
Dữ liệu sản phẩm chính được truy cập từ MongoDB Atlas. Repo chứa forecast_reference.csv làm snapshot tham chiếu dự báo. Không đưa secrets.toml, database tài khoản hoặc dữ liệu cá nhân vào gói nộp.

----- Thông tin đề tài --------------------
STT: 08
Tên đề tài: Nghiên cứu và xây dựng hệ thống phân tích hiệu quả kinh doanh và hỗ trợ ra quyết định trên sàn thương mại điện tử Tiki Việt Nam.
Lớp học phần: 261ABDA433708_03
Năm học: HK1/2026-2027
------------------------------------------
Thông tin nhóm
1. Trần Quốc Hảo (24126058) - Trưởng nhóm - SĐT: 0905851593 - Email: hao056878@gmail.com
2. Trần Minh Chiến (24126026)
3. Vũ Trần Chiến (24126027)
4. Nguyễn Đại Hào (24126053)
5. Hồ Quân Bảo (24126014)

CẤU TRÚC HỒ SƠ
source-code: mã ứng dụng, kiểm thử, xử lý dữ liệu, thí nghiệm Python/Orange và file Power BI.
reports: slide PDF, bảng tự chấm, tài liệu pipeline và kết quả thí nghiệm đã lưu.
dataset: đủ năm CSV sạch (45.330 bản ghi), gồm sản phẩm, reviews, nhà bán, danh mục, CausaSent và bộ tham chiếu dự báo riêng.
refs: danh sách nguồn dữ liệu và tài liệu phần mềm liên quan.
libs: requirements.txt và danh sách phần mềm.
readme.txt: thông tin đề tài, nhóm và hướng dẫn tổng quát.

CÀI ĐẶT VÀ CHẠY
1. Giải nén ZIP và mở thư mục 261ABDA433708_03_08_TikiLens.
2. Cài thư viện: python -m pip install -r libs/requirements.txt
3. Chuyển vào source-code. Tạo .streamlit/secrets.toml theo secrets.toml.example và điền kết nối MongoDB được cấp, hoặc đặt biến môi trường TIKI_MONGO_URI.
4. Chạy: python -m streamlit run app.py
5. Xem source-code/README.md để biết cách cấu hình tài khoản và chạy thí nghiệm.
Không kèm mật khẩu, URI thật hay database xác thực trong hồ sơ nộp.

TRẠNG THÁI HỒ SƠ NGÀY 01/11/2026
- Đã có báo cáo chính do nhóm cung cấp: reports/BC_BIGDATA_Nhom_8.docx và reports/BC_BIGDATA_Nhom_8.pdf. Giữ nguyên nội dung hai tệp đầu vào.
- Chưa có bảng phân công được nhóm xác nhận trong gói này. Danh sách thành viên không thay thế bảng phân công.
- Báo cáo, slide và bảng tự chấm là bản do nhóm cung cấp; chưa kiểm tra lại tính nhất quán toàn bộ nội dung khi tải lên.
- Đã kèm đủ năm CSV sạch, tổng 45.330 bản ghi; tên/mã khách hàng trong reviews được thay bằng mã đại diện nhất quán. CSV là dạng xuất phẳng, không phải backup BSON; ứng dụng vẫn cần kết nối MongoDB được cấu hình riêng. Không kèm tài khoản database.
- Video chưa được cung cấp (mục tùy chọn theo hướng dẫn).
- Cần xác nhận bảng phân công và cấu hình môi trường chạy trước khi nộp chính thức.

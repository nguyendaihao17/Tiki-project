# TikiLens - Hồ sơ đồ án Big Data

- **Đề tài:** Nghiên cứu và xây dựng hệ thống phân tích hiệu quả kinh doanh và hỗ trợ ra quyết định trên sàn thương mại điện tử Tiki Việt Nam.
- **Lớp học phần:** `261ABDA433708_03` · **Nhóm:** `08` · **Học kỳ:** HK1/2026-2027.
- **Ứng dụng:** [tikilens.streamlit.app](https://tikilens.streamlit.app/).

## Cấu trúc hồ sơ nộp

[Thư mục hồ sơ](261ABDA433708_03_08_TikiLens/) và [gói ZIP](261ABDA433708_03_08_TikiLens.zip) được đặt tên theo mẫu `<Mã lớp>_<STT nhóm>_<Tên đề tài>`.

```text
261ABDA433708_03_08_TikiLens/
├── source-code/   Mã ứng dụng, xử lý dữ liệu, thí nghiệm, kiểm thử, Power BI
├── reports/       Báo cáo Word/PDF, slide, bảng tự chấm, phân công, phụ lục
├── dataset/       Năm CSV sạch và bộ dữ liệu tham chiếu dự báo
├── refs/          Danh mục nguồn dữ liệu và tài liệu tham khảo
├── libs/          requirements.txt và danh sách phần mềm
└── readme.txt     Thông tin đề tài, thành viên, hướng dẫn chạy, trạng thái hồ sơ
```

ZIP chứa đúng một thư mục gốc như trên. Các file chạy ở gốc repo (`app.py`, `requirements.txt`, `.streamlit`) phục vụ Streamlit Cloud và nằm ngoài gói hồ sơ nộp. Cache, môi trường Python, tệp tạm và secrets thật không được đóng vào ZIP.

## Thành viên

| STT | Họ và tên | MSSV | Hoàn thành theo xác nhận của nhóm |
|---:|---|---|---:|
| 1 | Trần Quốc Hảo - Trưởng nhóm | 24126058 | 100% |
| 2 | Trần Minh Chiến | 24126026 | 100% |
| 3 | Vũ Trần Chiến | 24126027 | 100% |
| 4 | Nguyễn Đại Hào | 24126053 | 100% |
| 5 | Hồ Quân Bảo | 24126014 | 100% |

**Liên hệ trưởng nhóm:** 0905851593 · hao056878@gmail.com.

## Tài liệu và dữ liệu

| Thành phần | Vị trí |
|---|---|
| Báo cáo chính | [Word](261ABDA433708_03_08_TikiLens/reports/BC_BIGDATA_Nhom_8.docx) · [PDF](261ABDA433708_03_08_TikiLens/reports/BC_BIGDATA_Nhom_8.pdf) |
| Slide thuyết trình, 15 trang | [Slide PDF](261ABDA433708_03_08_TikiLens/reports/SLIDE_BIGDATA_Nhom_8.pdf) |
| Biểu mẫu tự chấm và phân công | [LabF](261ABDA433708_03_08_TikiLens/reports/LabF_bang-tu-cham.pdf) |
| Pipeline chuẩn hóa | [Tài liệu phần 2](261ABDA433708_03_08_TikiLens/reports/Pipeline_Phan2.docx) |
| Power BI | [TIKILENS_VN.pbix](261ABDA433708_03_08_TikiLens/source-code/powerbi/TIKILENS_VN.pbix) |
| Dữ liệu | [Dataset và mô tả](261ABDA433708_03_08_TikiLens/dataset/README.md) |
| Nguồn tham khảo | [Danh mục](261ABDA433708_03_08_TikiLens/refs/README.txt) |
| Phần mềm và thư viện | [Danh sách](261ABDA433708_03_08_TikiLens/libs/SOFTWARE.txt) · [requirements.txt](261ABDA433708_03_08_TikiLens/libs/requirements.txt) |

Năm CSV sạch có **45.330 bản ghi**. `forecast_reference.csv` được trích từ cùng dữ liệu sản phẩm để tái hiện dự báo, không cộng thêm vào tổng này. Trong reviews, tên và mã khách hàng đã được thay bằng mã đại diện nhất quán; các trường khác giữ nguyên.

## Chạy chương trình

- **Từ gói ZIP:** thực hiện theo [readme.txt](261ABDA433708_03_08_TikiLens/readme.txt) và [hướng dẫn trong source-code](261ABDA433708_03_08_TikiLens/source-code/README.md).
- **Từ gốc repo GitHub:** cài thư viện từ `261ABDA433708_03_08_TikiLens/libs/requirements.txt`, cấu hình MongoDB riêng theo `.streamlit/secrets.toml.example`, rồi chạy `python -m streamlit run app.py`.

Mã chuẩn bị dữ liệu: [data-pipeline](261ABDA433708_03_08_TikiLens/source-code/data-pipeline/README.md). Thí nghiệm độc lập: [Isolation Forest Python/Orange](261ABDA433708_03_08_TikiLens/source-code/experiments/isolation-forest/README.md) và [phân cụm/dự báo](261ABDA433708_03_08_TikiLens/source-code/experiments/seller-clustering-forecast/README.md).

## Kiểm tra trước khi nộp

- Biểu mẫu LabF đã có thông tin lớp/nhóm, 18 hạng mục được đánh dấu và bảng phân công đúng 5 thành viên, hoàn thành 100% theo xác nhận của nhóm. Ngày/chữ ký để trống cho nhóm xác nhận; video, vấn đáp, độ khó và tổng điểm không tự đánh giá.
- Ứng dụng cần kết nối MongoDB và tài khoản được cấp riêng. CSV là dữ liệu xuất phẳng, không phải backup BSON và không tự thay thế kết nối của app.
- Video chưa được cung cấp; đây là mục tùy chọn theo hướng dẫn của giảng viên.

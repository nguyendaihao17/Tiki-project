# TikiLens – Hồ sơ đồ án Big Data

- **Mã lớp:** `261ABDA433708_03`
- **Nhóm:** `08`
- **Học kỳ:** HK 1, năm học 2026–2027
- **Đề tài:** Nghiên cứu và xây dựng hệ thống phân tích hiệu quả kinh doanh và hỗ trợ ra quyết định trên sàn thương mại điện tử Tiki Việt Nam.

## Cấu trúc nộp bài

Toàn bộ hồ sơ dự án đặt trong thư mục [`261ABDA433708_03_08_TikiLens`](261ABDA433708_03_08_TikiLens/), theo mẫu `<Mã lớp>_<STT nhóm>_<Tên đề tài>`. Thư mục này gồm `source-code`, `reports`, `dataset`, `refs`, `libs` và `readme.txt`, theo cấu trúc giảng viên cung cấp.

`app.py`, `requirements.txt` và `.streamlit` ở gốc repo được giữ làm điểm chạy tương thích với Streamlit Cloud.

## Thành viên nhóm

| STT | Họ và tên | MSSV | Hoàn thành |
|---:|---|---:|---:|
| 01 | Trần Quốc Hảo (NT) | 24126058 | 100% |
| 02 | Trần Minh Chiến | 24126026 | 100% |
| 03 | Vũ Trần Chiến | 24126027 | 100% |
| 04 | Nguyễn Đại Hào | 24126053 | 100% |
| 05 | Hồ Quân Bảo | 24126014 | 100% |

**Trưởng nhóm:** Trần Quốc Hảo – 24126058
**Điện thoại:** 0905851593
**Email:** hao056878@gmail.com

## Chạy ứng dụng

Tại thư mục gốc repo, tạo môi trường Python, cài thư viện từ `261ABDA433708_03_08_TikiLens/libs/requirements.txt`, cấu hình `.streamlit/secrets.toml` từ tệp mẫu và chạy:

```powershell
streamlit run app.py
```

App Cloud tiếp tục dùng wrapper ở gốc và chạy mã chính tại `261ABDA433708_03_08_TikiLens/source-code/app.py`.

## Mã chuẩn bị dữ liệu và thí nghiệm

- [Thu thập, nhập và kiểm tra dữ liệu](261ABDA433708_03_08_TikiLens/source-code/data-pipeline/README.md): các script độc lập từ Drive của nhóm, kèm hướng dẫn cấu hình và tác động khi chạy.
- [Isolation Forest bằng Python và Orange](261ABDA433708_03_08_TikiLens/source-code/experiments/isolation-forest/README.md): notebook, workflow Orange, CSV sản phẩm và kết quả thí nghiệm đã lưu.
- [Phân cụm nhà bán và dự báo lượng bán](261ABDA433708_03_08_TikiLens/source-code/experiments/seller-clustering-forecast/README.md): mã thí nghiệm K-Means, Linear Regression và Random Forest từ hai CSV sạch.

## Dữ liệu

Dữ liệu sản phẩm chính được đọc từ MongoDB Atlas. Repo đã kèm năm CSV sạch với 45.330 bản ghi, cùng `forecast_reference.csv` để tái hiện phần đánh giá dự báo. Tên và mã khách hàng trong CSV reviews đã được thay bằng mã đại diện nhất quán. Không commit secrets, database tài khoản hoặc dữ liệu cá nhân.

## Gói nộp theo cấu trúc giảng viên

File `261ABDA433708_03_08_TikiLens.zip` chứa đúng một thư mục hồ sơ với năm thư mục quy định và `readme.txt`. File chạy, requirements và `.streamlit` ở gốc repo phục vụ Streamlit Cloud; gói nộp có cấu hình mẫu và hướng dẫn riêng trong `source-code`.

Power BI đặt tại `source-code/powerbi`, CSV đặt trong `dataset`, kết quả thí nghiệm đã lưu đặt trong `reports/experiments`. Đã loại cấu hình phát triển, cache, test rỗng và các bản mã trùng/không được app gọi khỏi gói.

**Chưa phải bản nộp hoàn chỉnh:** cần xác nhận bảng phân công và môi trường chạy MongoDB; CSV dữ liệu sạch đã đủ năm tập (45.330 bản ghi). Trạng thái được ghi rõ trong `readme.txt`; không tự thay bằng bản nháp hoặc khai tỷ lệ hoàn thành.

Báo cáo chính do nhóm cung cấp ngày 01/11/2026: [Word](261ABDA433708_03_08_TikiLens/reports/BC_BIGDATA_Nhom_8.docx) và [PDF](261ABDA433708_03_08_TikiLens/reports/BC_BIGDATA_Nhom_8.pdf).

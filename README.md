# TikiLens – Hồ sơ đồ án Big Data

- **Mã lớp:** `261ABDA433708_03`
- **Nhóm:** `08`
- **Học kỳ:** HK 1, năm học 2026–2027
- **Đề tài:** Nghiên cứu và xây dựng hệ thống phân tích hiệu quả kinh doanh và hỗ trợ ra quyết định trên sàn thương mại điện tử Tiki Việt Nam.

## Cấu trúc nộp bài

Toàn bộ hồ sơ dự án đặt trong thư mục [`261ABDA433708_03_08_TikiLens`](261ABDA433708_03_08_TikiLens/), theo mẫu `<Mã lớp>_<STT nhóm>_<Tên đề tài>`. Thư mục này gồm `source-code`, `reports` (bảng tự chấm LabF), `dataset`, `refs`, `libs` và `readme.txt`.

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

## Dữ liệu

Dữ liệu sản phẩm chính được đọc từ MongoDB Atlas. Repo có snapshot `forecast_reference.csv` để tái hiện phần đánh giá dự báo; dữ liệu đầy đủ cần được bổ sung nếu barem yêu cầu nộp dataset. Không commit secrets, database tài khoản hoặc dữ liệu cá nhân.

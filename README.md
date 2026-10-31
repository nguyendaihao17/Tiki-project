# TikiLens – Hồ sơ đồ án Big Data

- **Môn học:** Ứng dụng Phân tích Dữ liệu lớn trong Kinh doanh (Big Data)
- **Mã lớp:** `261ABDA433708_03`
- **Học kỳ:** HK 1, năm học 2026–2027
- **Đề tài:** Nghiên cứu và xây dựng hệ thống phân tích hiệu quả kinh doanh và hỗ trợ ra quyết định trên sàn thương mại điện tử Tiki Việt Nam.

Ứng dụng TikiLens gồm dashboard, khám phá dữ liệu, phân cụm, dự báo, phát hiện bất thường và quản trị dữ liệu.

## Cấu trúc repo
- `source-code/`: mã nguồn ứng dụng, kiểm thử và cấu hình phát triển.
- `reports/`: báo cáo quy trình, báo cáo kỹ thuật, báo cáo thành viên 1 và chỉnh sửa chương 4–5.
- `dataset/`: dữ liệu tham chiếu dự báo được sử dụng trong mã.
- `refs/`: ghi chú về danh mục tài liệu tham khảo trong báo cáo.
- `libs/requirements.txt`: danh sách thư viện Python.
- `readme.txt`: thông tin đề tài, thành viên và hướng dẫn nộp.

Tệp `app.py` và `requirements.txt` ở gốc là điểm vào tương thích cho Streamlit Cloud; mã ứng dụng và danh sách thư viện chính thức nằm trong các thư mục nêu trên.

## Thành viên nhóm

| STT | Họ và tên | MSSV | Hoàn thành |
|---:|---|---:|---:|
| 01 | Trần Quốc Hào (NT) | 24126058 | 100% |
| 02 | Trần Minh Chiến | 24126026 | 100% |
| 03 | Vũ Trần Chiến | 24126027 | 100% |
| 04 | Nguyễn Đại Hào | 24126053 | 100% |
| 05 | Hồ Quân Bảo | 24126014 | 100% |

**Trưởng nhóm:** Trần Quốc Hào – 24126058.

## Chạy cục bộ (PowerShell)
Tại thư mục gốc repo:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r libs/requirements.txt
Copy-Item .streamlit/secrets.toml.example .streamlit/secrets.toml
# Điền mongo_uri và initial_admin_setup_key vào secrets.toml (không đưa tệp thật lên GitHub)
streamlit run app.py
```

Streamlit Cloud tiếp tục chạy `app.py` ở gốc; wrapper chuyển vào ứng dụng thực trong `source-code/app.py`. Không cần đổi đường dẫn ứng dụng trong phần cài đặt Cloud.

## Dữ liệu và bảo mật
Ứng dụng đọc dữ liệu sản phẩm từ MongoDB Atlas. Dataset đầy đủ không được đưa vào repo vì hiện không có bản dữ liệu xuất phù hợp; `dataset/forecast_reference.csv` là snapshot tham chiếu dùng cho đánh giá dự báo. Secrets, SQLite người dùng và dữ liệu cá nhân không được commit.

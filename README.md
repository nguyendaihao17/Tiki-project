# TikiLens – Hồ sơ dự án ABDA433708 / Nhóm 24126058

Ứng dụng phân tích thương mại điện tử Tiki, gồm dashboard, khám phá dữ liệu, phân cụm, dự báo, phát hiện bất thường và quản trị dữ liệu.

## Cấu trúc repo
- `source-code/`: mã nguồn ứng dụng, kiểm thử và cấu hình phát triển.
- `reports/`: báo cáo quy trình, kỹ thuật, thành viên 1 và chỉnh sửa chương 4–5.
- `dataset/`: dữ liệu tham chiếu dự báo được sử dụng trong mã.
- `refs/`: ghi chú về vị trí danh mục tham khảo; hiện danh mục nằm trong các báo cáo.
- `libs/requirements.txt`: danh sách thư viện Python.
- `readme.txt`: thông tin nộp bài và hướng dẫn ngắn.

Tệp `app.py` và `requirements.txt` ở gốc là điểm vào tương thích cho Streamlit Cloud; mã ứng dụng và danh sách thư viện chính thức nằm trong các thư mục nêu trên.

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
Ứng dụng đọc dữ liệu sản phẩm từ MongoDB Atlas. Dataset đầy đủ không được đưa vào repo vì hiện không có bản dữ liệu xuất phù hợp trong thư mục dự án; `dataset/forecast_reference.csv` là snapshot tham chiếu được dùng cho phần đánh giá dự báo. Secrets, SQLite người dùng và dữ liệu cá nhân không được commit.

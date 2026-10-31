# TikiLens

Ứng dụng Streamlit gồm dashboard, khám phá dữ liệu, phân cụm, dự báo, phát hiện bất thường và quản trị. Thư mục này có thể chạy trực tiếp từ gói ZIP, không phụ thuộc file chạy tương thích ở gốc repo GitHub.

## Chạy từ gói nộp

Tại thư mục `261ABDA433708_03_08_TikiLens`, cài `python -m pip install -r libs/requirements.txt`, rồi chuyển vào `source-code`.

Tạo `.streamlit/secrets.toml` từ tệp `.streamlit/secrets.toml.example`, điền `mongo_uri` được cấp; có thể dùng biến môi trường `TIKI_MONGO_URI` thay thế. Chạy `python -m streamlit run app.py`.

Ứng dụng đọc dữ liệu kinh doanh từ database `tikilens_vn` và lưu tài khoản riêng trong `tikilens_auth`. Tài khoản và mật khẩu không nằm trong gói nộp. Dùng tài khoản được nhóm cấp; trên môi trường mới cần khởi tạo quản trị viên bằng `python -m src.auth` và thực hiện theo lời nhắc. Không đổi kết nối của hệ thống thật để thử nhập hoặc phục hồi dữ liệu.

## Thành phần

- `app.py`, `src/`, `webapp/`, `static/`: mã ứng dụng đang sử dụng.
- `tests/`: kiểm thử. Từ thư mục này chạy `python -m unittest discover -s tests`.
- `data-pipeline/`: thu thập, nhập và kiểm tra dữ liệu; đọc README trước khi chạy vì một số script ghi MongoDB.
- `experiments/`: thí nghiệm Python và Orange độc lập, không tự chạy cùng app. Các CSV đầu vào đặt ở `../dataset`; kết quả đã lưu nằm ở `../reports/experiments`.
- `powerbi/TIKILENS_VN.pbix`: mã báo cáo Power BI, mở bằng Power BI Desktop. Nếu làm mới dữ liệu, cần cấu hình lại nguồn phù hợp trên máy người xem.

Trang dự báo của app dùng `../dataset/forecast_reference.csv` cố định. Các trang còn lại cần MongoDB và không tự chuyển sang CSV khi mất kết nối. Các thí nghiệm không thay thế hoặc ghi đè module của ứng dụng.

Gói không chứa môi trường Python, cache, secrets thật hay database tài khoản. Tình trạng các tài liệu còn thiếu được ghi trong `../readme.txt`.

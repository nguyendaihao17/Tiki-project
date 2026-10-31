# TikiLens — Hướng dẫn sử dụng

Ứng dụng Streamlit phân tích dữ liệu sản phẩm Tiki, có dashboard, khám phá dữ liệu, mô hình học máy và trang quản trị.

## Bắt đầu nhanh (Windows)

Mở PowerShell tại thư mục dự án `Tiki Project`, rồi chạy:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Sao chép `.streamlit/secrets.toml.example` thành `.streamlit/secrets.toml` và điền chuỗi kết nối MongoDB của nhóm, hoặc đặt biến môi trường `TIKI_MONGO_URI`. Tệp `secrets.toml` đã được loại khỏi mã nguồn chia sẻ. Nếu chuỗi kết nối cũ từng được đẩy lên Git, hãy đổi mật khẩu MongoDB và xử lý lịch sử Git.

### Tạo tài khoản lần đầu

Nếu chưa có tài khoản, tạo Admin từ terminal tin cậy:

```powershell
python -m src.auth
```

Nhập tên đăng nhập, tên hiển thị và mã PIN chỉ gồm chữ số, dài tối đa 6 số. Khi nhập PIN, terminal **không hiện ký tự hoặc dấu `*`**; cứ gõ PIN rồi nhấn Enter.

### Chạy ứng dụng

```powershell
streamlit run app.py
```

Mở địa chỉ hiện trong terminal (thường là `http://localhost:8501`). Sau khi Admin đầu tiên được tạo, người dùng có thể chọn **Đăng ký** trên trang đầu để tạo tài khoản Người dùng; tài khoản mới được đăng nhập ngay sau khi tạo.

> Nếu đã tạo môi trường ảo và cài thư viện trước đó, chỉ cần kích hoạt môi trường rồi chạy `streamlit run app.py`.

## Dùng các chức năng chính

1. Đăng nhập bằng tài khoản hiện có hoặc chọn **Đăng ký** để tạo tài khoản Người dùng. Nếu quên mã PIN, liên hệ Admin để đặt lại.
2. Chọn trang tại thanh điều hướng bên trái:
   - **Phân tích & Dashboard**: xem biểu đồ, áp dụng bộ lọc và xuất báo cáo.
   - **Khám phá & Lọc dữ liệu**: tìm mã/tên sản phẩm hoặc khách hàng; lọc và xuất dữ liệu.
   - **Chất lượng dữ liệu**: quy mô dữ liệu và độ đầy đủ của các trường quan trọng.
   - **Phân cụm khách hàng & nhà bán**, **Dự báo**, **Phát hiện bất thường**: chạy các phân tích tương ứng.
   - **Quản trị dữ liệu & Báo cáo**: chỉ Admin được truy cập; quản lý sản phẩm, người dùng, sao lưu, phục hồi và báo cáo.
3. Dữ liệu được cache tối đa 5 phút. Nhấn **Làm mới dữ liệu** ở thanh bên để tải lại từ MongoDB sớm hơn.
4. Ở trang Khám phá hoặc Dashboard, dùng các nút tải xuống để xuất CSV/Excel.

## Xử lý nhanh sự cố

- **Không kết nối được dữ liệu**: kiểm tra Internet, quyền truy cập MongoDB Atlas và chuỗi kết nối trong `.streamlit/secrets.toml` hoặc biến môi trường `TIKI_MONGO_URI`.
- **Không đăng nhập được**: xác nhận đã tạo tài khoản bằng `python -m src.auth` và nhập đúng tên đăng nhập/PIN.
- **PIN không hiện khi nhập**: đây là hành vi bình thường của `getpass`; nhập xong rồi nhấn Enter.
- **Dữ liệu chưa cập nhật**: nhấn **Làm mới dữ liệu**; sau thao tác CRUD, cache sản phẩm được làm mới.

---

## Chi tiết chức năng

### Tổng quan và dashboard

- KPI: doanh thu ước tính, số lượng đã bán, lượt và điểm đánh giá, sản phẩm và nhà bán.
- Dashboard lọc theo danh mục, giá, TikiNOW và Freeship Xtra cho toàn bộ phân tích; ngày đánh giá chỉ lọc các chỉ số và biểu đồ đánh giá.
- Bảy góc nhìn: cơ cấu kinh doanh (Pareto doanh thu danh mục, phân khúc giá, danh mục cần ưu tiên phản hồi); phản hồi khách hàng (xu hướng và phân bố số sao, tỷ lệ 1–2 sao theo danh mục); sản phẩm và nhà bán (mức tập trung doanh thu, sản phẩm điểm thấp đã bán, quan hệ giảm giá/điểm/lượng bán); giá và khuyến mãi (nhóm mức giảm, lượng bán bình quân, khoảng giá 25–75%); dịch vụ giao hàng (độ phủ TikiNOW/Freeship Xtra, tỷ trọng và lượng bán bình quân theo tổ hợp dịch vụ); tập trung doanh thu (tỷ trọng doanh thu của Top 1%/10% sản phẩm, đường tích lũy và danh mục trong nhóm dẫn đầu); độ phủ đánh giá (nhóm lượt đánh giá trên sản phẩm, sản phẩm đã bán chưa có đánh giá và tỷ lệ có đánh giá theo danh mục).
- Doanh thu là ước tính từ ảnh chụp sản phẩm, không phải doanh thu giao dịch theo ngày. Xu hướng theo thời gian chỉ dùng ngày đánh giá; phân tích tỷ lệ theo danh mục cần tối thiểu 30 đánh giá hợp lệ.
- So sánh lượng đã bán theo mức giảm giá và dịch vụ là mô tả trên ảnh chụp, chưa chứng minh tác động nhân quả của khuyến mãi hoặc giao hàng.
- Có thể tải KPI, bảng danh mục và dữ liệu sau lọc ra CSV; Excel bổ sung các bảng mức giảm, khoảng giá, dịch vụ giao hàng, tập trung doanh thu và độ phủ đánh giá.

### Khám phá dữ liệu

- Tìm mã/tên sản phẩm; tìm mã/tên khách hàng trong dữ liệu đánh giá.
- Lọc theo danh mục, xuất xứ sản phẩm, đơn giá, số lượng đã bán và ngày đánh giá.
- Có thông báo khi không có kết quả; dữ liệu phù hợp có thể xuất ra CSV hoặc Excel.
- Dữ liệu hiện không có mã hóa đơn/order ID hay quốc gia khách hàng. Ngày lọc là ngày đánh giá, không đại diện cho ngày giao dịch.

### Phân tích và mô hình

- **Phân cụm khách hàng**: K-Means nhóm khách hàng theo hành vi đánh giá: tần suất, điểm đánh giá, độ biến động điểm, tỷ lệ đánh giá tiêu cực và số sản phẩm đã đánh giá. Không có lịch sử mua hàng/chi tiêu nên đây không phải phân cụm RFM mua hàng.
- **Phân cụm nhà bán hàng**: K-Means nhóm nhà bán theo số sản phẩm, số lượng đã bán, doanh thu ước tính, lượt đánh giá và điểm đánh giá trung bình. Dữ liệu là ảnh chụp sản phẩm nên đây không phải phân cụm RFM giao dịch theo thời gian.
- **Dự báo**: Random Forest ước tính số lượng bán từ thuộc tính sản phẩm; dữ liệu hiện không phải chuỗi thời gian doanh số.
- **Phát hiện bất thường**: Isolation Forest tìm sản phẩm có tổ hợp chỉ số khác biệt; kết quả thống kê không tự động đồng nghĩa với lỗi hay gian lận.

### Quản trị, CRUD và báo cáo

- Người dùng thường có thể xem các chức năng phân tích; chỉ Admin có quyền quản lý dữ liệu và tài khoản. Quyền được kiểm tra tại lớp xử lý thao tác.
- CRUD sản phẩm gồm xem danh sách/chi tiết, thêm, sửa, xóa mềm và khôi phục. Đầu vào được kiểm tra; doanh thu ước tính được tính lại khi cập nhật giá/số lượng.
- Sản phẩm xóa mềm được loại khỏi dashboard và báo cáo sản phẩm; đánh giá liên quan được giữ lại.
- Báo cáo quản trị hỗ trợ tải dữ liệu sản phẩm CSV và workbook Excel gồm KPI, thống kê danh mục và dữ liệu sản phẩm.

### Sao lưu và phục hồi

- Admin có thể tạo tệp ZIP sao lưu các collection `clean_*` nằm trong allowlist.
- Tệp sao lưu được kiểm tra cấu trúc, collection và số bản ghi trước khi phục hồi.
- Phục hồi chỉ được ghi vào database thử nghiệm có hậu tố `_restore_test` (mặc định `tikilens_vn_restore_test`); **không phục hồi vào database dữ liệu nhóm**.
- Cần nhập đúng tên database thử nghiệm để xác nhận thao tác thay thế dữ liệu tại database đích.
- Nhật ký ghi thời gian UTC, tài khoản, trạng thái và số lượng bản ghi; được lưu bền vững trong MongoDB Atlas.

## Cài đặt chi tiết

### Yêu cầu

- Python tương thích với các phiên bản thư viện trong `requirements.txt`.
- Kết nối Internet và quyền truy cập MongoDB Atlas của dự án.

### Windows PowerShell

Tại thư mục dự án:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Nếu PowerShell không cho phép kích hoạt môi trường ảo, có thể gọi trực tiếp:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\streamlit.exe run app.py
```

## Dữ liệu và hiệu năng

- Ứng dụng chỉ truy cập collection được khai báo trong allowlist `CLEAN_COLLECTIONS`; các luồng phân tích dùng dữ liệu `clean_*`, không đọc collection `raw_*`.
- Dữ liệu sản phẩm và đánh giá được tải riêng theo nhu cầu trang, chỉ lấy các trường cần thiết và cache 5 phút.
- Nút **Làm mới dữ liệu** ở thanh bên xóa cache để tải dữ liệu mới từ MongoDB.

## Tài khoản và cấu hình cục bộ

- Không có tài khoản/mật khẩu mặc định hoặc tài khoản mẫu trong mã nguồn. Khi triển khai Streamlit Cloud, thêm `initial_admin_setup_key` (tối thiểu 16 ký tự) vào Secrets để mở biểu mẫu tạo Admin đầu tiên; sau đó trang đăng ký công khai chỉ tạo tài khoản quyền Người dùng. Khi chạy cục bộ, có thể dùng `python -m src.auth`.
- Tài khoản và nhật ký sao lưu/phục hồi mặc định được lưu trong MongoDB Atlas ở database riêng `tikilens_auth`, tách khỏi dữ liệu sản phẩm; PIN được băm bằng bcrypt.
- Khi cần chạy bộ kiểm tra cục bộ, có thể đặt `TIKI_AUTH_DB_PATH` để dùng SQLite tạm thời.
- Có thể đổi tên database đích khi phục hồi bằng `TIKI_RESTORE_TEST_DB_NAME`, nhưng giá trị phải khác database nhóm và kết thúc bằng `_restore_test`.
- Có thể đặt `TIKI_BACKUP_AUDIT_DB_PATH` để chuyển nhật ký sang SQLite cục bộ khi chạy bộ kiểm tra.
- Không đưa database tài khoản, thông tin xác thực hoặc dữ liệu riêng tư lên Git.

## Cấu trúc dự án

```text
Tiki Project/
├── app.py
├── requirements.txt
├── readme_md.md
├── .streamlit/
│   └── config.toml
├── src/
│   ├── analytics.py
│   ├── auth.py
│   ├── backup.py
│   ├── crud.py
│   ├── database.py
│   └── reporting.py
└── webapp/
    ├── admin_page.py
    ├── anomaly_page.py
    ├── clustering_page.py
    ├── dashboard_page.py
    ├── explore_page.py
    ├── forecast_page.py
    └── overview_page.py
```

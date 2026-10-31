# Dữ liệu tham chiếu cho trang dự báo

`forecast_reference.csv` là 2.307 dòng đầy đủ được lấy, theo đúng thứ tự, từ
`tikilens_vn.clean_products.csv` trong tệp
`googlecollabsosanhpytvaorange-20261030T035304Z-1-001.zip` do nhóm cung cấp.
Tệp chỉ giữ 11 đặc trưng và `quantity_sold` dùng ở mục 4.2 của báo cáo
`Big data.pdf`; không chứa mã sản phẩm, tên người bán hay thông tin tài khoản.

Trang dự báo dùng ảnh chụp dữ liệu cố định này để tái tạo kết quả thí nghiệm.
Thao tác thêm, sửa, xóa sản phẩm trong MongoDB không thay đổi các chỉ số của
trang dự báo. Cần chạy lại và cập nhật dữ liệu tham chiếu nếu báo cáo thay đổi.

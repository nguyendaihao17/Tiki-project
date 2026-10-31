# Phân cụm nhà bán và dự báo lượng bán

Nguồn: hai file Python nhóm cung cấp có tên “code python khi đưa dữ liệu của 2 file csv”, bản có và không có chú thích. Chúng có cùng mã thực thi; chỉ giữ một bản có chú thích trong `seller_clustering_forecast.py`. Đã chuẩn hóa khoảng trắng và chỉnh đường dẫn CSV theo gói nộp, giữ logic mô hình.

## Nội dung

- K-Means nhóm nhà bán theo Recency, Frequency, Monetary thay thế, thử K=2..8 và chọn Silhouette Score lớn nhất.
- Linear Regression và Random Forest dự báo `quantity_sold` từ 11 thuộc tính sản phẩm; chia train/test 80/20 với random_state=42; đánh giá MAE, RMSE, R².

Recency trong mã là thời gian tính từ ngày thu thập, Frequency là số sản phẩm và Monetary là giá trị bán ước tính. Đây không phải lịch sử giao dịch mua hàng hay mô hình dự báo chuỗi thời gian.

## Chạy

Cài thư viện từ `libs/requirements.txt` ở gốc hồ sơ. Chạy `python seller_clustering_forecast.py` trong thư mục chứa script, hoặc gọi script bằng đường dẫn đầy đủ. Script tự xác định thư mục gốc và đọc hai tệp trong `dataset`:

- [tikilens_vn.clean_products.csv](../../../dataset/tikilens_vn.clean_products.csv).
- [tikilens_vn.clean_sellers.csv](../../../dataset/tikilens_vn.clean_sellers.csv).

Mã gốc vẫn đọc sellers dù chưa dùng `sellers_df` trong mô hình. Thống kê in ra màn hình và biểu đồ mở bằng Matplotlib; đóng cửa sổ biểu đồ để tiếp tục nếu môi trường chờ `plt.show()`. Script không kết nối MongoDB. Cần dữ liệu hợp lệ, đủ số nhà bán để thử K=2..8. Chưa xác nhận lại chỉ số thực nghiệm trong lần sắp xếp hồ sơ này.

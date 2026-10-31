# Phân cụm nhà bán và dự báo lượng bán

Mã thí nghiệm độc lập từ hai file nhóm cung cấp:

- `code python khi đưa dữ liệu của 2 file csv.py`.
- `code python khi đưa dữ liệu của 2 file csv sau khi bỏ chú thích.py`.

Hai file có cùng mã thực thi khi so sánh cây cú pháp Python, chỉ khác chú thích. Repo giữ một bản có chú thích, đổi tên thành `seller_clustering_forecast.py`; giữ nguyên logic và chú thích, chỉ chuẩn hóa khoảng trắng cuối dòng. Script không được app Streamlit tự động chạy và không kết nối MongoDB.

## Nội dung thí nghiệm

1. Nhóm theo `seller_id`, tính Recency từ `crawled_at`, Frequency từ số sản phẩm và Monetary từ tổng `revenue_estimate`. Chuẩn hóa ba đặc trưng, thử K-Means với K từ 2 đến 8 và chọn K có Silhouette Score cao nhất.
2. Dự báo `quantity_sold` bằng Linear Regression và Random Forest trên 11 thuộc tính sản phẩm; chia train/test 80/20 với `random_state=42`, đánh giá MAE, RMSE và R².

Các chỉ số được gọi là RFM trong mã là đặc trưng thay thế ở cấp nhà bán: ngày thu thập, số sản phẩm và giá trị bán ước tính. Chúng không phải lịch sử mua hàng hoặc RFM giao dịch của khách hàng. Dự báo lượng bán từ ảnh chụp sản phẩm cũng không phải dự báo chuỗi thời gian.

## Chuẩn bị và chạy

Cài thư viện theo `libs/requirements.txt` của dự án (cần NumPy, pandas, Matplotlib, seaborn và scikit-learn; `OneHotEncoder(sparse_output=False)` yêu cầu scikit-learn từ 1.2).

Đặt hai CSV trong **thư mục làm việc hiện tại** khi chạy:

- `tikilens_vn.clean_products.csv`: có thể dùng bản đi kèm [thí nghiệm Isolation Forest](../isolation-forest/tikilens_vn.clean_products.csv), sau khi kiểm tra các cột cần thiết.
- `tikilens_vn.clean_sellers.csv`: lấy từ bộ dữ liệu sạch của nhóm; chưa kèm trong thư mục này. Mã gốc vẫn đọc file này dù chưa dùng `sellers_df` trong các mô hình.

Từ thư mục chứa script và hai CSV, chạy `python seller_clustering_forecast.py`. Kết quả được in ra màn hình, các biểu đồ mở bằng Matplotlib; đóng cửa sổ biểu đồ để script tiếp tục nếu môi trường chờ `plt.show()`.

Giữ nguyên giả định của bản gốc về tên cột, kiểu dữ liệu, dữ liệu thiếu và số nhà bán đủ để thử K=2..8. Khi đóng gói đã kiểm tra cú pháp và sự tương đương giữa hai bản, chưa huấn luyện lại mô hình hoặc xác nhận các chỉ số thực nghiệm.

# Isolation Forest bằng Python và Orange

Nguồn: thư mục so sánh Python–Orange và workflow Isolation Forest của nhóm. Giữ logic mô hình gốc; notebook đã bỏ metadata tài khoản và chỉnh đường dẫn theo cấu trúc gói nộp.

## Vị trí các tệp

- `sosanhpythonvaorange.ipynb`: notebook Python.
- `isolation_forest.ows`: workflow Orange.
- [CSV sản phẩm](../../../dataset/tikilens_vn.clean_products.csv): 2.307 dòng đầu vào.
- [Kết quả đã lưu](../../../reports/experiments/isolation-forest/python_outliers_result.csv): 47 sản phẩm được mô hình Python đánh dấu bất thường trong lần chạy gốc.

## Chạy Python

Cài thư viện từ `libs/requirements.txt` ở gốc hồ sơ. Mở notebook bằng Jupyter với thư mục làm việc là thư mục chứa notebook (`source-code/experiments/isolation-forest`). Notebook đọc CSV từ `dataset` và ghi kết quả vào `reports/experiments/isolation-forest`, không kết nối MongoDB. Khi dùng Colab cần tải lên cả cấu trúc thư mục tương ứng và đặt lại working directory trước khi chạy.

Năm đầu vào: `price`, `discount_rate`, `quantity_sold`, `revenue_estimate`, `review_count`. Mô hình: `IsolationForest(contamination=0.02, random_state=42)`. Chạy lại sẽ ghi đè CSV kết quả; phiên bản thư viện có thể ảnh hưởng kết quả.

## Chạy Orange

Mở workflow bằng Orange3, tại CSV File Import chọn lại CSV trong `dataset`. Đã bỏ lịch sử đường dẫn tuyệt đối của máy thành viên; chọn CSV trong dataset trước khi chạy. Kiểm tra Select Columns → Outliers → Data Table và đối chiếu đầu vào, tiền xử lý, tham số trước khi so sánh với Python. Không khẳng định hai môi trường cho kết quả giống nhau.

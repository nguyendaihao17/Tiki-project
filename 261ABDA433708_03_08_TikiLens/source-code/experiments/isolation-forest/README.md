# Thí nghiệm Isolation Forest: Python và Orange

Nguồn: thư mục `googlecollabsosanhpytvaorange` và workflow `Thử nghiệm Isolation Forest.ows` trong Drive Big Data của nhóm. Notebook và CSV lấy từ bản tải `googlecollabsosanhpytvaorange-20261030T035304Z-1-001.zip`; workflow lấy từ bản `.ows` sẵn trên máy.

## Tệp đi kèm

- `sosanhpythonvaorange.ipynb`: notebook Colab gốc, bổ sung đuôi `.ipynb` và bỏ metadata tài khoản/phiên chạy; giữ mã và kết quả đã lưu.
- `tikilens_vn.clean_products.csv`: dữ liệu sản phẩm đầu vào để tái hiện thí nghiệm, không phải dữ liệu reviews hay kho tài khoản.
- `python_outliers_result.csv`: kết quả Python đã lưu từ lần chạy gốc.
- `isolation_forest.ows`: workflow Orange gốc, đổi tên tệp cho dễ truy cập.

## Python

Mở notebook bằng Jupyter hoặc Colab, đặt CSV sản phẩm trong cùng thư mục làm việc. Cần `pandas` và `scikit-learn` (có trong danh sách thư viện của dự án).

Notebook dùng 5 đặc trưng: `price`, `discount_rate`, `quantity_sold`, `revenue_estimate`, `review_count`, với `IsolationForest(contamination=0.02, random_state=42)`. Kết quả đã lưu ghi nhận **47 sản phẩm bất thường**; chạy lại sẽ ghi đè CSV kết quả trong thư mục làm việc. Phiên bản thư viện có thể ảnh hưởng kết quả chạy lại.

## Orange

Mở `isolation_forest.ows` bằng Orange3. Tại **CSV File Import**, chọn lại `tikilens_vn.clean_products.csv` trong thư mục này vì workflow gốc lưu đường dẫn tuyệt đối từ máy thành viên. Sau đó kiểm tra **Select Columns → Outliers → Data Table** và đối chiếu các đặc trưng/tham số với Python trước khi so sánh.

Các thiết lập workflow gốc được giữ nguyên; chưa xác nhận hai môi trường có cùng tiền xử lý hoặc kết quả giống nhau. Không cần cài Orange vào môi trường triển khai Streamlit.

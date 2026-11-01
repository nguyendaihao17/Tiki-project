# Dữ liệu kèm hồ sơ

Bộ CSV sạch chốt từ thư mục CK do nhóm xác nhận ngày 01/11/2026.

| Tệp | Số bản ghi |
|---|---:|
| `tikilens_vn.clean_products.csv` | 2.307 |
| `tikilens_vn.clean_reviews.csv` | 35.632 |
| `tikilens_vn.clean_sellers.csv` | 315 |
| `tikilens_vn.clean_categories.csv` | 10 |
| `tikilens_vn.clean_causasent.csv` | 7.066 |
| **Tổng 5 tập dữ liệu** | **45.330** |

`forecast_reference.csv` là bộ đặc trưng trích từ cùng 2.307 sản phẩm để tái hiện trang dự báo, không cộng thêm vào tổng trên. CausaSent có 7.066 document và 10.300 annotations.

Trong reviews, chỉ hai trường `customer_id` và `customer_name` được thay bằng mã đại diện nhất quán theo khách hàng như nhóm đã đồng ý. Có 27.312 nhóm khách hàng, giữ nguyên số review trong từng nhóm và các trường khác. Không đưa bảng đối chiếu hoặc khóa sinh mã lên GitHub. Bản CSV gốc trong CK được giữ nguyên trên máy.

Đã kiểm tra số lượng và liên kết reviews → products, products → sellers/categories. CSV giữ định dạng xuất phẳng của bản nhóm cung cấp, gồm các cột như `annotations[0].aspect_term` và `images[0]`; đây không phải backup BSON. Nếu nhập lại MongoDB, cần ánh xạ kiểu dữ liệu và cấu trúc mảng theo pipeline tương ứng. Ứng dụng vẫn đọc MongoDB Atlas, không tự đọc CSV thay thế. Không kèm tài khoản hoặc mật khẩu database.

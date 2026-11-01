# Dữ liệu

| Tệp | Số bản ghi |
|---|---:|
| `tikilens_vn.clean_products.csv` | 2.307 |
| `tikilens_vn.clean_reviews.csv` | 35.632 |
| `tikilens_vn.clean_sellers.csv` | 315 |
| `tikilens_vn.clean_categories.csv` | 10 |
| `tikilens_vn.clean_causasent.csv` | 7.066 |
| **Tổng** | **45.330** |

CausaSent có 7.066 document và 10.300 annotations. Nguồn dữ liệu được liệt kê trong `refs/README.txt`.

`forecast_reference.csv` giữ 11 đặc trưng và `quantity_sold` của cùng 2.307 sản phẩm để tái hiện đánh giá dự báo ở mục 4.2 báo cáo; không cộng thêm vào tổng bản ghi. Thay đổi dữ liệu sản phẩm trong MongoDB không làm thay đổi bộ tham chiếu này.

Trong reviews, `customer_id` và `customer_name` được thay bằng mã đại diện nhất quán. Vẫn giữ 27.312 nhóm khách hàng, số review của từng nhóm và các trường còn lại; không kèm bảng đối chiếu định danh.

CSV là dạng xuất phẳng, có các cột như `annotations[0].aspect_term` và `images[0]`. Khi nhập MongoDB cần khôi phục kiểu dữ liệu và cấu trúc mảng theo pipeline tương ứng; CSV không phải bản backup BSON.

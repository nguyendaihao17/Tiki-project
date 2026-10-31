# Dữ liệu kèm hồ sơ

| Tệp | Phạm vi | Nguồn trong hồ sơ nhóm |
|---|---|---|
| `forecast_reference.csv` | 2.307 dòng; các đặc trưng dùng để tái hiện trang dự báo | Snapshot đã được ứng dụng sử dụng, giữ nguyên |
| `tikilens_vn.clean_products.csv` | 2.307 sản phẩm; đầu vào Isolation Forest và thí nghiệm phân cụm/dự báo | Bản tải thư mục so sánh Python–Orange ngày 30/10/2026 |
| `tikilens_vn.clean_categories.csv` | 10 danh mục | Bản CSV sạch trong thư mục CK do nhóm lưu trên máy |
| `tikilens_vn.clean_sellers.csv` | 315 nhà bán | Bản CSV sạch trong thư mục CK do nhóm lưu trên máy |

Hai tệp sản phẩm có mục đích khác nhau: `forecast_reference.csv` chỉ giữ các đặc trưng của thí nghiệm dự báo; tệp sản phẩm đầy đủ giữ mã và thông tin mô tả cần cho thí nghiệm khác. Chúng không phải hai bản sao đồng nhất.

Ứng dụng đầy đủ vẫn đọc MongoDB Atlas. Gói này không chứa toàn bộ reviews, CausaSent hoặc kho xác thực. Không dùng gói như bản backup hoàn chỉnh của hệ thống. Các bảng reviews gốc có trường định danh/tên người dùng nên chưa được đưa vào gói công khai này; nhóm cần chuẩn bị bản dữ liệu phù hợp hoặc cơ chế truy cập được phép để phục vụ chấm bài.

CSV là dữ liệu dạng bảng; nếu nhập lại MongoDB cần kiểm tra kiểu dữ liệu và áp dụng pipeline chuẩn hóa tương ứng, không coi việc import CSV là phục hồi nguyên trạng BSON.

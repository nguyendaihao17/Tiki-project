# Chuẩn hóa trường mảng trong reviews

Nguồn: `SourceCode_Phan2.zip` do nhóm cung cấp. Thư mục này bổ sung bước chuẩn hóa các trường `images`, `product_attributes`, `vote_agree`, `vote_disagree` của collection `tikilens_vn.clean_reviews`.

## Các tệp

- `check_part2_connection.py`: kiểm tra kết nối và đếm reviews. Đổi tên từ `test_connection.py` để công cụ tìm test không tự kết nối MongoDB.
- `check_review_arrays.py`: thống kê kiểu dữ liệu của bốn trường, không sửa dữ liệu.
- `clean_review_arrays.py`: chuyển chuỗi JSON chứa mảng thành mảng BSON; giữ nguyên trường đã là mảng và kiểu dữ liệu khác. Chuỗi JSON lỗi hoặc không chứa mảng được ghi nhận là lỗi.
- [Pipeline_Phan2.docx](../../../reports/Pipeline_Phan2.docx): tài liệu gốc mô tả các pipeline chuẩn hóa, kiểm tra chất lượng, loại annotation trùng và kiểm tra liên kết giữa các collection. Tài liệu được giữ nguyên.

## Chạy thủ công

1. Trong thư mục này, cài thư viện bằng `python -m pip install -r ../requirements.txt`.
2. Tạo `.env` riêng tại đây với `MONGO_URI` là chuỗi kết nối của bạn; không đưa tệp này lên GitHub.
3. Chạy `python check_part2_connection.py`, rồi `python check_review_arrays.py` để kiểm tra.
4. Chạy `python clean_review_arrays.py` để xem thống kê các bản ghi cần chuyển đổi.

Đã đổi `APPLY_CHANGES` từ `True` trong bản đầu vào thành **`False`** để mặc định chỉ xem trước. Chỉ đổi thành `True` sau khi kiểm tra kết quả và chủ động muốn ghi vào `clean_reviews`; script dừng ghi nếu phát hiện lỗi JSON, và chia cập nhật thành các lô 500 bản ghi. Các lô không nằm trong một transaction chung.

Pipeline có `$out` trong tài liệu Word sẽ ghi/thay thế collection đích khi được chạy thủ công. Việc lưu mã và tài liệu vào repo không chạy pipeline hoặc thay đổi dữ liệu Atlas. Khi đóng gói chỉ kiểm tra ngoại tuyến, chưa chạy trên database thật.

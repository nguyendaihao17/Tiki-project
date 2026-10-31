# Thu thập, nhập và kiểm tra dữ liệu

Các script độc lập từ thư mục `Code` trên Drive của nhóm, bản tải ngày 28/10/2026 (`Code -20261028T082124Z-1-001.zip`). Chúng lưu lại quy trình chuẩn bị dữ liệu của đồ án và không được app Streamlit tự động chạy.

Đã thay đường dẫn Downloads cố định bằng thư mục chứa script; đổi `test_mongodb.py` thành `check_mongodb_connection.py` để công cụ kiểm thử không tự kết nối Atlas khi tìm test. Không kèm `.env`, backup hay log chứa dữ liệu.

## Chuẩn bị

Trong thư mục này, cài `python -m pip install -r requirements.txt`. Tạo tệp `.env` riêng với `MONGO_URI` là chuỗi kết nối Atlas của bạn. Biến này dành cho các script lịch sử; app Streamlit dùng cấu hình `TIKI_MONGO_URI`/`mongo_uri` riêng.

Đặt các CSV đầu vào tương ứng cạnh script nhập: `tiki_products_clean_full.csv`, `tiki_reviews.csv`, `tiki_categories.csv`, `tiki_sellers.csv`. Các tệp này không nằm trong gói mã nguồn này.

## Các bước và tác động

| Nhóm | Script | Tác động khi chạy |
|---|---|---|
| Thu thập Tiki | `tikilens_thu_thap_tiki_github.py` | Tải CSV công khai từ repo tham khảo, ghi vào `tikilens_acquisition/`; không ghi MongoDB. Chuyển CSV cần nhập ra cạnh script nhập. |
| Thu thập CausaSent | `tikilens_tai_nguon2_truc_tiep.py`, `tikilens_tai_nguon2.py` | Hai cách tải nguồn 2 vào `tikilens_source2/`; chọn một cách phù hợp. |
| Kết nối và khởi tạo | `check_mongodb_connection.py`, `setup_tikilens.py` | Script đầu kiểm tra kết nối; script sau tạo collection `raw_products` nếu chưa có. |
| Nhập Tiki | `import_tiki.py`, `import_tiki_categories.py`, `import_tiki_reviews.py`, `import_tiki_sellers.py` | Thêm/cập nhật dữ liệu trong MongoDB theo mã nghiệp vụ. |
| Nhập nguồn 2 | `tikilens_nhap_nguon2_atlas.py` | Kiểm tra manifest và nhập vào `raw_causasent_ate_v2`. |
| Kiểm tra chất lượng | `audit_tikilens.py`, `kiem_tra_chat_luong_tikilens.py`, `phan_tich_loi_tikilens.py`, `tikilens_kiem_tra_trung_nguon2.py` | Đọc MongoDB và xuất kết quả kiểm tra; không sửa dữ liệu. |
| Sao lưu/phục hồi thử | `tikilens_backup_atlas.py`, `tikilens_restore_test_atlas.py` | Xuất backup vào máy và phục hồi thử sang database `tikilens_restore_test`. |

Chỉ chạy từng script cần thiết, ví dụ `python kiem_tra_chat_luong_tikilens.py`. Các script nhập, khởi tạo và phục hồi có ghi dữ liệu; việc thêm chúng vào GitHub không thực hiện các thao tác đó.

## Chuẩn hóa dữ liệu phần 2

[Phần 2](part2/README.md) bổ sung ba script kiểm tra/chuyển đổi trường mảng trong `clean_reviews` và liên kết tới tài liệu `Pipeline_Phan2.docx` trong `reports/`, mô tả các pipeline từ `raw_*` sang `clean_*`.

Đây là mã quy trình lịch sử, chưa phải bộ pipeline tự động hoàn chỉnh từ dữ liệu thô đến toàn bộ collection `clean_*`. Chưa chạy lại các tác vụ mạng hoặc ghi Atlas khi đóng gói.

# Hướng dẫn chạy chương trình

## Ứng dụng Streamlit

Từ thư mục `261ABDA433708_03_08_TikiLens`, chạy:

```powershell
python -m pip install -r libs/requirements.txt
cd source-code
```

Tạo `.streamlit/secrets.toml` từ `.streamlit/secrets.toml.example` và điền `mongo_uri`, hoặc đặt biến môi trường `TIKI_MONGO_URI`. Ứng dụng dùng dữ liệu trong `tikilens_vn` và lưu tài khoản ở `tikilens_auth`. Trên môi trường mới, khởi tạo quản trị viên bằng `python -m src.auth`; sau đó chạy:

```powershell
python -m streamlit run app.py
```

Các trang dữ liệu cần MongoDB; app không tự thay kết nối bằng CSV. Trang dự báo dùng bộ `../dataset/forecast_reference.csv` cố định để tái hiện đánh giá mô hình. Không kèm thông tin đăng nhập thật trong gói nộp.

## Xử lý dữ liệu

Các script nằm trong `data-pipeline/`. Đặt `MONGO_URI` trong `.env` cạnh script cần chạy; riêng `Tiki_analytics.py` dùng biến môi trường `TIKI_MONGO_URI`.

| Nhóm | Script |
|---|---|
| Thu thập | `tikilens_thu_thap_tiki_github.py`, `tikilens_tai_nguon2_truc_tiep.py` |
| Khởi tạo và nhập dữ liệu | `setup_tikilens.py`, `import_tiki*.py`, `tikilens_nhap_nguon2_atlas.py` |
| Kiểm tra | `check_mongodb_connection.py`, `audit_tikilens.py`, `kiem_tra_chat_luong_tikilens.py`, `phan_tich_loi_tikilens.py`, `tikilens_kiem_tra_trung_nguon2.py` |
| Phân tích KPI | `Tiki_analytics.py` |
| Sao lưu/phục hồi thử | `tikilens_backup_atlas.py`, `tikilens_restore_test_atlas.py` |
| Chuẩn hóa trường mảng | Các script trong `part2/` |

Các script `import_tiki*.py` nhận CSV thô `tiki_products_clean_full.csv`, `tiki_reviews.csv`, `tiki_sellers.csv`, `tiki_categories.csv` đặt cạnh script. Script thu thập Tiki tải các tệp này vào `tikilens_acquisition/`; nguồn dữ liệu được liệt kê trong [refs](../refs/README.txt).

Chạy từng script cần thiết. Các script khởi tạo, nhập và phục hồi có ghi MongoDB. `part2/clean_review_arrays.py` mặc định `APPLY_CHANGES = False`; chỉ đặt `True` khi chủ động áp dụng cập nhật. Pipeline chuẩn hóa được trình bày trong [Pipeline_Phan2.docx](../reports/Pipeline_Phan2.docx); thao tác `$out` có thể thay thế collection đích.

## Thí nghiệm và Power BI

- **Isolation Forest Python:** mở `experiments/isolation-forest/sosanhpythonvaorange.ipynb` bằng Jupyter, với thư mục làm việc là thư mục chứa notebook. Đầu vào nằm trong `dataset`; CSV kết quả nằm ở `reports/experiments/isolation-forest`. Cần giữ cấu trúc thư mục này khi chạy trên Colab.
- **Orange:** mở `experiments/isolation-forest/isolation_forest.ows`, chọn lại `dataset/tikilens_vn.clean_products.csv` tại CSV File Import. Dùng năm biến `price`, `discount_rate`, `quantity_sold`, `revenue_estimate`, `review_count`, contamination `0.02`. Đối chiếu tham số và mã sản phẩm khi so sánh kết quả với Python.
- **Phân cụm/dự báo:** chạy `python experiments/seller-clustering-forecast/seller_clustering_forecast.py`. Script tự đọc hai CSV sản phẩm và nhà bán trong `dataset`, in thống kê và mở biểu đồ Matplotlib. Đóng cửa sổ biểu đồ để tiếp tục nếu chương trình đang chờ.
- **Power BI:** mở `powerbi/TIKILENS_VN.pbix` bằng Power BI Desktop; cấu hình lại nguồn khi cần làm mới dữ liệu.

Đặc trưng phân cụm nhà bán được tính từ ảnh chụp sản phẩm, không phải lịch sử giao dịch RFM. Hồi quy ước lượng lượng bán từ thuộc tính sản phẩm, không phải dự báo doanh số theo chuỗi thời gian. Kết quả Isolation Forest cần được kiểm tra thêm trước khi diễn giải nghiệp vụ.

## Kiểm thử

Tại thư mục `source-code`, chạy `python -m unittest discover -s tests`.

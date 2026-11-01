# 📊 BÁO CÁO NHẬN XÉT KINH DOANH & ĐỊNH NGHĨA KPI (TIKILENS VN)

**Dự án:** Phân tích Dữ liệu Thương mại Điện tử Tiki (TikiLens VN)  
**Phạm vi:** Dữ liệu 45,330 bản ghi (5 collections sạch) từ MongoDB Atlas & Dashboard trực quan hóa Power BI  

---

## 📐 PHẦN 1: BỘ KPI CỐT LÕI & CHỈ SỐ ĐO LƯỜNG (KPI DEFINITIONS)

Các chỉ số được tính toán trực tiếp từ dữ liệu hiển thị trên các phân hệ Dashboard Power BI:

| STT | Tên KPI | Công thức DAX / Logic tính toán | Giá trị thực tế trên Dashboard | Ý nghĩa Nghiệp vụ & Mục đích Giám sát |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **Giá trị bán ước tính** *(Estimated Revenue)* | `SUMX('clean_products', 'clean_products'[price] * 'clean_products'[quantity_sold])` | **1T đ** *(~1.228 Trillion VNĐ)* | Quy mô giá trị giao dịch tích lũy ước tính từ toàn bộ sản phẩm thu thập. |
| **2** | **Giá TB hiện tại** *(Average Price)* | `AVERAGE('clean_products'[price])` | **698K đ** | Mức giá bán trung bình niêm yết của các SKU trên sàn. |
| **3** | **Giá trung vị** *(Median Price)* | `MEDIAN('clean_products'[price])` | **185K đ** | Mức giá phân chia tập sản phẩm thành 2 nửa bằng nhau (phản ánh trung thực hơn AOV khi có sản phẩm cực đắt). |
| **4** | **Lượng bán tích lũy** *(Total Quantity Sold)* | `SUM('clean_products'[quantity_sold])` | **7M** *(~7.02 triệu sản phẩm)* | Tổng sản lượng tiêu thụ tích lũy của toàn bộ các sản phẩm. |
| **5** | **Sản phẩm** *(Total Products)* | `COUNTROWS('clean_products')` | **2K** *(2,307 SKU)* | Quy mô danh mục sản phẩm đang niêm yết thu thập được. |
| **6** | **Seller có sản phẩm** *(Total Sellers)* | `DISTINCTCOUNT('clean_products'[seller_id])` | **315 nhà bán** | Số lượng nhà bán hàng hiện tại đang sở hữu sản phẩm kinh doanh. |
| **7** | **Sản phẩm / Seller** *(Avg Products per Seller)* | `DIVIDE([Total Products], [Total Sellers])` | **7.32** | Số lượng sản phẩm trung bình do một nhà bán cung cấp. |
| **8** | **Review thu thập** *(Total Reviews)* | `COUNTROWS('clean_reviews')` | **36K** *(35,632 lượt review)* | Quy mô mẫu dữ liệu đánh giá thu thập dùng cho phân tích. |
| **9** | **Điểm TB review mẫu** *(Avg Review Rating)* | `AVERAGE('clean_reviews'[rating])` | **4.59 / 5.0 sao** | Chỉ số hài lòng tổng quan của người mua hàng (CSAT). |
| **10** | **Tỷ lệ 4–5 sao** *(Positive Review Rate)* | `DIVIDE(CALCULATE(COUNTROWS(), rating >= 4), Total Reviews)` | **90.7%** | Tỷ lệ trải nghiệm tích cực và hài lòng cao từ người mua. |
| **11** | **Tỷ lệ 1–2 sao** *(Negative Review Rate)* | `DIVIDE(CALCULATE(COUNTROWS(), rating <= 2), Total Reviews)` | **6.4%** | Tỷ lệ đánh giá tiêu cực / không hài lòng đối với giao dịch. |
| **12** | **SP có review mẫu** | `CALCULATE(DISTINCTCOUNT(product_id), reviews)` | **2K** | Số sản phẩm phát sinh lượt đánh giá trong tập dữ liệu mẫu. |
| **13** | **Review khớp mã seller** *(Seller Match Rate)* | `DIVIDE(Matched Seller Reviews, Total Reviews)` | **87.6%** | Tỷ lệ đánh giá được định danh chính xác nhà bán hàng tương ứng. |
| **14** | **CausaSent Annotations** | `COUNTROWS('causasent')` | **10K** *(10,000 nhãn)* | Tổng số lượng gán nhãn khía cạnh & cảm xúc từ tập CausaSent. |
| **15** | **Negative trong tập CausaSent**| `DIVIDE(Negative Annotations, Total Annotations)` | **59.3%** | Tỷ lệ nhãn mang cảm xúc tiêu cực trong tập CausaSent. |
| **16** | **Review thiếu nội dung** | `DIVIDE(Missing Content Reviews, Total Reviews)` | **47.1%** | Tỷ lệ lượt đánh giá chỉ chấm sao mà không ghi nhận bình luận. |

---

## 📈 PHẦN 2: BÁO CÁO NHẬN XÉT KINH DOANH CHI TIẾT (BUSINESS INSIGHTS)

### 1. Tổng quan các chỉ số KPI cốt lõi (Core Business Overview)
- **Tổng quy mô giá trị bán ước tính:** Đạt **1T đ** (khoảng 1.228 nghìn tỷ VNĐ) với tổng **Lượng bán tích lũy đạt 7M** (hơn 7 triệu sản phẩm).
- **Phân bố Giá bán:**
  - **Giá trung bình (Mean):** **698K đ**, bị kéo lên bởi nhóm thiết bị công nghệ cao cấp.
  - **Giá trung vị (Median):** **185K đ**, phản ánh phân khúc giá tiêu dùng phổ biến thực tế của khách hàng trên Tiki.
- **Hệ sinh thái Nhà bán & Đa dạng danh mục:**
  - Tổng số **2K sản phẩm** (2,307 SKU) được phân phối bởi **315 nhà bán hiện tại**.
  - Trung bình mỗi nhà bán kinh doanh **7.32 sản phẩm**.
- **Chất lượng đánh giá (Review Benchmark):**
  - Đã thu thập **36K review** mẫu trên tổng số **2K sản phẩm**.
  - Điểm trung bình đánh giá đạt **4.59 / 5.0 sao**.
  - Khách hàng có xu hướng hài lòng rất cao với **90.7% đánh giá đạt 4-5 sao**, trong khi đánh giá tiêu cực (1-2 sao) chỉ chiếm **6.4%**.

---

### 2. Cơ cấu Danh mục Sản phẩm & Phân khúc Giá (Category & Price Segment)

#### a. Cơ cấu Doanh thu & Lượng bán theo Danh mục
- **Nhóm dẫn đầu về Giá trị bán ước tính (Estimated Revenue):**
  1. **Làm Đẹp - Sức Khỏe:** Đứng đầu toàn sàn đạt **422bn đ** (chiếm **34.33%** tổng doanh thu).
  2. **Điện Thoại - Máy Tính Bảng:** Đạt **264bn đ** (chiếm **21.47%** tổng doanh thu).
  3. **Điện Gia Dụng:** Đạt **173bn đ** (chiếm **14.08%** tổng doanh thu).
  4. Các ngành hàng còn lại (Nhà Sách Tiki, Bách Hóa Online...) đóng góp lần lượt **148bn đ (12.01%)**, **77bn đ (6.3%)** và **55bn đ (4.44%)**.
- **Nhóm dẫn đầu về Lượng bán tích lũy (Quantity Sold):**
  - **Làm Đẹp - Sức Khỏe** áp đảo tuyệt đối về sản lượng tiêu thụ (đạt hơn **4 triệu sản phẩm**).
  - Tiếp theo là **Nhà Sách Tiki** (đạt khoảng **1 triệu sản phẩm**) và **Bách Hóa Online**.
- **Top 5 Sản phẩm có lượng bán tích lũy cao nhất:**
  1. *Dầu gội Selsun chống gàu, sạch gàu & hết ngứa da đầu...*: Dẫn đầu toàn sàn với **0.58M (~580,000) sản phẩm**.
  2. *Sửa rửa mặt ngăn ngừa mụn Acnes Creamy Wash 100g*: Đạt **0.35M (~350,000) sản phẩm**.
  3. *Miếng dán mụn giúp giảm mụn sưng viêm Acnes Clear Patch (24 Miếng)*: Đạt **0.20M (~200,000) sản phẩm**.

#### b. Phân tích Phân khúc Giá (Price Segments)
- **Cơ cấu Số lượng Sản phẩm (Total Products by price_segment):**
  - Phân khúc **Phổ thông (100K - 500K)** sở hữu số lượng SKU phong phú nhất (hơn **1,200 sản phẩm**).
  - Phân khúc **Giá rẻ (< 100K)** và **Trung cấp (500K - 2Tr)** lần lượt đứng tiếp theo với khoảng 400 - 500 SKU.
- **Cơ cấu Lượng bán tích lũy (Quantity Sold by price_segment):**
  - **Phân khúc Giá rẻ (< 100K):** Đóng vai trò là "mồi câu phễu" (Traffic Driver) thu hút khách hàng với lượng bán kỷ lục (hơn **4 triệu sản phẩm**).
  - **Phân khúc Phổ thông (100K - 500K):** Đạt sản lượng bán ấn tượng thứ hai (hơn **1.8 triệu sản phẩm**).
  - Phân khúc **Cận cao cấp (2Tr - 10Tr)** và **Cao cấp (>= 10Tr)** có lượng bán thấp nhưng đóng góp giá trị đơn hàng cao.

---

### 3. Phân tích Giá, Khuyến mãi & Điểm Đánh giá (Pricing, Discounts & Ratings)

- **Chiến lược Giảm giá (Discount Band Breakdown):**
  - **Số sản phẩm theo mức giảm:** Nhóm **1. Không giảm** chiếm số lượng SKU đông nhất (hơn 1,100 sản phẩm). Nhóm giảm **3. 11–25%** xếp thứ hai (hơn 500 sản phẩm), tiếp theo là nhóm **2. 1–10%**.
  - **Lượng bán theo mức giảm:** Các sản phẩm nằm trong khung giảm giá **11–25%** đạt sản lượng tiêu thụ vượt trội nhất (gần **5 triệu sản phẩm**), cho thấy đây là khoảng chiết khấu vàng kích thích hành vi mua sắm hiệu quả nhất.
- **Tương quan Giảm giá & Điểm Đánh giá (Scatter Plot):**
  - Phân bố điểm số sản phẩm (*Average Valid Product Rating*) tập trung dày đặc ở dải **4.0 – 5.0 sao** trên hầu hết các mức chiết khấu ($0\% - 80\%$).
  - Các phân khúc giá rẻ (<100K) và phổ thông (100K-500K) trải rộng ở mọi mức giảm giá, trong khi phân khúc Cao cấp (>=10Tr) giữ mức discount thấp hơn và ổn định quanh điểm số 4.5 – 5 sao.

---

### 4. Phân tích Nhà bán & Dịch vụ Nền tảng (Sellers & Platform Features)

- **Mô hình Gian hàng Chính hãng (is_authentic):**
  - Các sản phẩm xác thực **Authentic (True)** mang lại giá trị bán vượt trội (**hơn 1.1T đ**), chiếm gần như trọn vẹn quy mô doanh số toàn sàn so với sản phẩm thường (False).
- **Dịch vụ Giao hàng Nhanh (is_tiki_now):**
  - Gian hàng sử dụng dịch vụ **TikiNOW (True)** đóng góp tới hơn **1T đ** doanh số ước tính. Đây là năng lực cạnh tranh cốt lõi giúp giữ chân khách hàng VIP của Tiki.
- **Ưu đãi Vận chuyển (is_freeship_xtra):**
  - Doanh số ước tính của nhóm sản phẩm **không hỗ trợ Freeship Xtra (False)** đạt hơn **0.6T đ**, nhỉnh hơn nhóm có Freeship Xtra (True - khoảng **0.4T đ**).
- **Phân tích Nhà bán hàng (Seller Analytics):**
  - **Tiki Trading** khẳng định vị thế độc tôn với **934 sản phẩm** niêm yết (áp đảo so với nhà bán thứ hai là *ĐỦ VIỆT Official* với 51 sản phẩm và *Hồng Hạnh Mobile* với 46 sản phẩm).
  - Doanh số của **Tiki Trading** đạt **1.18T đ**, chiếm gần **96%** tổng giá trị giao dịch của top các nhà bán trên sàn.

---

### 5. Phân tích Đánh giá Khách hàng & Cảm xúc (Customer Reviews & Sentiment Audit)

#### a. Xu hướng Đánh giá & Độ đầy đủ Nội dung
- **Xu hướng Đánh giá theo Thời gian (2015 – 2026):**
  - Giai đoạn 2015 – 2019: Lượng review phát sinh thấp.
  - Từ năm 2020 đến 2026: Số lượng review tăng vọt, đạt đỉnh liên tục trong giai đoạn **2022 – 2025** (dao động 5,000 - 6,000 review/năm). Đường biểu diễn **5 sao** (màu hồng) chiếm ưu thế tuyệt đối.
- **Tỷ lệ thiếu nội dung (Missing Content Rate):**
  - Tỷ lệ review thiếu nội dung bình luận trung bình toàn sàn là **47.1%**.
  - Đánh giá **4 sao và 5 sao** có tỷ lệ bỏ trống nội dung bình luận cao nhất (gần **50%**), do khách hàng hài lòng thường chỉ bấm chọn số sao mà không để lại comment.
  - Ngược lại, các đánh giá **1, 2 và 3 sao** có tỷ lệ điền nội dung chữ rất cao (tỷ lệ thiếu nội dung cực thấp dưới 5%), cho thấy khi gặp sự cố, khách hàng luôn chủ động viết chi tiết lý do không hài lòng.

#### b. Phân tích Chuyên sâu Cảm xúc & Khía cạnh (Tập CausaSent Audit - 10K Annotations)
- **Cơ cấu Nhãn & Nguồn dữ liệu:** Tập CausaSent bao gồm **10K nhãn**, trong đó **59.3%** nhãn mang cảm xúc tiêu cực (tập trung khai thác phản hồi xấu để cải thiện vận hành). Nguồn dữ liệu đóng góp chính từ tập `tiki` (~8K nhãn) và `gold` (~2.4K nhãn).
- **Tần suất theo Khía cạnh (Aspect Frequency):**
  1. **Ngoại quan & Bao bì sản phẩm (appearance):** Được đề cập nhiều nhất (hơn 3,400 nhãn).
  2. **Chất lượng sản phẩm (product_quality):** Xếp thứ hai (gần 2,700 nhãn).
  3. **Vận chuyển & Giao hàng (delivery):** Xếp thứ ba (hơn 1,200 nhãn).
  4. Các khía cạnh khác bao gồm: *packaging*, *price*, *customer_service*, *usability*.
- **Tỷ lệ Tiêu cực theo Khía cạnh (Negative Aspect Rate):**
  - **packaging (Đóng gói bao bì):** Đạt tỷ lệ phản hồi tiêu cực cao nhất (**~90%**), phản ánh tình trạng móp méo, hư hỏng hộp trong quá trình vận chuyển.
  - **usability (Khả năng sử dụng/Công năng):** Đạt tỷ lệ tiêu cực xếp thứ hai (**~74%**).
  - **appearance (Độ hoàn thiện/Ngoại quan):** Tỷ lệ tiêu cực khoảng **~72%**.

---

## 💡 PHẦN 3: KHUYẾN NGHỊ CHIẾN LƯỢC KINH DOANH (ACTIONABLE RECOMMENDATIONS)

1. **Củng cố Trụ cột "Authentic + TikiNow" & Hợp tác chiến lược với Tiki Trading:**
   - Tiếp tục đẩy mạnh mô hình hàng chính hãng (tỷ trọng doanh thu >90%). Mở rộng danh mục hàng tiêu dùng nhanh (FMCG) giao nhanh trong 2H để giữ chân tệp khách hàng cao cấp.
2. **Tối ưu hóa Chiến lược Khuyến mãi theo Khung 11–25%:**
   - Tập trung các chương trình Kích cầu/Flash Sale vào dải giảm giá **11–25%**, đây là điểm ngọt (Sweet Spot) mang lại lượng bán tích lũy cao nhất (gần 5M sản phẩm) mà không làm suy giảm biên lợi nhuận của nhà bán.
3. **Cải thiện Chất lượng Đóng gói (Packaging) & Vận chuyển:**
   - Dữ liệu kiểm toán CausaSent chỉ ra **Packaging** có tỷ lệ phàn nàn tiêu cực lên tới **90%**. Cần nâng cấp chuẩn đóng gói chống sốc cho các mặt hàng Chăm sóc cá nhân và Điện máy để giảm thiểu rủi ro đánh giá 1-2 sao.
4. **Xử lý Đánh giá Tiêu cực dựa trên Nội dung Chi tiết:**
   - Vì 95%+ khách hàng đánh giá 1-2 sao đều viết bình luận chi tiết (Missing Content <5%), hệ thống CSKH cần tự động quét từ khóa tiêu cực thuộc nhóm *product_quality* và *usability* để tiến hành đổi trả/bồi hoàn lập tức cho khách hàng.
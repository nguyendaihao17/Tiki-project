import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor

# Cấu hình giao diện đồ thị
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['figure.figsize'] = (10, 6)

# ==============================================================================
# BƯỚC 0: TẢI VÀ TIỀN XỬ LÝ DỮ LIỆU BAN ĐẦU
# ==============================================================================
print("--- DANG TAI DU LIEU ---")
products_df = pd.read_csv('tikilens_vn.clean_products.csv')
sellers_df = pd.read_csv('tikilens_vn.clean_sellers.csv')

# Chuyển đổi định dạng thời gian
products_df['crawled_at'] = pd.to_datetime(products_df['crawled_at'])

# ==============================================================================
# MỤC 1: HỌC KHÔNG GIÁM SÁT (RFM CLUSTERING VỚI K-MEANS)
# ==============================================================================
print("\n" + "="*50)
print("MỤC 1: HỌC KHÔNG GIÁM SÁT - PHÂN CỤM RFM")
print("="*50)

# 1.1 Xây dựng bộ đặc trưng RFM ở mức Seller/Khách hàng
# Ngày mốc tính Recency (Lấy ngày mới nhất trong dữ liệu + 1 ngày)
snapshot_date = products_df['crawled_at'].max() + pd.Timedelta(days=1)

rfm_df = products_df.groupby('seller_id').agg({
    'crawled_at': lambda x: (snapshot_date - x.max()).days,  # Recency (Số ngày từ lần cập nhật gần nhất)
    'product_id': 'count',                                   # Frequency (Số lượng sản phẩm đăng bán)
    'revenue_estimate': 'sum'                                # Monetary (Tổng doanh thu ước tính)
}).reset_index()

rfm_df.rename(columns={
    'crawled_at': 'Recency',
    'product_id': 'Frequency',
    'revenue_estimate': 'Monetary'
}, inplace=True)

# Tránh đưa mã seller_id vào mô hình phân cụm
X_rfm = rfm_df[['Recency', 'Frequency', 'Monetary']].copy()

# 1.2 Chuẩn hóa dữ liệu (StandardScaler)
scaler_rfm = StandardScaler()
X_rfm_scaled = scaler_rfm.fit_transform(X_rfm)

# 1.3 Thử nghiệm K-Means và tìm K tối ưu bằng Elbow & Silhouette Score
inertia = []
silhouette_scores = []
K_range = range(2, 9)

for k in K_range:
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(X_rfm_scaled)
    inertia.append(kmeans.inertia_)
    score = silhouette_score(X_rfm_scaled, kmeans.labels_)
    silhouette_scores.append(score)

# Trực quan hóa Elbow Method & Silhouette Score
fig, ax = plt.subplots(1, 2, figsize=(14, 5))

# Đồ thị Elbow
ax[0].plot(K_range, inertia, 'bo-', markersize=8)
ax[0].set_title('Phương pháp Elbow (Inertia vs K)')
ax[0].set_xlabel('Số lượng cụm (K)')
ax[0].set_ylabel('Inertia')

# Đồ thị Silhouette
ax[1].plot(K_range, silhouette_scores, 'ro-', markersize=8)
ax[1].set_title('Chỉ số Silhouette Score vs K')
ax[1].set_xlabel('Số lượng cụm (K)')
ax[1].set_ylabel('Silhouette Score')

plt.tight_layout()
plt.show()

# 1.4 Chọn K tối ưu (giả định K=3 dựa trên điểm Silhouette cao nhất)
optimal_k = K_range[np.argmax(silhouette_scores)]
print(f">> Số cụm (K) tối ưu được chọn dựa trên Silhouette Score: K = {optimal_k}")

kmeans_final = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
rfm_df['Cluster'] = kmeans_final.fit_predict(X_rfm_scaled)

# 1.5 Mô tả đặc điểm từng cụm
cluster_summary = rfm_df.groupby('Cluster').agg({
    'seller_id': 'count',
    'Recency': 'mean',
    'Frequency': 'mean',
    'Monetary': 'mean'
}).rename(columns={'seller_id': 'So_Luong_Seller'}).reset_index()

print("\n--- BẢNG THỐNG KÊ ĐẶC TRƯNG CÁC CỤM ---")
print(cluster_summary.to_string(index=False))

# Gợi ý chiến lược chăm sóc khách hàng/nhà bán
print("\n--- ĐÁNH GIÁ VÀ GỢI Ý CHIẾN LƯỢC CHĂM SÓC ---")
for cluster_id in range(optimal_k):
    subset = cluster_summary[cluster_summary['Cluster'] == cluster_id].iloc[0]
    print(f"\n* Cụm {cluster_id}:")
    print(f"  - Quy mô: {int(subset['So_Luong_Seller'])} nhà bán")
    print(f"  - TB Recency: {subset['Recency']:.1f} ngày | TB Frequency: {subset['Frequency']:.1f} SP | TB Doanh thu: {subset['Monetary']:,.0f} VNĐ")

    # Đưa ra gợi ý theo đặc điểm
    if subset['Monetary'] == cluster_summary['Monetary'].max():
        print("  - Chiến lược: NÓM VIP / CHỦ LỰC -> Cần ưu tiên chăm sóc 1-1, hỗ trợ gói truyền thông/ADS cao cấp.")
    elif subset['Frequency'] == cluster_summary['Frequency'].max():
        print("  - Chiến lược: NHÀ BÁN TIỀM NĂNG -> Đăng nhiều sản phẩm nhưng doanh thu trung bình, hỗ trợ tối ưu giá và chạy Flash Sale.")
    else:
        print("  - Chiến lược: NHÀ BÁN MỚI / HOẠT ĐỘNG THẤP -> Gửi email nhắc nhở, cung cấp tài liệu hướng dẫn đăng bán hiệu quả.")


# ==============================================================================
# MỤC 2: HỌC CÓ GIÁM SÁT (DỰ BÁO SỐ LƯỢNG BÁN - QUANTITY SOLD)
# ==============================================================================
print("\n" + "="*50)
print("MỤC 2: HỌC CÓ GIÁM SÁT - DỰ BÁO SỐ LƯỢNG BÁN (QUANTITY_SOLD)")
print("="*50)

# 2.1 Lựa chọn biến mục tiêu và đặc trưng đầu vào (Tránh Data Leakage)
# LƯU Ý: Không dùng 'revenue_estimate' làm biến đầu vào vì nó trực tiếp chứa thông tin của 'quantity_sold' (Leakage)
target = 'quantity_sold'

num_features = ['price', 'original_price', 'discount', 'discount_rate', 'rating_average', 'review_count']
cat_features = ['price_segment', 'seller_type', 'is_official_store', 'is_authentic', 'is_freeship_xtra']

# Làm sạch dữ liệu missing cho các đặc trưng chọn lựa
model_df = products_df[[target] + num_features + cat_features].dropna().copy()

X = model_df[num_features + cat_features]
y = model_df[target]

# 2.2 Chia tập Train / Test (80/20)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f">> Kích thước tập Train: {X_train.shape[0]} mẫu | Tập Test: {X_test.shape[0]} mẫu")

# 2.3 Xây dựng Pipeline xử lý tiền xử lý (Scaling cho biến số, One-Hot cho biến phân loại)
numeric_transformer = StandardScaler()
categorical_transformer = OneHotEncoder(handle_unknown='ignore', sparse_output=False)

preprocessor = ColumnTransformer(
    transformers=[
        ('num', numeric_transformer, num_features),
        ('cat', categorical_transformer, cat_features)
    ]
)

# 2.4 Xây dựng và huấn luyện các mô hình
models = {
    "Linear Regression (Baseline)": Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', LinearRegression())
    ]),
    "Random Forest Regressor": Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', RandomForestRegressor(n_estimators=100, random_state=42))
    ])
}

# 2.5 Đánh giá mô hình bằng MAE, RMSE, R2
results = []

for name, model in models.items():
    # Huấn luyện
    model.fit(X_train, y_train)

    # Dự báo
    y_pred = model.predict(X_test)

    # Tính các chỉ số đo lường
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    results.append({
        'Model': name,
        'MAE': mae,
        'RMSE': rmse,
        'R2 Score': r2
    })

# Hiển thị kết quả so sánh
results_df = pd.DataFrame(results)
print("\n--- KẾT QUẢ ĐÁNH GIÁ MÔ HÌNH HỒI QUY ---")
print(results_df.to_string(index=False))

# 2.6 Trực quan hóa so sánh Thực tế vs Dự báo của Random Forest
rf_model = models["Random Forest Regressor"]
y_pred_rf = rf_model.predict(X_test)

plt.figure(figsize=(8, 6))
plt.scatter(y_test, y_pred_rf, alpha=0.5, color='teal')
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
plt.xlabel('Số lượng bán thực tế (Actual)')
plt.ylabel('Số lượng bán dự báo (Predicted)')
plt.title('Random Forest: Thực tế vs Dự báo')
plt.tight_layout()
plt.show()

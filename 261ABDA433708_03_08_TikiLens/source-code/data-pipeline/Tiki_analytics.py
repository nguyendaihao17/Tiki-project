import os
import pandas as pd
import numpy as np
from pymongo import MongoClient

# ==============================================================================
# 1. CẤU HÌNH KẾT NỐI MONGODB ATLAS
# ==============================================================================
# Lấy URI từ biến môi trường để bảo mật thông tin đăng nhập
MONGO_URI = os.getenv("TIKI_MONGO_URI", "").strip()
DB_NAME = "tikilens_vn"

def get_db_connection():
    """Khởi tạo và trả về kết nối CSDL MongoDB Atlas."""
    if not MONGO_URI:
        print("Chua cau hinh TIKI_MONGO_URI.")
        return None
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        return client[DB_NAME]
    except Exception as e:
        print(f"❌ Lỗi kết nối MongoDB Atlas: {type(e).__name__}")
        return None

def load_all_collections():
    """Tải và chuẩn hóa dữ liệu từ 5 collections của CSDL tikilens_vn."""
    db = get_db_connection()
    if db is None:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    col_names = db.list_collection_names()

    # Xác định tên collection sạch (clean_*) hoặc raw_*
    p_col = "clean_products" if "clean_products" in col_names else "raw_products"
    r_col = "clean_reviews" if "clean_reviews" in col_names else "raw_reviews"
    s_col = "clean_sellers" if "clean_sellers" in col_names else "raw_sellers"
    c_col = "clean_categories" if "clean_categories" in col_names else "raw_categories"
    cs_col = "causasent" if "causasent" in col_names else "clean_causasent"

    # Tải dữ liệu vào DataFrames
    df_products = pd.DataFrame(list(db[p_col].find({}, {'_id': 0}))) if p_col in col_names else pd.DataFrame()
    df_reviews = pd.DataFrame(list(db[r_col].find({}, {'_id': 0}))) if r_col in col_names else pd.DataFrame()
    df_sellers = pd.DataFrame(list(db[s_col].find({}, {'_id': 0}))) if s_col in col_names else pd.DataFrame()
    df_categories = pd.DataFrame(list(db[c_col].find({}, {'_id': 0}))) if c_col in col_names else pd.DataFrame()
    df_causasent = pd.DataFrame(list(db[cs_col].find({}, {'_id': 0}))) if cs_col in col_names else pd.DataFrame()

    # Chuẩn hóa dữ liệu Products
    if not df_products.empty:
        df_products['price'] = pd.to_numeric(df_products.get('price', 0), errors='coerce').fillna(0)
        df_products['quantity_sold'] = pd.to_numeric(df_products.get('quantity_sold', df_products.get('historical_sold', 0)), errors='coerce').fillna(0)
        df_products['rating_average'] = pd.to_numeric(df_products.get('rating_average', 0), errors='coerce').fillna(0)
        df_products['discount_rate'] = pd.to_numeric(df_products.get('discount_rate', 0), errors='coerce').fillna(0)
        df_products['estimated_revenue'] = df_products['price'] * df_products['quantity_sold']

        # Phân khúc giá (Price Segments)
        bins = [-np.inf, 100000, 500000, 2000000, 10000000, np.inf]
        labels = ['Giá rẻ (< 100K)', 'Phổ thông (100K - 500K)', 'Trung cấp (500K - 2Tr)', 'Cận cao cấp (2Tr - 10Tr)', 'Cao cấp (>= 10Tr)']
        df_products['price_segment'] = pd.cut(df_products['price'], bins=bins, labels=labels)

        # Khoảng giảm giá (Discount Bands)
        disc_bins = [-np.inf, 0, 10, 25, np.inf]
        disc_labels = ['1. Không giảm', '2. 1-10%', '3. 11-25%', '4. >25%']
        df_products['discount_band'] = pd.cut(df_products['discount_rate'], bins=disc_bins, labels=disc_labels)

    # Chuẩn hóa dữ liệu Reviews
    if not df_reviews.empty:
        df_reviews['rating'] = pd.to_numeric(df_reviews.get('rating', 0), errors='coerce').fillna(0)
        df_reviews['content'] = df_reviews.get('content', '').fillna('').astype(str)
        df_reviews['is_missing_content'] = df_reviews['content'].str.strip() == ''

    return df_products, df_reviews, df_sellers, df_categories, df_causasent

# ==============================================================================
# 2. CHỨC NĂNG TÍNH BỘ KPI CỐT LÕI (CORE KPIS)
# ==============================================================================
def calculate_system_kpis(df_products, df_reviews, df_causasent):
    """Tính toán toàn bộ bộ chỉ số KPI chuẩn xác theo Dashboard Power BI."""
    if df_products.empty:
        return {}

    total_revenue = df_products['estimated_revenue'].sum()
    total_quantity_sold = df_products['quantity_sold'].sum()
    total_products = len(df_products)

    # Sellers
    seller_col = 'seller_id' if 'seller_id' in df_products.columns else 'seller_name'
    total_sellers = df_products[seller_col].nunique() if seller_col in df_products.columns else 0
    prods_per_seller = total_products / total_sellers if total_sellers > 0 else 0

    # Giá
    mean_price = df_products['price'].mean()
    median_price = df_products['price'].median()
    min_price = df_products['price'].min()
    max_price = df_products['price'].max()

    # Reviews & CSAT
    total_reviews = len(df_reviews) if not df_reviews.empty else 0
    avg_rating = df_reviews['rating'].mean() if total_reviews > 0 else 0

    pos_reviews = len(df_reviews[df_reviews['rating'] >= 4]) if total_reviews > 0 else 0
    neg_reviews = len(df_reviews[df_reviews['rating'] <= 2]) if total_reviews > 0 else 0
    pos_rate = (pos_reviews / total_reviews * 100) if total_reviews > 0 else 0
    neg_rate = (neg_reviews / total_reviews * 100) if total_reviews > 0 else 0

    missing_content_rate = (df_reviews['is_missing_content'].sum() / total_reviews * 100) if total_reviews > 0 else 0

    # Review Match Seller
    matched_seller_reviews = df_reviews['seller_id'].notna().sum() if 'seller_id' in df_reviews.columns else 0
    seller_match_rate = (matched_seller_reviews / total_reviews * 100) if total_reviews > 0 else 0

    # Risk Products (Rating <= 3.0 & Sold > 0)
    risky_prods = df_products[(df_products['quantity_sold'] > 0) & (df_products['rating_average'] > 0) & (df_products['rating_average'] <= 3.0)]
    risk_rate = (len(risky_prods) / total_products * 100) if total_products > 0 else 0

    # CausaSent
    causasent_total = len(df_causasent) if not df_causasent.empty else 0
    if causasent_total > 0 and 'sentiment' in df_causasent.columns:
        causasent_neg_count = (df_causasent['sentiment'] == 'negative').sum()
        causasent_neg_rate = (causasent_neg_count / causasent_total) * 100
    else:
        causasent_neg_rate = 0

    return {
        "Giá trị bán ước tính (VNĐ)": total_revenue,
        "Lượng bán tích lũy": total_quantity_sold,
        "Tổng sản phẩm (SKU)": total_products,
        "Tổng nhà bán (Sellers)": total_sellers,
        "Sản phẩm / Seller": round(prods_per_seller, 2),
        "Giá TB hiện tại (VNĐ)": mean_price,
        "Giá trung vị (VNĐ)": median_price,
        "Khoảng giá (Min - Max VNĐ)": f"{min_price:,.0f} - {max_price:,.0f}",
        "Review thu thập": total_reviews,
        "Điểm TB review mẫu": round(avg_rating, 2),
        "Tỷ lệ 4-5 sao (%)": round(pos_rate, 2),
        "Tỷ lệ 1-2 sao (%)": round(neg_rate, 2),
        "Review thiếu nội dung (%)": round(missing_content_rate, 2),
        "Review khớp mã seller (%)": round(seller_match_rate, 2),
        "Tỷ lệ sản phẩm rủi ro (%)": round(risk_rate, 2),
        "CausaSent Annotations": causasent_total,
        "CausaSent Negative Rate (%)": round(causasent_neg_rate, 2)
    }

# ==============================================================================
# 3. PHÂN TÍCH CHUYÊN SÂU THEO DANH MỤC, NHÀ BÁN & CẢM XÚC
# ==============================================================================
def analyze_category_breakdown(df_products):
    """Phân tích cơ cấu giá trị bán và sản lượng theo Danh mục chính."""
    if df_products.empty or 'category_name' not in df_products.columns:
        return pd.DataFrame()

    df_cat = df_products.groupby('category_name').agg(
        Total_Products=('name', 'count'),
        Quantity_Sold=('quantity_sold', 'sum'),
        Estimated_Revenue=('estimated_revenue', 'sum'),
        Avg_Rating=('rating_average', 'mean')
    ).reset_index()

    total_rev = df_cat['Estimated_Revenue'].sum()
    df_cat['Revenue_Share_%'] = (df_cat['Estimated_Revenue'] / total_rev * 100).round(2)
    return df_cat.sort_values(by='Estimated_Revenue', ascending=False)

def analyze_platform_services(df_products):
    """Phân tích hiệu quả kinh doanh theo dịch vụ TikiNOW, Freeship Xtra, Authentic."""
    if df_products.empty:
        return {}

    def to_bool(val):
        return str(val).strip().lower() in ['true', '1', 'yes']

    df_products['is_tiki_now_b'] = df_products.get('is_tiki_now', False).apply(to_bool)
    df_products['is_freeship_b'] = df_products.get('is_freeship_xtra', False).apply(to_bool)
    df_products['is_authentic_b'] = df_products.get('is_authentic', False).apply(to_bool)

    return {
        "Authentic Revenue (VNĐ)": df_products[df_products['is_authentic_b']]['estimated_revenue'].sum(),
        "Non-Authentic Revenue (VNĐ)": df_products[~df_products['is_authentic_b']]['estimated_revenue'].sum(),
        "TikiNOW Revenue (VNĐ)": df_products[df_products['is_tiki_now_b']]['estimated_revenue'].sum(),
        "Non-TikiNOW Revenue (VNĐ)": df_products[~df_products['is_tiki_now_b']]['estimated_revenue'].sum(),
        "Freeship Xtra Revenue (VNĐ)": df_products[df_products['is_freeship_b']]['estimated_revenue'].sum(),
        "Non-Freeship Xtra Revenue (VNĐ)": df_products[~df_products['is_freeship_b']]['estimated_revenue'].sum()
    }

def analyze_top_sellers(df_products, top_n=5):
    """Phân tích Top nhà bán có nhiều sản phẩm và doanh thu cao nhất (Tiki Trading)."""
    if df_products.empty or 'seller_name' not in df_products.columns:
        return pd.DataFrame()

    df_sellers = df_products.groupby('seller_name').agg(
        Total_Products=('name', 'count'),
        Quantity_Sold=('quantity_sold', 'sum'),
        Estimated_Revenue=('estimated_revenue', 'sum')
    ).reset_index()

    return df_sellers.sort_values(by='Estimated_Revenue', ascending=False).head(top_n)

def analyze_causasent_aspects(df_causasent):
    """Phân tích khía cạnh và tỷ lệ negative từ tập CausaSent."""
    if df_causasent.empty or 'aspect_category' not in df_causasent.columns or 'sentiment' not in df_causasent.columns:
        return pd.DataFrame()

    df_aspect = df_causasent.groupby('aspect_category').agg(
        Total_Annotations=('sentiment', 'count'),
        Negative_Count=('sentiment', lambda x: (x == 'negative').sum())
    ).reset_index()

    df_aspect['Negative_Rate_%'] = (df_aspect['Negative_Count'] / df_aspect['Total_Annotations'] * 100).round(2)
    return df_aspect.sort_values(by='Total_Annotations', ascending=False)

# ==============================================================================
# 4. CHƯƠNG TRÌNH CHÍNH & IN BÁO CÁO KẾT QUẢ
# ==============================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("🚀 BÁO CÁO PHÂN TÍCH KINH DOANH & KIỂM TOÁN DỮ LIỆU TIKILENS VN")
    print("=" * 80)

    # 1. Tải dữ liệu
    df_p, df_r, df_s, df_c, df_cs = load_all_collections()

    if not df_p.empty:
        # 2. In bộ KPI cốt lõi
        kpis = calculate_system_kpis(df_p, df_r, df_cs)
        print("\n📊 --- 1. BỘ CHỈ SỐ KPI CỐT LÕI (CORE KPIS OVERVIEW) ---")
        for k, v in kpis.items():
            if isinstance(v, (int, float)) and "VNĐ" in k:
                print(f"  • {k:<32}: {v:>18,.0f} VNĐ")
            elif isinstance(v, (int, float)) and "%" in k:
                print(f"  • {k:<32}: {v:>18.2f} %")
            elif isinstance(v, (int, float)):
                print(f"  • {k:<32}: {v:>18,}")
            else:
                print(f"  • {k:<32}: {str(v):>18}")

        # 3. Cơ cấu Danh mục
        print("\n📦 --- 2. CƠ CẤU PHÂN BỐ DOANH THU THEO DANH MỤC CHÍNH ---")
        df_cat_summary = analyze_category_breakdown(df_p)
        if not df_cat_summary.empty:
            print(df_cat_summary.to_string(index=False))

        # 4. Phân tích Dịch vụ Nền tảng
        print("\n💎 --- 3. ĐÁNH GIÁ HIỆU QUẢ DỊCH VỤ NỀN TẢNG (TIKINOW / AUTHENTIC) ---")
        services = analyze_platform_services(df_p)
        for sk, sv in services.items():
            print(f"  • {sk:<32}: {sv:>18,.0f} VNĐ")

        # 5. Top Nhà Bán hàng
        print("\n🏪 --- 4. TOP 5 NHÀ BÁN HÀNG DẪN ĐẦU DOANH THU (TOP SELLERS) ---")
        top_sellers = analyze_top_sellers(df_p, 5)
        if not top_sellers.empty:
            print(top_sellers.to_string(index=False))

        # 6. Khía cạnh CausaSent
        print("\n💬 --- 5. PHÂN TÍCH KHÍA CẠNH & CẢM XÚC CAUSASENT (10K ANNOTATIONS) ---")
        df_aspects = analyze_causasent_aspects(df_cs)
        if not df_aspects.empty:
            print(df_aspects.to_string(index=False))

        print("\n" + "=" * 80)
        print("✅ THỰC THI THÀNH CÔNG VÀ ĐÃ TRÍCH XUẤT TOÀN BỘ INSIGHTS TỪ MONGODB ATLAS!")
        print("=" * 80)
    else:
        print("❌ Không thể nạp dữ liệu từ MongoDB Atlas. Vui lòng kiểm tra lại kết nối mạng!")

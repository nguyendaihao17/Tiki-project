import streamlit as st
import pandas as pd
from src.auth import check_permission, login_sidebar
from src.analytics import (
    calculate_core_kpis,
    load_dashboard_reviews_data,
    load_products_data,
    load_reviews_data,
)
from webapp import (
    admin_page,
    anomaly_page,
    customer_clustering_page,
    dashboard_page,
    explore_page,
    forecast_page,
    overview_page,
)

# Cấu hình giao diện Streamlit toàn cục
st.set_page_config(
    page_title="TikiLens | Phân tích thương mại điện tử",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  :root { color-scheme: light; }
  .stApp { background: #f6f8fb; color: #172b4d; }
  [data-testid="stSidebar"] { background: #eaf0f7; border-right: 1px solid #d9e2ed; }
  [data-testid="stSidebar"] [role="radiogroup"] label { padding: .35rem .5rem; border-radius: 6px; }
  [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background: #d9eaf0; color: #0b5871; font-weight: 650; }
  [data-testid="stMetric"] { background: #fff; border: 1px solid #dfe7ef; border-radius: 10px; padding: 16px; min-height: 112px; }
  [data-testid="stMetricLabel"] { color: #52657b; }
  [data-testid="stMetricValue"] { color: #113c63; }
  [data-testid="stVerticalBlockBorderWrapper"] { border-color: #dfe7ef; }
  h1, h2, h3 { color: #123858; letter-spacing: -.025em; }
  .user-name { color: #123858; font-size: 1rem; font-weight: 650; margin: .25rem 0 .1rem; }
  .login-eyebrow { margin-top: 3vh; color: #0c6282; font-size: .78rem; font-weight: 750; letter-spacing: .16em; }
  @media (max-width: 768px) { [data-testid="stMetric"] { min-height: 96px; } }
</style>
""", unsafe_allow_html=True)

def main():
    # Đăng nhập trước khi tải dữ liệu và dựng điều hướng.
    is_logged_in = login_sidebar()
    if not is_logged_in:
        return
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### Khám phá")
    
    # 2. Điều hướng theo từng chức năng
    pages = [
        "Phân tích & Dashboard",
        "Khám phá & Lọc dữ liệu",
        "Chất lượng dữ liệu",
        "Phân cụm khách hàng",
        "Dự báo",
        "Phát hiện bất thường",
    ]
    if check_permission("admin"):
        pages.append("Quản trị dữ liệu & Báo cáo")
    page = st.sidebar.radio("Chọn chức năng", pages)

    if st.sidebar.button(
        "Làm mới dữ liệu",
        help="Xóa cache dữ liệu và tải lại từ MongoDB.",
    ):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()

    needs_reviews = page in {
        "Chất lượng dữ liệu",
        "Khám phá & Lọc dữ liệu",
        "Phân tích & Dashboard",
        "Phân cụm khách hàng",
    }
    needs_products = page != "Phân cụm khách hàng"

    # Collection data is cached independently for five minutes; each page only
    # loads the collections it uses. Model fitting happens within page content.
    with st.spinner("Đang tải dữ liệu cần cho trang này..."):
        df_products = load_products_data() if needs_products else None
        df_reviews = (
            load_dashboard_reviews_data()
            if page in {"Chất lượng dữ liệu", "Phân tích & Dashboard"}
            else load_reviews_data()
        ) if needs_reviews else None
        if df_products is None:
            df_products = pd.DataFrame()
        if df_reviews is None:
            df_reviews = pd.DataFrame()
        kpis = calculate_core_kpis(df_products, df_reviews)
        
    # 4. Điều phối các trang giao diện
    if page == "Chất lượng dữ liệu":
        overview_page.show(df_products, df_reviews, kpis)
    elif page == "Khám phá & Lọc dữ liệu":
        explore_page.show(df_products, df_reviews)
    elif page == "Phân tích & Dashboard":
        dashboard_page.show(df_products, df_reviews, kpis)
    elif page == "Phân cụm khách hàng":
        customer_clustering_page.show(df_reviews)
    elif page == "Dự báo":
        forecast_page.show(df_products)
    elif page == "Phát hiện bất thường":
        anomaly_page.show(df_products)
    elif page == "Quản trị dữ liệu & Báo cáo":
        admin_page.show(df_products)

if __name__ == "__main__":
    main()

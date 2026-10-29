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
    clustering_page,
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
  .stApp { background: #f5f7fb; color: #12243b; }
  [data-testid="stAppViewBlockContainer"] { max-width: 1540px; padding: 1.8rem 2.75rem 3rem; }
  [data-testid="stHeader"] { background: rgba(245, 247, 251, .88); }
  [data-testid="stSidebar"] { background: #0b2038; border-right: 1px solid #153a5d; }
  [data-testid="stSidebar"] * { color: #e8f0f8; }
  [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { color: #aabfd4; }
  [data-testid="stSidebar"] hr { border-color: rgba(183, 209, 234, .2); }
  [data-testid="stSidebar"] [role="radiogroup"] label {
    border: 1px solid transparent;
    border-radius: 7px;
    margin: .16rem 0;
    padding: .48rem .58rem;
    transition: background .15s ease, border-color .15s ease;
  }
  [data-testid="stSidebar"] [role="radiogroup"] label:hover { background: rgba(255, 255, 255, .07); }
  [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background: rgba(33, 168, 177, .2);
    border-color: rgba(95, 218, 223, .28);
    color: #ffffff;
    font-weight: 650;
  }
  [data-testid="stSidebar"] [data-baseweb="radio"] > div:first-child { background: transparent; border-color: #7190ad; }
  [data-testid="stSidebar"] button {
    background: transparent;
    border-color: #496987;
    color: #edf6fb;
  }
  [data-testid="stSidebar"] button:hover { border-color: #65ccd1; color: #ffffff; }
  .brand-lockup { display: flex; align-items: center; gap: .72rem; padding: .55rem 0 1.15rem; }
  .brand-mark {
    align-items: center; background: #16a3ad; border-radius: 7px; color: #ffffff !important;
    display: inline-flex; font-size: .78rem; font-weight: 800; height: 2.2rem; justify-content: center;
    letter-spacing: .04em; width: 2.2rem;
  }
  .brand-name { color: #ffffff !important; font-size: 1.18rem; font-weight: 760; letter-spacing: -.025em; line-height: 1.1; }
  .brand-subtitle { color: #aabfd4 !important; font-size: .73rem; letter-spacing: .04em; margin-top: .14rem; text-transform: uppercase; }
  .sidebar-user { border: 1px solid rgba(183, 209, 234, .18); border-radius: 7px; margin: .65rem 0 .9rem; padding: .72rem .78rem; }
  .sidebar-user-name { color: #ffffff !important; font-size: .93rem; font-weight: 700; }
  .sidebar-user-role { color: #9ec3d4 !important; font-size: .78rem; margin-top: .18rem; }
  .app-header { align-items: center; border-bottom: 1px solid #dbe4ee; display: flex; justify-content: space-between; margin: -.2rem 0 1.75rem; padding-bottom: .9rem; }
  .app-header-brand { color: #103858; font-size: .92rem; font-weight: 760; letter-spacing: .01em; }
  .app-header-context { color: #728399; font-size: .79rem; }
  [data-testid="stMetric"] {
    background: #ffffff; border: 1px solid #dce6ef; border-radius: 8px; box-shadow: 0 2px 8px rgba(25, 54, 84, .04);
    min-height: 106px; padding: 1rem 1.05rem;
  }
  [data-testid="stMetricLabel"] { color: #60738a; font-size: .8rem; font-weight: 650; }
  [data-testid="stMetricValue"] { color: #103858; font-size: 1.72rem; font-weight: 740; }
  [data-testid="stVerticalBlockBorderWrapper"] { background: #ffffff; border-color: #dce6ef; border-radius: 8px; }
  [data-testid="stTabs"] [data-baseweb="tab-list"] { border-bottom-color: #dbe4ee; gap: 1.35rem; }
  [data-testid="stTabs"] button { color: #61748a; font-weight: 620; padding: .55rem .1rem; }
  [data-testid="stTabs"] button[aria-selected="true"] { color: #087f89; }
  [data-testid="stTabs"] [data-baseweb="tab-highlight"] { background-color: #0d9ba5; height: 2px; }
  [data-testid="stDataFrame"] { border: 1px solid #dce6ef; border-radius: 8px; overflow: hidden; }
  [data-baseweb="select"] > div, [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input {
    border-color: #cbd9e5; border-radius: 6px;
  }
  [data-testid="stButton"] button, [data-testid="stFormSubmitButton"] button {
    border-radius: 6px; font-weight: 670; min-height: 2.45rem;
  }
  [data-testid="stButton"] button[kind="primary"], [data-testid="stFormSubmitButton"] button[kind="primary"] {
    background: #0a8792; border-color: #0a8792;
  }
  [data-testid="stButton"] button[kind="primary"]:hover, [data-testid="stFormSubmitButton"] button[kind="primary"]:hover { background: #08727b; border-color: #08727b; }
  h1, h2, h3 { color: #102f4b; letter-spacing: -.028em; }
  h1 { font-weight: 760; }
  h2, h3 { font-weight: 700; }
  [data-testid="stCaptionContainer"] p { color: #708198; }
  .login-hero { margin: 8vh 0 1.15rem; }
  .login-eyebrow { color: #087f89; font-size: .72rem; font-weight: 780; letter-spacing: .14em; text-transform: uppercase; }
  .login-title { color: #102f4b; font-size: clamp(2rem, 4vw, 2.9rem); font-weight: 780; letter-spacing: -.045em; line-height: 1.06; margin: .65rem 0; }
  .login-description { color: #60738a; font-size: 1rem; line-height: 1.65; margin: 0; max-width: 36rem; }
  .login-card-label { color: #102f4b; font-size: .9rem; font-weight: 700; margin-bottom: .6rem; }
  [data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stTabs"]) { box-shadow: 0 10px 30px rgba(20, 49, 79, .07); }
  @media (max-width: 768px) {
    [data-testid="stAppViewBlockContainer"] { padding: 1.25rem 1rem 2rem; }
    [data-testid="stMetric"] { min-height: 92px; padding: .8rem; }
    .app-header-context { display: none; }
    .login-hero { margin-top: 3vh; }
  }
</style>
""", unsafe_allow_html=True)

def main():
    # Đăng nhập trước khi tải dữ liệu và dựng điều hướng.
    is_logged_in = login_sidebar()
    if not is_logged_in:
        return

    st.markdown(
        """<div class="app-header">
          <div class="app-header-brand">TikiLens <span style="color:#8aa0b6;font-weight:500">/ Analytics Workspace</span></div>
          <div class="app-header-context">Phân tích thương mại điện tử · Dữ liệu sản phẩm và đánh giá</div>
        </div>""",
        unsafe_allow_html=True,
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### Khám phá")
    
    # 2. Điều hướng theo từng chức năng
    pages = [
        "Phân tích & Dashboard",
        "Khám phá & Lọc dữ liệu",
        "Chất lượng dữ liệu",
        "Phân cụm khách hàng & nhà bán",
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
        "Phân cụm khách hàng & nhà bán",
    }
    needs_products = True

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
    elif page == "Phân cụm khách hàng & nhà bán":
        clustering_page.show(df_products, df_reviews)
    elif page == "Dự báo":
        forecast_page.show(df_products)
    elif page == "Phát hiện bất thường":
        anomaly_page.show(df_products)
    elif page == "Quản trị dữ liệu & Báo cáo":
        admin_page.show(df_products)

if __name__ == "__main__":
    main()

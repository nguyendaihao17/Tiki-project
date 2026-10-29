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
    page_icon="🔵",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  :root { color-scheme: light; }
  .stApp { background: #f5f8ff; color: #183153; }
  [data-testid="stAppViewBlockContainer"] { max-width: 1540px; padding: 1.8rem 2.75rem 3rem; }
  [data-testid="stAppViewBlockContainer"]:has(.login-hero) { max-width: 1120px; padding-top: 4vh; }
  [data-testid="stHeader"] { background: rgba(245, 248, 255, .92); }
  [data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #dce8f7; }
  [data-testid="stSidebar"] * { color: #183153; }
  [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p { color: #607b9d; }
  [data-testid="stSidebar"] hr { border-color: #e3ecf8; }
  [data-testid="stSidebar"] [role="radiogroup"] label {
    border: 1px solid transparent;
    border-radius: 7px;
    margin: .16rem 0;
    padding: .48rem .58rem;
    transition: background .15s ease, border-color .15s ease;
  }
  [data-testid="stSidebar"] [role="radiogroup"] label:hover { background: #f1f7ff; }
  [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
    background: #e8f3ff;
    border-color: #c7e1ff;
    color: #0758b4;
    font-weight: 650;
  }
  [data-testid="stSidebar"] [data-baseweb="radio"] > div:first-child { background: transparent; border-color: #8aa9ce; }
  [data-testid="stSidebar"] button {
    background: #ffffff;
    border-color: #c9dcf2;
    color: #164c87;
  }
  [data-testid="stSidebar"] button:hover { border-color: #0b74e5; color: #0758b4; }
  .brand-lockup { display: flex; align-items: center; gap: .72rem; padding: .55rem 0 1.15rem; }
  .brand-mark {
    align-items: center; background: #0b74e5; border-radius: 9px; color: #ffffff !important;
    display: inline-flex; font-size: .78rem; font-weight: 800; height: 2.2rem; justify-content: center;
    letter-spacing: .04em; width: 2.2rem;
  }
  .brand-name { color: #123e73 !important; font-size: 1.18rem; font-weight: 760; letter-spacing: -.025em; line-height: 1.1; }
  .brand-subtitle { color: #6b85a4 !important; font-size: .73rem; letter-spacing: .04em; margin-top: .14rem; text-transform: uppercase; }
  .sidebar-user { background: #f1f7ff; border: 1px solid #dbe9fb; border-radius: 8px; margin: .65rem 0 .9rem; padding: .72rem .78rem; }
  .sidebar-user-name { color: #14395e !important; font-size: .93rem; font-weight: 700; }
  .sidebar-user-role { color: #47729f !important; font-size: .78rem; margin-top: .18rem; }
  .app-header { align-items: center; border-bottom: 1px solid #dbe4ee; display: flex; justify-content: space-between; margin: -.2rem 0 1.75rem; padding-bottom: .9rem; }
  .app-header-brand { color: #0b65c7; font-size: .92rem; font-weight: 760; letter-spacing: .01em; }
  .app-header-context { color: #728399; font-size: .79rem; }
  [data-testid="stMetric"] {
    background: #ffffff; border: 1px solid #dce6ef; border-radius: 8px; box-shadow: 0 2px 8px rgba(25, 54, 84, .04);
    min-height: 106px; padding: 1rem 1.05rem;
  }
  [data-testid="stMetricLabel"] { color: #60738a; font-size: .8rem; font-weight: 650; }
  [data-testid="stMetricValue"] { color: #115eac; font-size: 1.72rem; font-weight: 740; }
  [data-testid="stVerticalBlockBorderWrapper"] { background: #ffffff; border-color: #dce6ef; border-radius: 8px; }
  [data-testid="stTabs"] [role="tablist"] {
    background: #edf5ff; border: 1px solid #d6e7fb; border-radius: 10px;
    gap: .4rem; overflow-x: auto; padding: .35rem; scrollbar-width: thin;
  }
  [data-testid="stTabs"] [role="tab"] {
    background: #ffffff; border: 1px solid #d6e7fb; border-radius: 7px;
    color: #174b80; flex: 0 0 auto; font-weight: 650; min-height: 2.35rem;
    padding: .58rem .8rem; white-space: nowrap;
  }
  [data-testid="stTabs"] [role="tab"] p { color: inherit; }
  [data-testid="stTabs"] [role="tab"]:hover { background: #f2f8ff; color: #0758b4; }
  [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    background: #e4f1ff; border-color: #8fc3ff; color: #0758b4;
    box-shadow: 0 1px 5px rgba(11, 116, 229, .14);
  }
  [data-testid="stTabs"] [role="tab"][aria-selected="true"] p { color: #0758b4; }
  [data-testid="stTabs"] [role="tab"]:focus-visible { outline: 2px solid #0b74e5; outline-offset: 2px; }
  [data-testid="stTabs"] [data-baseweb="tab-highlight"],
  [data-testid="stTabs"] [data-baseweb="tab-border"] { display: none; }
  [data-testid="stDataFrame"] { border: 1px solid #dce6ef; border-radius: 8px; overflow: hidden; }
  [data-baseweb="select"] > div, [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input {
    border-color: #cbd9e5; border-radius: 6px;
  }
  [data-testid="stButton"] button, [data-testid="stFormSubmitButton"] button {
    border-radius: 6px; font-weight: 670; min-height: 2.45rem;
  }
  [data-testid="stButton"] button[kind="primary"], [data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"] {
    background: #0b74e5; border-color: #0b74e5; color: #ffffff;
  }
  [data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"] p,
  [data-testid="stButton"] button[kind="primary"] p { color: #ffffff; }
  [data-testid="stButton"] button[kind="primary"]:hover, [data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"]:hover { background: #0758b4; border-color: #0758b4; }
  h1, h2, h3 { color: #102f4b; letter-spacing: -.028em; }
  h1 { font-weight: 760; }
  h2, h3 { font-weight: 700; }
  [data-testid="stCaptionContainer"] p { color: #708198; }
  .login-hero { background: linear-gradient(145deg, #0b74e5, #0758b4); border-radius: 16px; color: #ffffff; margin: 3vh 0 1rem; min-height: 26rem; padding: 3rem 2.5rem; }
  .login-eyebrow { color: #cbe5ff; font-size: .74rem; font-weight: 780; letter-spacing: .13em; text-transform: uppercase; }
  .login-title { color: #ffffff; font-size: clamp(2rem, 3.5vw, 3.3rem); font-weight: 780; letter-spacing: -.045em; line-height: 1.1; margin: 1.7rem 0 1rem; }
  .login-description { color: #e2f0ff; font-size: 1rem; line-height: 1.65; margin: 0; max-width: 26rem; }
  .login-features { border-top: 1px solid rgba(255,255,255,.3); color: #e2f0ff; font-size: .88rem; line-height: 1.9; margin-top: 3.4rem; padding-top: 1.2rem; }
  .login-form-intro { color: #14395e; font-size: 1.45rem; font-weight: 750; letter-spacing: -.03em; margin: 3vh 0 1rem; }
  .login-card-label { color: #102f4b; font-size: .9rem; font-weight: 700; margin-bottom: .6rem; }
  [data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stTabs"]) { box-shadow: 0 10px 30px rgba(20, 49, 79, .07); }
  [data-testid="stVerticalBlockBorderWrapper"]:has(.login-card-label) { border-color: #d8e7fa; padding: .55rem; }
  @media (max-width: 768px) {
    [data-testid="stAppViewBlockContainer"] { padding: 1.25rem 1rem 2rem; }
    [data-testid="stAppViewBlockContainer"]:has(.login-hero) { padding-top: 0; }
    [data-testid="stHorizontalBlock"]:has(.login-hero) { flex-direction: column; gap: .25rem; }
    [data-testid="stHorizontalBlock"]:has(.login-hero) > [data-testid="stColumn"] { min-width: 100%; width: 100%; }
    [data-testid="stMetric"] { min-height: 92px; padding: .8rem; }
    .app-header-context { display: none; }
    .login-hero { margin-top: 1vh; min-height: auto; padding: 1.25rem 1.5rem; }
    .login-title { margin: .9rem 0; }
    .login-features { display: none; }
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

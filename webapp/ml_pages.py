import streamlit as st
from src.analytics import run_kmeans_rfm, run_random_forest_regression, run_isolation_forest

def show(df_products):
    st.subheader("Phân tích nâng cao bằng Machine Learning")
    
    tab1, tab2, tab3 = st.tabs(["1. Phân cụm Nhà bán (K-Means RFM)", "2. Dự báo số lượng bán (Random Forest)", "3. Phát hiện bất thường (Isolation Forest)"])
    
    with tab1:
        st.markdown("### Phân cụm Nhà bán hàng theo mô hình RFM")
        if st.button("Chạy thuật toán K-Means"):
            rfm_df, kmeans = run_kmeans_rfm(df_products)
            if rfm_df is not None:
                st.success("Phân cụm hoàn tất! Thành công chia nhà bán thành các nhóm chiến lược.")
                st.dataframe(rfm_df.groupby('Cluster').agg({'seller_id': 'count', 'Frequency': 'mean', 'Monetary': 'mean'}), use_container_width=True)
            else:
                st.error("Không đủ dữ liệu để phân cụm.")
                
    with tab2:
        st.markdown("### Mô hình Hồi quy dự báo số lượng bán sản phẩm")
        if st.button("Huấn luyện mô hình Random Forest"):
            pipeline, metrics, (y_test, y_pred) = run_random_forest_regression(df_products)
            if metrics:
                st.success("Huấn luyện thành công mô hình Random Forest Regressor!")
                c1, c2, c3 = st.columns(3)
                c1.metric("MAE (Sai số tuyệt đối)", f"{metrics['MAE']:,.2f}")
                c2.metric("RMSE", f"{metrics['RMSE']:,.2f}")
                c3.metric("R2 Score", f"{metrics['R2 Score']:.4f}")
                
    with tab3:
        st.markdown("### Phát hiện Sản phẩm Bất thường (Top 2% Outliers)")
        if st.button("Chạy Isolation Forest"):
            res_df = run_isolation_forest(df_products)
            outliers = res_df[res_df['Outlier'] == 'Yes']
            st.warning(f"Phát hiện tổng cộng **{len(outliers)}** sản phẩm dị biệt (Hero Products / Best-sellers).")
            st.dataframe(outliers[['product_id', 'name', 'price', 'quantity_sold', 'estimated_revenue']], use_container_width=True)

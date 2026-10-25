import pandas as pd
import streamlit as st
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


FEATURE_CANDIDATES = [
    "price",
    "discount_rate",
    "quantity_sold",
    "revenue_estimate",
    "estimated_revenue",
    "review_count",
    "rating_average",
]


def show(df_products):
    st.title("Phát hiện sản phẩm bất thường")
    st.caption("Isolation Forest tìm sản phẩm có tổ hợp chỉ số khác biệt so với phần còn lại.")
    if df_products.empty:
        st.warning("Không có dữ liệu sản phẩm.")
        return

    feature_columns = [column for column in FEATURE_CANDIDATES if column in df_products.columns]
    if len(feature_columns) < 2:
        st.info("Cần ít nhất hai trường số (giá, lượng bán, doanh thu, đánh giá...) để phát hiện bất thường.")
        return

    anomaly_percent = st.slider("Tỷ lệ bất thường giả định (%)", 1, 10, 2)
    data = df_products.copy()
    features = data[feature_columns].apply(pd.to_numeric, errors="coerce")
    usable = features.notna().any(axis=1)
    features = features.loc[usable]
    data = data.loc[usable].copy()
    if len(features) < 10:
        st.info("Cần ít nhất 10 sản phẩm có dữ liệu số để chạy Isolation Forest.")
        return

    model = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        IsolationForest(contamination=anomaly_percent / 100, random_state=42),
    )
    labels = model.fit_predict(features)
    scores = model[-1].decision_function(
        model[1].transform(model[0].transform(features))
    )
    data["Kết quả"] = ["Bất thường" if label == -1 else "Bình thường" for label in labels]
    data["Điểm bất thường"] = scores
    anomalies = data[data["Kết quả"] == "Bất thường"].sort_values("Điểm bất thường")

    metrics = st.columns(3)
    metrics[0].metric("Sản phẩm được phân tích", f"{len(data):,}")
    metrics[1].metric("Bất thường phát hiện", f"{len(anomalies):,}")
    metrics[2].metric("Tỷ lệ giả định", f"{anomaly_percent}%")
    st.info(
        "Bất thường chỉ có nghĩa là khác biệt về thống kê; không tự động đồng nghĩa với sản phẩm lỗi, "
        "gian lận hoặc bán chạy."
    )

    display_columns = [
        column
        for column in [
            "product_id",
            "name",
            "category_name",
            "price",
            "quantity_sold",
            "revenue_estimate",
            "estimated_revenue",
            "rating_average",
            "Điểm bất thường",
        ]
        if column in anomalies.columns
    ]
    if anomalies.empty:
        st.success("Không phát hiện sản phẩm bất thường theo tỷ lệ đã chọn.")
    else:
        st.dataframe(anomalies[display_columns], use_container_width=True, hide_index=True)
        st.download_button(
            "Tải danh sách bất thường (CSV)",
            anomalies[display_columns].to_csv(index=False).encode("utf-8-sig"),
            "tiki_product_anomalies.csv",
            "text/csv",
        )

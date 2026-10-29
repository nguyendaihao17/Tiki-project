import altair as alt
import numpy as np
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


def _score_distribution(data: pd.DataFrame) -> pd.DataFrame:
    """Aggregate model scores before sending them to the browser."""
    scores = pd.to_numeric(data["Điểm bất thường"], errors="coerce")
    lower, upper = scores.min(), scores.max()
    if lower == upper:
        lower, upper = lower - 0.5, upper + 0.5
    edges = np.linspace(lower, upper, 25)
    rows = []
    for label in ("Bình thường", "Bất thường"):
        counts, _ = np.histogram(scores[data["Kết quả"].eq(label)], bins=edges)
        rows.extend(
            {"Điểm": (left + right) / 2, "Sản phẩm": int(count), "Kết quả": label}
            for left, right, count in zip(edges[:-1], edges[1:], counts)
        )
    return pd.DataFrame(rows)


def _category_anomaly_rates(data: pd.DataFrame, minimum: int = 10) -> pd.DataFrame:
    """Rank sufficiently populated categories by observed anomaly rate."""
    category_column = "root_category_name" if "root_category_name" in data else "category_name"
    if category_column not in data:
        return pd.DataFrame(columns=["Danh mục", "Sản phẩm", "Bất thường", "Tỷ lệ (%)"])
    categories = data[category_column]
    if category_column == "root_category_name" and "category_name" in data:
        categories = categories.fillna(data["category_name"])
    categories = categories.fillna("Chưa phân loại").astype(str).str.strip()
    categories = categories.mask(categories.eq(""), "Chưa phân loại")
    grouped = (
        pd.DataFrame({"Danh mục": categories, "Bất thường": data["Kết quả"].eq("Bất thường")})
        .groupby("Danh mục", as_index=False)
        .agg(**{"Sản phẩm": ("Bất thường", "size"), "Bất thường": ("Bất thường", "sum")})
    )
    grouped = grouped[grouped["Sản phẩm"].ge(minimum)].copy()
    grouped["Tỷ lệ (%)"] = grouped["Bất thường"] / grouped["Sản phẩm"] * 100
    return grouped.sort_values(["Tỷ lệ (%)", "Bất thường"], ascending=False).head(10)


def show(df_products):
    st.title("Phát hiện sản phẩm bất thường")
    st.caption("TikiLens / Phát hiện bất thường · So sánh các chỉ số sản phẩm trong ảnh chụp dữ liệu")
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

    observed_rate = len(anomalies) / len(data) * 100
    revenue_column = "estimated_revenue" if "estimated_revenue" in data else "revenue_estimate"
    revenue = pd.to_numeric(data[revenue_column], errors="coerce").clip(lower=0) if revenue_column in data else pd.Series(dtype=float)
    revenue_share = revenue.loc[anomalies.index].sum() / revenue.sum() * 100 if revenue.sum() > 0 else None

    st.header("Tổng quan bất thường")
    metrics = st.columns(4)
    metrics[0].metric("Sản phẩm được phân tích", f"{len(data):,}")
    metrics[1].metric("Bất thường phát hiện", f"{len(anomalies):,}")
    metrics[2].metric("Tỷ lệ thực tế", f"{observed_rate:.1f}%")
    metrics[3].metric("Tỷ trọng doanh thu ước tính", f"{revenue_share:.1f}%" if revenue_share is not None else "—",
                      help="Phần doanh thu ước tính thuộc nhóm sản phẩm bất thường; không phải doanh thu thất thoát.")
    st.caption(f"Mô hình Isolation Forest dùng tỷ lệ giả định {anomaly_percent}%. Điểm âm thể hiện sản phẩm khác biệt hơn; kết quả không tự xác nhận sản phẩm lỗi hay gian lận.")

    st.header("Bản đồ bất thường")
    score_column, category_column = st.columns((3, 2))
    with score_column, st.container(border=True):
        st.subheader("Phân bố điểm bất thường")
        distribution = _score_distribution(data)
        chart = alt.Chart(distribution).mark_area(opacity=0.55).encode(
            x=alt.X("Điểm:Q", title="Điểm mô hình · thấp hơn là khác biệt hơn"),
            y=alt.Y("Sản phẩm:Q", title="Số sản phẩm", stack=None),
            color=alt.Color("Kết quả:N", scale=alt.Scale(
                domain=["Bình thường", "Bất thường"], range=["#0b74e5", "#d94a4a"])),
            tooltip=[alt.Tooltip("Điểm:Q", format=".3f"), "Kết quả:N", "Sản phẩm:Q"],
        ).properties(height=320)
        st.altair_chart(chart, use_container_width=True)
    with category_column, st.container(border=True):
        st.subheader("Danh mục có tỷ lệ cao")
        rates = _category_anomaly_rates(data)
        if rates.empty:
            st.info("Cần danh mục có ít nhất 10 sản phẩm để so sánh tỷ lệ.")
        else:
            chart = alt.Chart(rates).mark_bar(color="#d94a4a", cornerRadiusEnd=3).encode(
                x=alt.X("Tỷ lệ (%):Q", title="Sản phẩm bất thường (%)"),
                y=alt.Y("Danh mục:N", sort="-x", title=None, axis=alt.Axis(labelLimit=170)),
                tooltip=["Danh mục:N", "Sản phẩm:Q", "Bất thường:Q",
                         alt.Tooltip("Tỷ lệ (%):Q", format=".1f")],
            ).properties(height=320)
            st.altair_chart(chart, use_container_width=True)
        st.caption("Chỉ so sánh danh mục có từ 10 sản phẩm; tối đa 10 danh mục.")

    if {"price", "quantity_sold"}.issubset(data.columns):
        chart_columns = [column for column in (
            "product_id", "price", "quantity_sold", "Kết quả", "Điểm bất thường"
        ) if column in data]
        points = data[chart_columns].copy()
        points["price"] = pd.to_numeric(points["price"], errors="coerce")
        points["quantity_sold"] = pd.to_numeric(points["quantity_sold"], errors="coerce")
        points = points[
            np.isfinite(points["price"]) & np.isfinite(points["quantity_sold"])
            & points["price"].ge(0) & points["quantity_sold"].ge(0)
        ]
        normal = points[points["Kết quả"].eq("Bình thường")]
        unusual = points[points["Kết quả"].eq("Bất thường")]
        if len(normal) > 2500:
            normal = normal.sample(2500, random_state=42)
        if len(unusual) > 1000:
            unusual = unusual.nsmallest(1000, "Điểm bất thường")
        points = pd.concat([normal, unusual])
        if not points.empty:
            with st.container(border=True):
                st.subheader("Giá và lượng bán của các sản phẩm")
                chart = alt.Chart(points).mark_circle(opacity=0.6, size=55).encode(
                    x=alt.X("price:Q", title="Giá (VNĐ)", scale=alt.Scale(type="symlog"), axis=alt.Axis(format="~s")),
                    y=alt.Y("quantity_sold:Q", title="Số lượng đã bán", scale=alt.Scale(type="symlog"), axis=alt.Axis(format="~s")),
                    color=alt.Color("Kết quả:N", scale=alt.Scale(
                        domain=["Bình thường", "Bất thường"], range=["#0b74e5", "#d94a4a"])),
                    tooltip=[alt.Tooltip("product_id:N", title="Mã sản phẩm") if "product_id" in points else
                             alt.Tooltip("Kết quả:N"), alt.Tooltip("price:Q", title="Giá", format=",.0f"),
                             alt.Tooltip("quantity_sold:Q", title="Đã bán", format=",.0f"),
                             alt.Tooltip("Điểm bất thường:Q", format=".3f")],
                ).properties(height=350).interactive()
                st.altair_chart(chart, use_container_width=True)
                st.caption("Biểu đồ hiển thị tối đa 2.500 sản phẩm bình thường được lấy mẫu và 1.000 sản phẩm có điểm bất thường thấp nhất. Các chỉ số tổng quan vẫn tính trên toàn bộ dữ liệu.")

    st.header("Sản phẩm cần xem xét")
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

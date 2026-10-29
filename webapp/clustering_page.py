import pandas as pd
import streamlit as st
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


FEATURE_COLUMNS = [
    "product_count",
    "quantity_sold",
    "estimated_revenue",
    "review_count",
    "average_rating",
]


def _seller_features(df_products: pd.DataFrame) -> pd.DataFrame:
    """Create one portfolio-and-performance record for each seller."""
    if df_products.empty or "seller_id" not in df_products.columns:
        return pd.DataFrame()

    products = df_products.dropna(subset=["seller_id"]).copy()
    if products.empty:
        return pd.DataFrame()

    products["seller_id"] = products["seller_id"].astype(str).str.strip()
    products = products[products["seller_id"].ne("")]
    if products.empty:
        return pd.DataFrame()

    for column in ("quantity_sold", "estimated_revenue", "review_count", "rating_average"):
        products[column] = pd.to_numeric(products.get(column, 0), errors="coerce").fillna(0)

    product_key = "product_id" if "product_id" in products.columns else "seller_id"
    features = (
        products.groupby("seller_id", as_index=False)
        .agg(
            product_count=(product_key, "nunique"),
            quantity_sold=("quantity_sold", "sum"),
            estimated_revenue=("estimated_revenue", "sum"),
            review_count=("review_count", "sum"),
            average_rating=("rating_average", "mean"),
        )
    )
    return features.replace([float("inf"), float("-inf")], pd.NA).fillna(0)


def _customer_features(df_reviews: pd.DataFrame) -> pd.DataFrame:
    """Create one review-behavior record for each customer."""
    required = {"customer_id", "rating"}
    if df_reviews.empty or not required.issubset(df_reviews.columns):
        return pd.DataFrame()

    reviews = df_reviews.dropna(subset=["customer_id"]).copy()
    reviews["customer_id"] = reviews["customer_id"].astype(str).str.strip()
    reviews = reviews[reviews["customer_id"].ne("")]
    reviews["rating"] = pd.to_numeric(reviews["rating"], errors="coerce")
    reviews = reviews.dropna(subset=["rating"])
    if reviews.empty:
        return pd.DataFrame()

    product_key = "product_id" if "product_id" in reviews.columns else "rating"
    features = (
        reviews.groupby("customer_id", as_index=False)
        .agg(
            review_count=("rating", "size"),
            average_rating=("rating", "mean"),
            rating_std=("rating", "std"),
            unique_products=(product_key, "nunique"),
        )
    )
    if "sentiment" in reviews.columns:
        negative = reviews["sentiment"].astype(str).str.upper().eq("NEGATIVE")
    else:
        negative = reviews["rating"].le(2)
    negative_rates = negative.groupby(reviews["customer_id"]).mean()
    features["negative_review_rate"] = features["customer_id"].map(negative_rates)
    return features.replace([float("inf"), float("-inf")], pd.NA).fillna(0)


def _show_seller_clustering(df_products: pd.DataFrame) -> None:
    st.caption("Nhóm nhà bán theo quy mô danh mục và hiệu quả của sản phẩm đang có trong dữ liệu.")
    st.info(
        "Phân cụm sử dụng số sản phẩm, số lượng đã bán, doanh thu ước tính, lượt đánh giá "
        "và điểm đánh giá trung bình. Đây là phân tích danh mục sản phẩm tại thời điểm chụp, "
        "không phải RFM giao dịch theo thời gian."
    )

    features = _seller_features(df_products)
    if features.empty:
        st.warning("Cần dữ liệu seller_id để phân cụm nhà bán hàng.")
        return

    minimum_products = st.slider("Số sản phẩm tối thiểu của mỗi nhà bán", 1, 10, 1)
    eligible = features[features["product_count"] >= minimum_products].copy()
    if len(eligible) < 2:
        st.warning("Không đủ nhà bán thỏa điều kiện để phân cụm.")
        return

    max_clusters = min(8, len(eligible))
    default_clusters = min(4, len(eligible))
    cluster_count = st.slider("Số nhóm nhà bán", 2, max_clusters, default_clusters)
    scaled = StandardScaler().fit_transform(eligible[FEATURE_COLUMNS].astype(float))
    model = KMeans(n_clusters=cluster_count, random_state=42, n_init=10)
    eligible["cluster"] = model.fit_predict(scaled)

    clusters = (
        eligible.groupby("cluster", as_index=False)
        .agg(
            sellers=("seller_id", "size"),
            average_products=("product_count", "mean"),
            average_quantity_sold=("quantity_sold", "mean"),
            average_revenue=("estimated_revenue", "mean"),
            average_reviews=("review_count", "mean"),
            average_rating=("average_rating", "mean"),
        )
    )

    metrics = st.columns(3)
    metrics[0].metric("Nhà bán được phân cụm", f"{len(eligible):,}")
    metrics[1].metric("Số nhóm", f"{cluster_count}")
    metrics[2].metric("Đặc trưng", f"{len(FEATURE_COLUMNS)}")

    st.subheader("Hồ sơ các nhóm nhà bán")
    st.dataframe(
        clusters.style.format(
            {
                "average_products": "{:.1f}",
                "average_quantity_sold": "{:.0f}",
                "average_revenue": "{:,.0f}",
                "average_reviews": "{:.1f}",
                "average_rating": "{:.2f}",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Nhà bán theo nhóm")
    st.dataframe(eligible, use_container_width=True, hide_index=True)
    st.download_button(
        "Tải kết quả phân cụm (CSV)",
        eligible.to_csv(index=False).encode("utf-8-sig"),
        "tiki_seller_clusters.csv",
        "text/csv",
    )


def _show_customer_clustering(df_reviews: pd.DataFrame) -> None:
    st.caption("Nhóm khách hàng theo hành vi đánh giá trong dữ liệu hiện có.")
    st.info(
        "Phân cụm sử dụng tần suất đánh giá, điểm đánh giá, độ biến động điểm, tỷ lệ đánh giá "
        "tiêu cực và số sản phẩm đã đánh giá. Dữ liệu không có lịch sử đơn hàng hoặc chi tiêu, "
        "do đó đây không phải phân cụm RFM mua hàng."
    )

    features = _customer_features(df_reviews)
    if features.empty:
        st.warning("Cần dữ liệu customer_id và rating để phân cụm khách hàng.")
        return

    minimum_reviews = st.slider("Số lượt đánh giá tối thiểu của mỗi khách hàng", 1, 10, 2)
    eligible = features[features["review_count"] >= minimum_reviews].copy()
    if len(eligible) < 2:
        st.warning("Không đủ khách hàng thỏa điều kiện để phân cụm.")
        return

    feature_columns = [
        "review_count",
        "average_rating",
        "rating_std",
        "unique_products",
        "negative_review_rate",
    ]
    max_clusters = min(8, len(eligible))
    default_clusters = min(4, len(eligible))
    cluster_count = st.slider("Số nhóm khách hàng", 2, max_clusters, default_clusters)
    scaled = StandardScaler().fit_transform(eligible[feature_columns].astype(float))
    model = KMeans(n_clusters=cluster_count, random_state=42, n_init=10)
    eligible["cluster"] = model.fit_predict(scaled)

    clusters = (
        eligible.groupby("cluster", as_index=False)
        .agg(
            customers=("customer_id", "size"),
            average_reviews=("review_count", "mean"),
            average_rating=("average_rating", "mean"),
            negative_review_rate=("negative_review_rate", "mean"),
            average_products_reviewed=("unique_products", "mean"),
        )
    )

    metrics = st.columns(3)
    metrics[0].metric("Khách hàng được phân cụm", f"{len(eligible):,}")
    metrics[1].metric("Số nhóm", f"{cluster_count}")
    metrics[2].metric("Đặc trưng", f"{len(feature_columns)}")

    st.subheader("Hồ sơ các nhóm khách hàng")
    st.dataframe(
        clusters.style.format(
            {
                "average_reviews": "{:.1f}",
                "average_rating": "{:.2f}",
                "negative_review_rate": "{:.1%}",
                "average_products_reviewed": "{:.1f}",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.subheader("Khách hàng theo nhóm")
    st.dataframe(eligible, use_container_width=True, hide_index=True)
    st.download_button(
        "Tải kết quả phân cụm (CSV)",
        eligible.to_csv(index=False).encode("utf-8-sig"),
        "tiki_customer_clusters.csv",
        "text/csv",
    )


def show(df_products: pd.DataFrame, df_reviews: pd.DataFrame) -> None:
    st.title("Phân cụm khách hàng và nhà bán hàng")
    customer_tab, seller_tab = st.tabs(["Khách hàng", "Nhà bán hàng"])
    with customer_tab:
        _show_customer_clustering(df_reviews)
    with seller_tab:
        _show_seller_clustering(df_products)

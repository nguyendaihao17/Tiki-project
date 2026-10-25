import pandas as pd
import streamlit as st
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


def _customer_features(df_reviews):
    required = {"customer_id", "rating"}
    if df_reviews.empty or not required.issubset(df_reviews.columns):
        return pd.DataFrame()

    reviews = df_reviews.dropna(subset=["customer_id"]).copy()
    reviews["rating"] = pd.to_numeric(reviews["rating"], errors="coerce")
    reviews = reviews.dropna(subset=["rating"])
    if reviews.empty:
        return pd.DataFrame()

    features = reviews.groupby("customer_id").agg(
        review_count=("rating", "size"),
        average_rating=("rating", "mean"),
        rating_std=("rating", "std"),
        unique_products=("product_id", "nunique") if "product_id" in reviews else ("rating", "size"),
    )
    features["rating_std"] = features["rating_std"].fillna(0)

    if "sentiment" in reviews.columns:
        negative = reviews["sentiment"].astype(str).str.upper().eq("NEGATIVE")
        features["negative_review_rate"] = negative.groupby(reviews["customer_id"]).mean()
    else:
        features["negative_review_rate"] = (
            reviews["rating"].le(2).groupby(reviews["customer_id"]).mean()
        )

    if "created_at" in reviews.columns:
        reviews["review_date"] = pd.to_datetime(reviews["created_at"], errors="coerce", utc=True)
        last_review = reviews.groupby("customer_id")["review_date"].max()
        snapshot = reviews["review_date"].max()
        if pd.notna(snapshot):
            features["days_since_last_review"] = (snapshot - last_review).dt.days
    return features.replace([float("inf"), float("-inf")], pd.NA).fillna(0)


def show(df_reviews):
    st.title("Phân cụm khách hàng")
    st.caption("Nhóm khách hàng dựa trên hành vi đánh giá trong dữ liệu hiện có.")
    st.info(
        "Nguồn dữ liệu hiện không có lịch sử đơn hàng hoặc chi tiêu theo khách hàng. "
        "Vì vậy, các nhóm được tạo từ tần suất đánh giá, điểm đánh giá, tỷ lệ đánh giá tiêu cực "
        "và số sản phẩm đã đánh giá; đây không phải phân cụm RFM mua hàng."
    )

    features = _customer_features(df_reviews)
    if features.empty:
        st.warning("Cần dữ liệu customer_id và rating để phân cụm khách hàng.")
        return

    minimum_reviews = st.slider("Số lượt đánh giá tối thiểu", 1, 10, 2)
    eligible = features[features["review_count"] >= minimum_reviews].copy()
    if len(eligible) < 2:
        st.warning("Không đủ khách hàng thỏa điều kiện để phân cụm.")
        return

    cluster_count = st.slider("Số nhóm khách hàng", 2, min(8, len(eligible)), min(4, len(eligible)))
    values = eligible.astype(float)
    scaled = StandardScaler().fit_transform(values)
    model = KMeans(n_clusters=cluster_count, random_state=42, n_init=10)
    eligible["cluster"] = model.fit_predict(scaled)
    eligible.index.name = "customer_id"

    clusters = eligible.groupby("cluster").agg(
        customers=("review_count", "size"),
        average_reviews=("review_count", "mean"),
        average_rating=("average_rating", "mean"),
        negative_review_rate=("negative_review_rate", "mean"),
        average_products_reviewed=("unique_products", "mean"),
    )
    metrics = st.columns(3)
    metrics[0].metric("Khách hàng được phân cụm", f"{len(eligible):,}")
    metrics[1].metric("Số nhóm", f"{cluster_count}")
    metrics[2].metric("Đặc trưng", f"{len(values.columns)}")

    st.subheader("Hồ sơ các nhóm")
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
    )
    st.subheader("Khách hàng theo nhóm")
    st.dataframe(eligible.reset_index(), use_container_width=True, hide_index=True)
    st.download_button(
        "Tải kết quả phân cụm (CSV)",
        eligible.reset_index().to_csv(index=False).encode("utf-8-sig"),
        "tiki_customer_clusters.csv",
        "text/csv",
    )

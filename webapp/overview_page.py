"""Visibility into dataset coverage, separate from the business dashboard."""

import pandas as pd
import streamlit as st


def show(df_products, df_reviews, _kpis=None):
    st.title("Chất lượng dữ liệu")
    st.caption("Kiểm tra độ đầy đủ của các trường quan trọng trước khi diễn giải kết quả phân tích.")

    if df_products.empty:
        st.warning("Chưa có dữ liệu sản phẩm. Kiểm tra kết nối dữ liệu hoặc làm mới ở thanh bên.")
        return

    metrics = st.columns(4)
    metrics[0].metric("Sản phẩm", f"{len(df_products):,}")
    metrics[1].metric("Đánh giá", f"{len(df_reviews):,}")
    metrics[2].metric("Nhà bán", f"{df_products['seller_id'].nunique():,}" if "seller_id" in df_products else "—")
    metrics[3].metric("Danh mục chính", f"{df_products['root_category_name'].nunique():,}" if "root_category_name" in df_products else "—")

    st.header("Độ đầy đủ theo trường")
    coverage = []
    for label, frame, columns in (
        ("Sản phẩm", df_products, ["product_id", "name", "price", "category_name", "seller_id"]),
        ("Đánh giá", df_reviews, ["review_id", "customer_id", "product_id", "rating", "created_at"]),
    ):
        for column in columns:
            if column in frame:
                missing = int(frame[column].isna().sum())
                coverage.append({"Tập dữ liệu": label, "Trường": column, "Bản ghi thiếu": missing,
                                 "Độ đầy đủ (%)": round((1 - missing / len(frame)) * 100, 2) if len(frame) else 0})
            else:
                coverage.append({"Tập dữ liệu": label, "Trường": column, "Bản ghi thiếu": "Không có trường",
                                 "Độ đầy đủ (%)": 0})
    st.dataframe(pd.DataFrame(coverage), hide_index=True, width="stretch")
    st.caption("Trường vắng mặt được đánh dấu 0%; các phép phân tích liên quan cần được diễn giải thận trọng.")

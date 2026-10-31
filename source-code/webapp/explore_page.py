import pandas as pd
import streamlit as st
from src.reporting import dataframe_to_csv, excel_workbook_bytes


def _numeric_range(frame, column, label, key):
    if column not in frame.columns:
        st.caption(f"Không có trường {label} trong dữ liệu.")
        return None

    values = pd.to_numeric(frame[column], errors="coerce").dropna()
    if values.empty:
        st.caption(f"Không có giá trị {label} hợp lệ để lọc.")
        return None

    minimum = int(values.min())
    maximum = int(values.max())
    if minimum == maximum:
        st.caption(f"{label}: {minimum:,.0f}")
        return minimum, maximum
    lower, upper = st.columns(2)
    start = lower.number_input(f"{label} từ", min_value=0, max_value=maximum,
                               value=minimum, step=1000 if column == "price" else 1, key=f"{key}_min")
    end = upper.number_input(f"{label} đến", min_value=0, max_value=maximum,
                             value=maximum, step=1000 if column == "price" else 1, key=f"{key}_max")
    if start > end:
        st.warning(f"{label}: giá trị từ phải nhỏ hơn hoặc bằng giá trị đến.")
    return start, end


def _filter_reviews(df_reviews, customer_query, date_range):
    if df_reviews.empty:
        return df_reviews.copy()

    reviews = df_reviews.copy()
    if customer_query:
        customer_matches = pd.Series(False, index=reviews.index)
        for column in ("customer_id", "customer_name"):
            if column in reviews.columns:
                customer_matches |= reviews[column].astype(str).str.contains(
                    customer_query,
                    case=False,
                    regex=False,
                    na=False,
                )
        reviews = reviews[customer_matches]

    if date_range and "created_at" in reviews.columns:
        review_dates = pd.to_datetime(reviews["created_at"], errors="coerce", utc=True).dt.date
        reviews = reviews[review_dates.between(date_range[0], date_range[1])]
    return reviews


def _filter_products(df_products, product_query, categories, origins, price_range, quantity_range, customer_reviews):
    products = df_products.copy()
    if product_query:
        product_matches = pd.Series(False, index=products.index)
        for column in ("product_id", "name"):
            if column in products.columns:
                product_matches |= products[column].astype(str).str.contains(
                    product_query,
                    case=False,
                    regex=False,
                    na=False,
                )
        products = products[product_matches]

    category_column = "root_category_name" if "root_category_name" in products else "category_name"
    if categories and category_column in products.columns:
        products = products[products[category_column].astype(str).isin(categories)]
    if origins and "origin" in products.columns:
        products = products[products["origin"].astype(str).isin(origins)]
    if price_range and "price" in products.columns:
        prices = pd.to_numeric(products["price"], errors="coerce")
        products = products[prices.between(price_range[0], price_range[1])]
    if quantity_range and "quantity_sold" in products.columns:
        quantities = pd.to_numeric(products["quantity_sold"], errors="coerce")
        products = products[quantities.between(quantity_range[0], quantity_range[1])]

    if customer_reviews is not None:
        if "product_id" not in products.columns or "product_id" not in customer_reviews.columns:
            return products.iloc[0:0]
        matching_ids = customer_reviews["product_id"].dropna().astype(str).unique()
        products = products[products["product_id"].astype(str).isin(matching_ids)]
    return products


def show(df_products, df_reviews=None):
    st.title("Khám phá dữ liệu")
    st.caption("Tìm sản phẩm, tra cứu đánh giá theo khách hàng và xuất dữ liệu sau lọc.")

    if df_products.empty:
        st.warning("Không có dữ liệu sản phẩm.")
        return
    if df_reviews is None:
        df_reviews = pd.DataFrame()

    if "review_id" in df_reviews.columns:
        st.caption(
            "Nguồn dữ liệu hiện không có mã hóa đơn/order ID hoặc quốc gia khách hàng. "
            "Có thể tìm theo mã/tên sản phẩm hoặc mã/tên khách hàng; ngày lọc là ngày đánh giá "
            "(không phải ngày giao dịch). Bộ lọc xuất xứ bên dưới là xuất xứ sản phẩm."
        )
    else:
        st.caption(
            "Nguồn dữ liệu hiện không có mã hóa đơn/order ID, quốc gia khách hàng hoặc dữ liệu đơn hàng. "
            "Có thể tìm sản phẩm và lọc theo xuất xứ sản phẩm; ngày lọc là ngày thu thập/đánh giá "
            "nếu có trường tương ứng."
        )

    st.header("Điều kiện tìm kiếm")
    search_columns = st.columns(2)
    with search_columns[0]:
        product_query = st.text_input("Mã hoặc tên sản phẩm", key="explore_product_query", placeholder="Nhập mã hoặc tên sản phẩm")
    with search_columns[1]:
        customer_query = st.text_input("Mã hoặc tên khách hàng", key="explore_customer_query", placeholder="Nhập mã hoặc tên khách hàng")

    date_range = None
    date_filter_active = False
    if not df_reviews.empty and "created_at" in df_reviews.columns:
        dates = pd.to_datetime(df_reviews["created_at"], errors="coerce", utc=True).dropna()
        if not dates.empty:
            first_date, last_date = dates.min().date(), dates.max().date()
            date_value = st.date_input(
                "Khoảng ngày đánh giá",
                value=(first_date, last_date),
                min_value=first_date,
                max_value=last_date,
                key="explore_review_dates",
            )
            if isinstance(date_value, (tuple, list)) and len(date_value) == 2:
                date_range = date_value
                date_filter_active = date_range != (first_date, last_date)
    else:
        st.caption("Không có trường ngày đánh giá để lọc.")

    filters = st.columns(2)
    with filters[0]:
        category_column = "root_category_name" if "root_category_name" in df_products else "category_name"
        categories = (
            sorted(df_products[category_column].dropna().astype(str).unique())
            if category_column in df_products.columns
            else []
        )
        selected_categories = st.multiselect(
            "Danh mục chính",
            categories,
            placeholder="Tất cả danh mục",
        )
    with filters[1]:
        origins = sorted(df_products["origin"].dropna().astype(str).unique()) if "origin" in df_products else []
        selected_origins = st.multiselect(
            "Xuất xứ sản phẩm",
            origins,
            placeholder="Tất cả xuất xứ",
            disabled=not origins,
        )
        if not origins:
            st.caption("Không có trường xuất xứ.")
    numeric_filters = st.columns(2)
    with numeric_filters[0]:
        price_range = _numeric_range(df_products, "price", "Khoảng đơn giá (VNĐ)", "explore_price_range")
    with numeric_filters[1]:
        quantity_range = _numeric_range(
            df_products,
            "quantity_sold",
            "Khoảng số lượng đã bán",
            "explore_quantity_range",
        )

    filtered_reviews = _filter_reviews(
        df_reviews,
        customer_query,
        date_range if date_filter_active else None,
    )
    reviews_applied = bool(customer_query or date_filter_active)
    if not reviews_applied:
        filtered_reviews = df_reviews.iloc[0:0].copy()
    filtered_products = _filter_products(
        df_products,
        product_query,
        selected_categories,
        selected_origins,
        price_range,
        quantity_range,
        filtered_reviews if reviews_applied else None,
    )

    st.success(f"Tìm thấy **{len(filtered_products):,}** sản phẩm"
               + (f" và **{len(filtered_reviews):,}** đánh giá phù hợp." if reviews_applied else ". Chưa áp dụng điều kiện tìm đánh giá."))
    if filtered_products.empty and filtered_reviews.empty:
        st.warning("Không tìm thấy kết quả phù hợp với điều kiện tìm kiếm và bộ lọc.")
        return

    if not filtered_products.empty:
        st.header("Sản phẩm")
        product_columns = [
            column
            for column in [
                "product_id",
                "name",
                "category_name",
                "origin",
                "price",
                "quantity_sold",
                "estimated_revenue",
                "revenue_estimate",
                "rating_average",
                "review_count",
            ]
            if column in filtered_products.columns
        ]
        st.dataframe(filtered_products[product_columns], width="stretch", hide_index=True)
        export_columns = st.columns(2)
        with export_columns[0]:
            st.download_button(
                "Tải sản phẩm đã lọc (CSV)",
                dataframe_to_csv(filtered_products),
                "filtered_tiki_products.csv",
                "text/csv",
            )
        with export_columns[1]:
            st.download_button(
                "Tải sản phẩm đã lọc (Excel)",
                excel_workbook_bytes({"San pham": filtered_products}),
                "filtered_tiki_products.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    if not filtered_reviews.empty:
        st.header("Đánh giá khớp với khách hàng và khoảng ngày")
        review_columns = [
            column
            for column in [
                "review_id",
                "customer_id",
                "customer_name",
                "product_id",
                "rating",
                "sentiment",
                "created_at",
                "title",
            ]
            if column in filtered_reviews.columns
        ]
        st.dataframe(filtered_reviews[review_columns], width="stretch", hide_index=True)
        export_columns = st.columns(2)
        with export_columns[0]:
            st.download_button(
                "Tải đánh giá đã lọc (CSV)",
                dataframe_to_csv(filtered_reviews),
                "filtered_tiki_reviews.csv",
                "text/csv",
            )
        with export_columns[1]:
            st.download_button(
                "Tải đánh giá đã lọc (Excel)",
                excel_workbook_bytes({"Danh gia": filtered_reviews}),
                "filtered_tiki_reviews.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

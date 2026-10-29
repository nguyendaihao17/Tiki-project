"""Dashboard for the product snapshot and its linked reviews."""

from math import ceil

import altair as alt
import pandas as pd
import streamlit as st

from src.reporting import dataframe_to_csv, excel_workbook_bytes

TIKI_BLUE = "#0b74e5"
GOLD = "#f5a623"


def _number(frame, column):
    return pd.to_numeric(frame.get(column, pd.Series(index=frame.index, dtype=float)), errors="coerce")


def _revenue(frame):
    if "estimated_revenue" in frame:
        return _number(frame, "estimated_revenue").fillna(0)
    if "revenue_estimate" in frame:
        return _number(frame, "revenue_estimate").fillna(0)
    return (_number(frame, "price") * _number(frame, "quantity_sold")).fillna(0)


def _boolean(value):
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return None
    value = str(value).strip().lower()
    if value in {"true", "1", "yes", "có"}:
        return True
    if value in {"false", "0", "no", "không"}:
        return False
    return None


def filter_dashboard_data(products, reviews, categories=(), price_range=None,
                          tiki_now="Tất cả", freeship="Tất cả", review_dates=None):
    """Product filters affect all panels; review dates affect reviews only."""
    products, reviews = products.copy(), reviews.copy()
    category_column = "root_category_name" if "root_category_name" in products else "category_name"
    if categories and category_column in products:
        products = products[products[category_column].astype(str).isin(categories)]
    if price_range is not None and "price" in products:
        products = products[_number(products, "price").between(*price_range)]
    for column, choice in (("is_tiki_now", tiki_now), ("is_freeship_xtra", freeship)):
        if choice != "Tất cả" and column in products:
            products = products[products[column].map(_boolean).eq(choice == "Có")]
    if "product_id" in products and "product_id" in reviews:
        ids = products["product_id"].dropna().astype(str)
        reviews = reviews[reviews["product_id"].astype(str).isin(ids)]
    if review_dates is not None and "created_at" in reviews:
        dates = pd.to_datetime(reviews["created_at"], errors="coerce", utc=True).dt.date
        reviews = reviews[dates.between(*review_dates)]
    return products, reviews


def dashboard_summary(products, reviews):
    sold = _number(products, "quantity_sold").fillna(0)
    product_rating = _number(products, "rating_average")
    review_rating = _number(reviews, "rating")
    valid_reviews = review_rating[review_rating.between(1, 5)]
    price = _number(products, "price").dropna()
    sold_and_rated = sold.gt(0) & product_rating.gt(0)
    risk = int((sold_and_rated & product_rating.le(3)).sum())
    return {
        "revenue": float(_revenue(products).sum()),
        "products": len(products),
        "sold": float(sold.sum()),
        "reviews": len(reviews),
        "rating": float(valid_reviews.mean()) if not valid_reviews.empty else None,
        "negative_rate": float(valid_reviews.le(2).mean() * 100) if not valid_reviews.empty else None,
        "sellers": products["seller_id"].nunique() if "seller_id" in products else None,
        "risk": risk,
        "risk_rate": risk / int(sold_and_rated.sum()) * 100 if sold_and_rated.any() else None,
        "min_price": float(price.min()) if not price.empty else None,
        "max_price": float(price.max()) if not price.empty else None,
    }


def _money(value):
    if value is None or pd.isna(value):
        return "—"
    if abs(value) >= 1_000_000_000_000:
        return f"{value / 1_000_000_000_000:,.2f} nghìn tỷ ₫"
    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:,.2f} tỷ ₫"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:,.1f} triệu ₫"
    return f"{value:,.0f} ₫"


def _category_table(products):
    detail = products.copy()
    category = "root_category_name" if "root_category_name" in detail else "category_name"
    detail["Danh mục"] = detail[category].fillna("Chưa phân loại") if category in detail else "Chưa phân loại"
    detail["Doanh thu ước tính"] = _revenue(detail)
    detail["Giá"] = _number(detail, "price")
    detail["Đã bán"] = _number(detail, "quantity_sold").fillna(0)
    detail["Điểm sản phẩm"] = _number(detail, "rating_average").where(lambda values: values.gt(0))
    table = (detail.groupby("Danh mục", dropna=False)
             .agg(**{"Sản phẩm": ("Danh mục", "size"),
                     "Doanh thu ước tính": ("Doanh thu ước tính", "sum"),
                     "Đã bán": ("Đã bán", "sum"),
                     "Điểm sản phẩm TB": ("Điểm sản phẩm", "mean"),
                     "Giá thấp nhất": ("Giá", "min"),
                     "Giá cao nhất": ("Giá", "max")})
             .reset_index().sort_values("Doanh thu ước tính", ascending=False))
    total = table["Doanh thu ước tính"].sum()
    table["Tỷ trọng (%)"] = table["Doanh thu ước tính"] / total * 100 if total else 0.0
    table["Lũy kế (%)"] = table["Tỷ trọng (%)"].cumsum()
    return table


def _price_segment_table(products):
    if "price_segment" not in products:
        return pd.DataFrame()
    detail = pd.DataFrame({
        "Phân khúc": products["price_segment"].fillna("Chưa phân khúc"),
        "Doanh thu ước tính": _revenue(products),
        "Đã bán": _number(products, "quantity_sold").fillna(0),
    })
    return (detail.groupby("Phân khúc", dropna=False)
            .agg(**{"Sản phẩm": ("Phân khúc", "size"),
                    "Doanh thu ước tính": ("Doanh thu ước tính", "sum"),
                    "Đã bán": ("Đã bán", "sum")})
            .reset_index().sort_values("Doanh thu ước tính", ascending=False))


def _discount_band_table(products):
    discount = _number(products, "discount_rate")
    valid = discount.between(0, 100)
    if not valid.any():
        return pd.DataFrame()
    bands = pd.cut(discount[valid], [-.1, 0, 10, 25, 50, 100],
                   labels=["Không giảm", "1–10%", "11–25%", "26–50%", ">50%"])
    detail = pd.DataFrame({"Mức giảm": bands,
                           "Đã bán": _number(products, "quantity_sold")[valid].fillna(0).clip(lower=0),
                           "Doanh thu ước tính": _revenue(products)[valid]})
    table = (detail.groupby("Mức giảm", observed=True)
             .agg(**{"Sản phẩm": ("Mức giảm", "size"), "Đã bán": ("Đã bán", "sum"),
                     "Doanh thu ước tính": ("Doanh thu ước tính", "sum")})
             .reset_index())
    table["Đã bán/SP"] = table["Đã bán"] / table["Sản phẩm"]
    return table


def _price_category_table(products):
    category = "root_category_name" if "root_category_name" in products else "category_name"
    names = products[category].fillna("Chưa phân loại") if category in products else "Tất cả"
    detail = pd.DataFrame({"Danh mục": names, "Giá": _number(products, "price")})
    detail = detail[detail["Giá"].gt(0)]
    if detail.empty:
        return pd.DataFrame()
    return (detail.groupby("Danh mục")["Giá"]
            .agg(**{"Sản phẩm": "size", "Q1": lambda values: values.quantile(.25),
                    "Trung vị": "median", "Q3": lambda values: values.quantile(.75)})
            .reset_index().sort_values("Trung vị", ascending=False))


def _service_mix_table(products):
    if not {"is_tiki_now", "is_freeship_xtra"}.issubset(products):
        return pd.DataFrame()
    now = products["is_tiki_now"].map(_boolean)
    ship = products["is_freeship_xtra"].map(_boolean)
    valid = now.notna() & ship.notna()
    if not valid.any():
        return pd.DataFrame()
    detail = pd.DataFrame({"TikiNOW": now[valid].map({True: "Có", False: "Không"}),
                           "Freeship Xtra": ship[valid].map({True: "Có", False: "Không"}),
                           "Đã bán": _number(products, "quantity_sold")[valid].fillna(0).clip(lower=0),
                           "Doanh thu ước tính": _revenue(products)[valid]})
    groups = pd.MultiIndex.from_product([["Có", "Không"], ["Có", "Không"]],
                                         names=["TikiNOW", "Freeship Xtra"])
    table = (detail.groupby(["TikiNOW", "Freeship Xtra"])
             .agg(**{"Sản phẩm": ("Đã bán", "size"), "Đã bán": ("Đã bán", "sum"),
                     "Doanh thu ước tính": ("Doanh thu ước tính", "sum")})
             .reindex(groups, fill_value=0).reset_index())
    table["Nhóm dịch vụ"] = "NOW " + table["TikiNOW"] + " · Freeship " + table["Freeship Xtra"]
    table["Tỷ trọng sản phẩm (%)"] = table["Sản phẩm"] / table["Sản phẩm"].sum() * 100
    revenue = table["Doanh thu ước tính"].sum()
    table["Tỷ trọng doanh thu (%)"] = table["Doanh thu ước tính"] / revenue * 100 if revenue else 0.0
    table["Đã bán/SP"] = table["Đã bán"].div(table["Sản phẩm"].where(table["Sản phẩm"].gt(0))).fillna(0)
    return table


def _portfolio_concentration_table(products):
    revenue = _revenue(products).clip(lower=0).sort_values(ascending=False).reset_index(drop=True)
    total = revenue.sum()
    if not total:
        return pd.DataFrame()
    cumulative = revenue.cumsum()
    return pd.DataFrame({
        "Tỷ lệ sản phẩm đứng đầu (%)": range(101),
        "Tỷ lệ doanh thu lũy kế (%)": [
            0.0 if percent == 0 else cumulative.iloc[ceil(len(revenue) * percent / 100) - 1] / total * 100
            for percent in range(101)
        ],
    })


def _top_product_category_table(products):
    if products.empty:
        return pd.DataFrame()
    category = "root_category_name" if "root_category_name" in products else "category_name"
    detail = pd.DataFrame({
        "Danh mục": products[category].fillna("Chưa phân loại") if category in products else "Chưa phân loại",
        "Doanh thu ước tính": _revenue(products).clip(lower=0),
    })
    top = detail.nlargest(ceil(len(detail) * .1), "Doanh thu ước tính")
    return (top.groupby("Danh mục")
            .agg(**{"Sản phẩm": ("Danh mục", "size"),
                    "Doanh thu ước tính": ("Doanh thu ước tính", "sum")})
            .reset_index().sort_values("Doanh thu ước tính", ascending=False))


def _review_coverage_table(products):
    if "review_count" not in products:
        return pd.DataFrame()
    counts = _number(products, "review_count")
    valid = counts.ge(0) & counts.mod(1).eq(0)
    if not valid.any():
        return pd.DataFrame()
    labels = ["0", "1–9", "10–99", "≥100"]
    bands = pd.cut(counts[valid], [-1, 0, 9, 99, float("inf")], labels=labels)
    detail = pd.DataFrame({
        "Lượt đánh giá/SP": bands,
        "Doanh thu ước tính": _revenue(products)[valid].clip(lower=0),
    })
    table = (detail.groupby("Lượt đánh giá/SP", observed=True)
             .agg(**{"Sản phẩm": ("Doanh thu ước tính", "size"),
                     "Doanh thu ước tính": ("Doanh thu ước tính", "sum")})
             .reindex(labels, fill_value=0).reset_index())
    table["Tỷ trọng sản phẩm (%)"] = table["Sản phẩm"] / table["Sản phẩm"].sum() * 100
    total = table["Doanh thu ước tính"].sum()
    table["Tỷ trọng doanh thu (%)"] = table["Doanh thu ước tính"] / total * 100 if total else 0.0
    return table


def _review_coverage_category_table(products):
    if "review_count" not in products:
        return pd.DataFrame()
    counts = _number(products, "review_count")
    valid = counts.ge(0) & counts.mod(1).eq(0)
    if not valid.any():
        return pd.DataFrame()
    category = "root_category_name" if "root_category_name" in products else "category_name"
    names = products[category].fillna("Chưa phân loại") if category in products else "Chưa phân loại"
    detail = pd.DataFrame({"Danh mục": names[valid], "Có đánh giá": counts[valid].gt(0)})
    table = (detail.groupby("Danh mục")
             .agg(**{"Sản phẩm": ("Có đánh giá", "size"),
                     "Có đánh giá": ("Có đánh giá", "sum")})
             .reset_index())
    table["Tỷ lệ có đánh giá (%)"] = table["Có đánh giá"] / table["Sản phẩm"] * 100
    return table.sort_values("Tỷ lệ có đánh giá (%)")


def _review_category_table(products, reviews):
    category = "root_category_name" if "root_category_name" in products else "category_name"
    if not {"product_id", category}.issubset(products) or "product_id" not in reviews:
        return pd.DataFrame()
    lookup = products[["product_id", category]].dropna(subset=["product_id"]).copy()
    lookup["product_id"] = lookup["product_id"].astype(str)
    lookup = lookup.drop_duplicates("product_id").rename(columns={category: "Danh mục"})
    detail = pd.DataFrame({"product_id": reviews["product_id"].astype(str),
                           "Điểm": _number(reviews, "rating")})
    detail = detail[detail["Điểm"].between(1, 5)].merge(lookup, on="product_id", how="inner")
    if detail.empty:
        return pd.DataFrame()
    detail["Danh mục"] = detail["Danh mục"].fillna("Chưa phân loại")
    detail["Tiêu cực"] = detail["Điểm"].le(2)
    table = (detail.groupby("Danh mục")
             .agg(**{"Lượt đánh giá": ("Điểm", "size"),
                     "Đánh giá 1–2 sao": ("Tiêu cực", "sum"),
                     "Điểm TB": ("Điểm", "mean")})
             .reset_index())
    table["Tỷ lệ 1–2 sao (%)"] = table["Đánh giá 1–2 sao"] / table["Lượt đánh giá"] * 100
    return table.sort_values("Tỷ lệ 1–2 sao (%)", ascending=False)


def _seller_table(products):
    if "seller_id" not in products:
        return pd.DataFrame()
    detail = products.dropna(subset=["seller_id"]).copy()
    if detail.empty:
        return pd.DataFrame()
    detail["Nhà bán"] = detail["seller_id"].astype(str)
    detail["Doanh thu ước tính"] = _revenue(detail)
    table = (detail.groupby("Nhà bán")
             .agg(**{"Sản phẩm": ("Nhà bán", "size"),
                     "Doanh thu ước tính": ("Doanh thu ước tính", "sum")})
             .reset_index().sort_values("Doanh thu ước tính", ascending=False))
    total = table["Doanh thu ước tính"].sum()
    table["Tỷ trọng (%)"] = table["Doanh thu ước tính"] / total * 100 if total else 0.0
    return table


def _seller_comparison(sellers):
    top = sellers.head(10)
    if len(top) > 1 and top["Tỷ trọng (%)"].iloc[0] >= 60:
        return top.iloc[1:], top.iloc[0]
    return top, None


def _review_trend_table(reviews):
    if "created_at" not in reviews or "rating" not in reviews:
        return pd.DataFrame(), False
    dates = pd.to_datetime(reviews["created_at"], errors="coerce", utc=True).dt.tz_localize(None)
    ratings = _number(reviews, "rating")
    valid = dates.notna() & ratings.between(1, 5)
    if not valid.any():
        return pd.DataFrame(), False
    monthly = dates[valid].dt.to_period("M")
    annual = monthly.nunique() > 36
    periods = dates[valid].dt.to_period("Y" if annual else "M")
    trend = pd.DataFrame({"Kỳ": periods.dt.start_time,
                          "Sao": ratings[valid].astype(int),
                          "Lượt đánh giá": 1})
    return trend.groupby(["Kỳ", "Sao"], as_index=False)["Lượt đánh giá"].sum(), annual


def _chart(chart):
    st.altair_chart(chart.configure_view(stroke=None).configure_axis(
        labelColor="#52657b", titleColor="#123858", gridColor="#e8edf2", domain=False
    ), width="stretch")


def _filters(products, reviews):
    category_column = "root_category_name" if "root_category_name" in products else "category_name"
    categories = sorted(products[category_column].dropna().astype(str).unique()) if category_column in products else []
    prices = _number(products, "price").dropna()
    dates = (pd.to_datetime(reviews["created_at"], errors="coerce", utc=True).dropna()
             if "created_at" in reviews else pd.Series(dtype="datetime64[ns, UTC]"))
    with st.container(border=True):
        title, reset = st.columns([4, 1])
        title.header("Bộ lọc phân tích")
        if reset.button("Đặt lại", width="stretch"):
            st.session_state.update(dash_categories=[], dash_tikinow="Tất cả", dash_freeship="Tất cả")
            if not prices.empty:
                st.session_state.update(dash_price_min=int(prices.min()), dash_price_max=int(prices.max()))
            if not dates.empty:
                st.session_state.dash_dates = (dates.min().date(), dates.max().date())
            st.rerun()
        st.caption("Danh mục, giá và dịch vụ lọc toàn dashboard. Khoảng ngày chỉ lọc đánh giá, không đổi doanh thu ước tính.")
        with st.form("dashboard_filters"):
            fields = st.columns([2, 1, 1])
            with fields[0]:
                selected = st.multiselect("Danh mục chính", categories, placeholder="Tất cả danh mục", key="dash_categories")
            with fields[1]:
                tiki_now = st.selectbox("TikiNOW", ["Tất cả", "Có", "Không"], key="dash_tikinow",
                                        disabled="is_tiki_now" not in products)
            with fields[2]:
                freeship = st.selectbox("Freeship Xtra", ["Tất cả", "Có", "Không"], key="dash_freeship",
                                        disabled="is_freeship_xtra" not in products)
            price_range = None
            if not prices.empty and prices.min() < prices.max():
                price_cols = st.columns(2)
                lower = price_cols[0].number_input("Giá từ (VNĐ)", min_value=0, max_value=int(prices.max()),
                                                  value=int(prices.min()), step=10_000, key="dash_price_min")
                upper = price_cols[1].number_input("Giá đến (VNĐ)", min_value=0, max_value=int(prices.max()),
                                                  value=int(prices.max()), step=10_000, key="dash_price_max")
                price_range = (lower, upper)
                if lower > upper:
                    st.warning("Giá từ phải nhỏ hơn hoặc bằng giá đến.")
            review_dates = None
            if not dates.empty:
                selected_dates = st.date_input("Khoảng ngày đánh giá", (dates.min().date(), dates.max().date()),
                                               min_value=dates.min().date(), max_value=dates.max().date(), key="dash_dates")
                if len(selected_dates) == 2:
                    review_dates = selected_dates
                else:
                    st.warning("Chọn đủ ngày bắt đầu và kết thúc.")
            else:
                st.caption("Không có ngày đánh giá hợp lệ để lọc.")
            st.form_submit_button("Áp dụng bộ lọc", type="primary")
    return selected, price_range, tiki_now, freeship, review_dates


def show(df_products, df_reviews, _kpis=None):
    st.title("Trung tâm phân tích")
    st.caption("TikiLens / Dashboard · Ảnh chụp hiện tại của sản phẩm và đánh giá liên quan")
    if df_products.empty:
        st.warning("Chưa có dữ liệu sản phẩm. Kiểm tra kết nối hoặc làm mới dữ liệu ở thanh bên.")
        return
    products, reviews = filter_dashboard_data(df_products, df_reviews, *_filters(df_products, df_reviews))
    if products.empty:
        st.info("Không có sản phẩm phù hợp. Hãy nới bộ lọc hoặc nhấn Đặt lại.")
        return
    summary = dashboard_summary(products, reviews)
    st.caption(f"Đang xem **{summary['products']:,} / {len(df_products):,} sản phẩm** và **{summary['reviews']:,} / {len(df_reviews):,} đánh giá**.")

    st.header("Sức khỏe kinh doanh")
    row = st.columns(3)
    row[0].metric("Doanh thu ước tính", _money(summary["revenue"]),
                  help="Giá bán × số lượng đã bán trong ảnh chụp dữ liệu; không phải doanh thu giao dịch theo ngày.")
    row[1].metric("Sản phẩm", f"{summary['products']:,}")
    row[2].metric("Số lượng đã bán", f"{summary['sold']:,.0f}")
    row = st.columns(3)
    row[0].metric("Lượt đánh giá", f"{summary['reviews']:,}")
    row[1].metric("Điểm đánh giá", f"{summary['rating']:.2f} / 5" if summary["rating"] is not None else "—",
                  help="Trung bình điểm của lượt đánh giá sau lọc.")
    row[2].metric("Nhà bán", f"{summary['sellers']:,}" if summary["sellers"] is not None else "—")
    st.caption("Doanh thu là ước tính theo sản phẩm. Ngày đánh giá chỉ thay đổi các chỉ số và biểu đồ phản hồi.")

    table = _category_table(products)
    segments = _price_segment_table(products)
    discount_bands = _discount_band_table(products)
    price_categories = _price_category_table(products)
    service_mix = _service_mix_table(products)
    concentration = _portfolio_concentration_table(products)
    top_product_categories = _top_product_category_table(products)
    review_coverage = _review_coverage_table(products)
    review_coverage_categories = _review_coverage_category_table(products)
    review_categories = _review_category_table(products, reviews)
    sellers = _seller_table(products)
    st.header("Góc nhìn phân tích")
    business_tab, voice_tab, product_tab, price_tab, service_tab, concentration_tab, coverage_tab = st.tabs([
        "Cơ cấu kinh doanh", "Đánh giá & rủi ro", "Sản phẩm & nhà bán",
        "Giá & khuyến mãi", "Dịch vụ giao hàng", "Tập trung doanh thu", "Độ phủ đánh giá",
    ])

    with business_tab:
        st.subheader("Danh mục nào tạo phần lớn doanh thu?")
        st.caption("Biểu đồ Pareto xếp danh mục theo doanh thu ước tính; đường vàng cho biết tỷ trọng cộng dồn.")
        with st.container(border=True):
            base = alt.Chart(table).encode(x=alt.X(
                "Danh mục:N", sort=table["Danh mục"].tolist(), title=None,
                axis=alt.Axis(labelAngle=-30, labelLimit=135),
            ))
            bars = base.mark_bar(color=TIKI_BLUE, cornerRadiusEnd=3).encode(
                y=alt.Y("Doanh thu ước tính:Q", title="Doanh thu ước tính (VNĐ)", axis=alt.Axis(format="~s")),
                tooltip=["Danh mục:N", alt.Tooltip("Doanh thu ước tính:Q", format=",.0f"),
                         alt.Tooltip("Tỷ trọng (%):Q", format=".1f"), "Sản phẩm:Q"],
            )
            cumulative = base.mark_line(color=GOLD, point=True, strokeWidth=2.5).encode(
                y=alt.Y("Lũy kế (%):Q", title="Tỷ trọng lũy kế (%)",
                        scale=alt.Scale(domain=[0, 100]), axis=alt.Axis(orient="right")),
                tooltip=["Danh mục:N", alt.Tooltip("Lũy kế (%):Q", format=".1f")],
            )
            _chart(alt.layer(bars, cumulative).resolve_scale(y="independent").properties(height=330))
            st.caption(f"Ba danh mục đứng đầu chiếm **{table['Tỷ trọng (%)'].head(3).sum():.1f}%** doanh thu ước tính trong phạm vi lọc.")

        st.subheader("Phân khúc giá: doanh thu và lượng bán")
        if segments.empty:
            st.info("Dữ liệu chưa có phân khúc giá để phân tích.")
        else:
            left, right = st.columns(2)
            for slot, metric, color in ((left, "Doanh thu ước tính", TIKI_BLUE), (right, "Đã bán", GOLD)):
                with slot, st.container(border=True):
                    st.markdown(f"**{metric} theo phân khúc**")
                    chart = alt.Chart(segments).mark_bar(color=color, cornerRadiusEnd=3).encode(
                        x=alt.X(f"{metric}:Q", axis=alt.Axis(format="~s"), title=metric),
                        y=alt.Y("Phân khúc:N", sort=segments["Phân khúc"].tolist(), title=None,
                                axis=alt.Axis(labelLimit=190)),
                        tooltip=["Phân khúc:N", alt.Tooltip(f"{metric}:Q", format=",.0f"), "Sản phẩm:Q"],
                    ).properties(height=255)
                    _chart(chart)
        st.caption("Hai biểu đồ mô tả cơ cấu hiện tại; không suy ra tăng trưởng theo thời gian từ số lượng đã bán tích lũy.")

        st.subheader("Danh mục nào cần ưu tiên xem phản hồi?")
        opportunity = table.merge(review_categories[["Danh mục", "Lượt đánh giá", "Tỷ lệ 1–2 sao (%)"]],
                                  on="Danh mục", how="inner") if not review_categories.empty else pd.DataFrame()
        opportunity = opportunity[opportunity["Lượt đánh giá"] >= 30] if not opportunity.empty else opportunity
        if opportunity.empty:
            st.info("Cần ít nhất 30 đánh giá hợp lệ mỗi danh mục để so sánh tỷ lệ tiêu cực.")
        else:
            with st.container(border=True):
                chart = alt.Chart(opportunity).mark_circle(opacity=.8, stroke="white", strokeWidth=1).encode(
                    x=alt.X("Tỷ trọng (%):Q", title="Tỷ trọng doanh thu ước tính (%)"),
                    y=alt.Y("Tỷ lệ 1–2 sao (%):Q", title="Tỷ lệ đánh giá 1–2 sao (%)"),
                    size=alt.Size("Sản phẩm:Q", scale=alt.Scale(range=[80, 950]), title="Sản phẩm"),
                    color=alt.Color("Điểm sản phẩm TB:Q", scale=alt.Scale(scheme="blues"),
                                    title="Điểm sản phẩm TB"),
                    tooltip=["Danh mục:N", alt.Tooltip("Tỷ trọng (%):Q", format=".1f"),
                             alt.Tooltip("Tỷ lệ 1–2 sao (%):Q", format=".1f"),
                             "Lượt đánh giá:Q", "Sản phẩm:Q"],
                ).properties(height=340)
                _chart(chart)
                st.caption("Góc trên bên phải là danh mục có tỷ trọng doanh thu cao và nhiều đánh giá 1–2 sao; kích thước điểm là số sản phẩm.")

    with voice_tab:
        st.subheader("Phản hồi khách hàng thay đổi ra sao?")
        voice_metrics = st.columns(3)
        voice_metrics[0].metric("Đánh giá 1–2 sao", f"{summary['negative_rate']:.1f}%" if summary["negative_rate"] is not None else "—",
                                help="Số đánh giá 1–2 sao / số đánh giá có điểm hợp lệ.")
        voice_metrics[1].metric("Điểm đánh giá TB", f"{summary['rating']:.2f} / 5" if summary["rating"] is not None else "—")
        voice_metrics[2].metric("Lượt đánh giá", f"{summary['reviews']:,}")
        trend, annual = _review_trend_table(reviews)
        with st.container(border=True):
            st.markdown("**Xu hướng đánh giá theo số sao**")
            if trend.empty:
                st.info("Chưa có ngày và điểm đánh giá hợp lệ trong phạm vi lọc.")
            else:
                chart = alt.Chart(trend).mark_area(opacity=.9).encode(
                    x=alt.X("Kỳ:T", title="Năm" if annual else "Tháng",
                            axis=alt.Axis(format="%Y" if annual else "%m/%Y", tickCount=10)),
                    y=alt.Y("sum(Lượt đánh giá):Q", title="Lượt đánh giá"),
                    color=alt.Color("Sao:O", scale=alt.Scale(domain=[1, 2, 3, 4, 5],
                                     range=["#c75b52", "#df9365", "#e4bd70", "#7bb9b1", TIKI_BLUE]),
                                    title="Số sao"),
                    tooltip=[alt.Tooltip("Kỳ:T", format="%Y" if annual else "%m/%Y"),
                             "Sao:O", alt.Tooltip("Lượt đánh giá:Q", format=",.0f")],
                ).properties(height=310)
                _chart(chart)
                st.caption("Khoảng dài được gộp theo năm. Kỳ cuối có thể chưa đủ dữ liệu; đây là lượt đánh giá, không phải doanh số.")
        left, right = st.columns([1, 1.3])
        with left, st.container(border=True):
            st.markdown("**Phân bố số sao**")
            ratings = _number(reviews, "rating")
            counts = (ratings[ratings.between(1, 5)].value_counts()
                      .reindex([1, 2, 3, 4, 5], fill_value=0)
                      .rename_axis("Sao").reset_index(name="Lượt đánh giá"))
            if counts["Lượt đánh giá"].sum():
                chart = alt.Chart(counts).mark_bar(color=GOLD, cornerRadiusEnd=3).encode(
                    x=alt.X("Sao:O", title="Số sao", axis=alt.Axis(labelAngle=0)),
                    y=alt.Y("Lượt đánh giá:Q"),
                    tooltip=["Sao:O", alt.Tooltip("Lượt đánh giá:Q", format=",.0f")],
                ).properties(height=300)
                _chart(chart)
            else:
                st.info("Chưa có đánh giá hợp lệ.")
        with right, st.container(border=True):
            st.markdown("**Tỷ lệ 1–2 sao theo danh mục**")
            eligible = review_categories[review_categories["Lượt đánh giá"] >= 30] if not review_categories.empty else pd.DataFrame()
            if eligible.empty:
                st.info("Không đủ 30 đánh giá hợp lệ trong mỗi danh mục để so sánh.")
            else:
                chart = alt.Chart(eligible).mark_bar(color="#c97855", cornerRadiusEnd=3).encode(
                    x=alt.X("Tỷ lệ 1–2 sao (%):Q", title="Tỷ lệ đánh giá 1–2 sao (%)"),
                    y=alt.Y("Danh mục:N", sort="-x", title=None, axis=alt.Axis(labelLimit=180)),
                    tooltip=["Danh mục:N", alt.Tooltip("Tỷ lệ 1–2 sao (%):Q", format=".1f"),
                             "Lượt đánh giá:Q", "Đánh giá 1–2 sao:Q"],
                ).properties(height=300)
                _chart(chart)
            st.caption("Chỉ hiển thị danh mục có ít nhất 30 đánh giá; tỷ lệ không thay thế việc đọc nội dung phản hồi.")

    with product_tab:
        st.subheader("Sản phẩm và nhà bán cần chú ý")
        risk_metrics = st.columns(3)
        risk_metrics[0].metric("SP đã bán, điểm ≤ 3", f"{summary['risk']:,}")
        risk_metrics[1].metric("Tỷ lệ trong SP đã bán & có điểm", f"{summary['risk_rate']:.1f}%" if summary["risk_rate"] is not None else "—")
        risk_metrics[2].metric("Tỷ trọng Top 10 nhà bán",
                               f"{sellers['Tỷ trọng (%)'].head(10).sum():.1f}%" if not sellers.empty else "—")
        st.caption("Điểm thấp là tín hiệu rà soát, chưa đủ để kết luận sản phẩm kém chất lượng.")
        with st.container(border=True):
            st.markdown("**Nhà bán đóng góp doanh thu ước tính cao**")
            if sellers.empty:
                st.info("Dữ liệu chưa có mã nhà bán.")
            else:
                chart_sellers, leader = _seller_comparison(sellers)
                if leader is not None:
                    st.caption(f"Nhà bán {leader['Nhà bán']} chiếm **{leader['Tỷ trọng (%)']:.1f}%** doanh thu ước tính; biểu đồ so sánh các nhà bán xếp sau.")
                chart = alt.Chart(chart_sellers).mark_bar(color=TIKI_BLUE, cornerRadiusEnd=3).encode(
                    x=alt.X("Doanh thu ước tính:Q", axis=alt.Axis(format="~s"), title="Doanh thu ước tính (VNĐ)"),
                    y=alt.Y("Nhà bán:N", sort="-x", title=None),
                    tooltip=["Nhà bán:N", alt.Tooltip("Doanh thu ước tính:Q", format=",.0f"),
                             alt.Tooltip("Tỷ trọng (%):Q", format=".1f"), "Sản phẩm:Q"],
                ).properties(height=330)
                _chart(chart)
                st.caption("Xếp theo doanh thu ước tính từ ảnh chụp sản phẩm; mã nhà bán được giữ như trong dữ liệu.")
        with st.container(border=True):
            st.markdown("**Giảm giá, điểm sản phẩm và lượng bán**")
            scatter = pd.DataFrame({"Giảm giá (%)": _number(products, "discount_rate"),
                                    "Điểm sản phẩm": _number(products, "rating_average"),
                                    "Đã bán": _number(products, "quantity_sold").clip(lower=0),
                                    "Phân khúc": products["price_segment"].fillna("Chưa phân khúc")
                                    if "price_segment" in products else "Tất cả"})
            scatter = scatter[scatter["Giảm giá (%)"].between(0, 100) &
                              scatter["Điểm sản phẩm"].gt(0) &
                              scatter["Điểm sản phẩm"].le(5)].dropna()
            scatter = scatter.sample(n=min(1500, len(scatter)), random_state=42)
            if scatter.empty:
                st.info("Chưa có đủ dữ liệu giảm giá và điểm sản phẩm.")
            else:
                chart = alt.Chart(scatter).mark_circle(opacity=.4, stroke="white", strokeWidth=.5).encode(
                    x=alt.X("Giảm giá (%):Q", title="Mức giảm giá (%)"),
                    y=alt.Y("Điểm sản phẩm:Q", scale=alt.Scale(domain=[1, 5])),
                    size=alt.Size("Đã bán:Q", scale=alt.Scale(type="sqrt", range=[30, 430]), title="Đã bán"),
                    color=alt.Color("Phân khúc:N", scale=alt.Scale(scheme="tableau10"), title="Phân khúc"),
                    tooltip=[alt.Tooltip("Giảm giá (%):Q", format=".1f"),
                             alt.Tooltip("Điểm sản phẩm:Q", format=".2f"),
                             alt.Tooltip("Đã bán:Q", format=",.0f"), "Phân khúc:N"],
                ).properties(height=330)
                _chart(chart)
                st.caption("Mỗi điểm là một sản phẩm đã có điểm đánh giá; cỡ điểm biểu thị lượng đã bán. Tối đa 1.500 điểm được lấy mẫu; tương quan không chứng minh quan hệ nhân quả.")

    with price_tab:
        st.subheader("Giá bán và mức giảm giá")
        prices = _number(products, "price")
        discounts = _number(products, "discount_rate")
        valid_discounts = discounts[discounts.between(0, 100)]
        discounted = valid_discounts[valid_discounts.gt(0)]
        price_metrics = st.columns(3)
        price_metrics[0].metric("Giá trung vị", _money(prices[prices.gt(0)].median()))
        price_metrics[1].metric("SP có giảm giá", f"{valid_discounts.gt(0).mean() * 100:.1f}%" if not valid_discounts.empty else "—")
        price_metrics[2].metric("Mức giảm trung vị", f"{discounted.median():.0f}%" if not discounted.empty else "—",
                                help="Chỉ tính sản phẩm có mức giảm từ 1% đến 100%.")
        st.caption("Mức giảm lấy từ dữ liệu sản phẩm hiện tại; không có lịch sử giá để đo tác động của chương trình khuyến mãi.")
        if discount_bands.empty:
            st.info("Chưa có mức giảm giá hợp lệ trong phạm vi lọc.")
        else:
            left, right = st.columns(2)
            for slot, metric, color in ((left, "Sản phẩm", TIKI_BLUE), (right, "Đã bán/SP", GOLD)):
                with slot, st.container(border=True):
                    st.markdown(f"**{metric} theo mức giảm**")
                    chart = alt.Chart(discount_bands).mark_bar(color=color, cornerRadiusEnd=3).encode(
                        x=alt.X(f"{metric}:Q", title=metric, axis=alt.Axis(format="~s")),
                        y=alt.Y("Mức giảm:N", sort=discount_bands["Mức giảm"].tolist(), title=None),
                        tooltip=["Mức giảm:N", "Sản phẩm:Q", alt.Tooltip("Đã bán:Q", format=",.0f"),
                                 alt.Tooltip("Đã bán/SP:Q", format=",.1f")],
                    ).properties(height=250)
                    _chart(chart)
            st.caption("Lượng đã bán là số tích lũy bình quân mỗi sản phẩm; chênh lệch giữa nhóm giảm giá không chứng minh khuyến mãi làm tăng lượng bán.")
        st.subheader("Khoảng giá điển hình theo danh mục")
        if price_categories.empty:
            st.info("Chưa có giá dương hợp lệ để so sánh theo danh mục.")
        else:
            with st.container(border=True):
                base = alt.Chart(price_categories).encode(
                    y=alt.Y("Danh mục:N", sort=price_categories["Danh mục"].tolist(), title=None,
                            axis=alt.Axis(labelLimit=210)),
                    tooltip=["Danh mục:N", "Sản phẩm:Q", alt.Tooltip("Q1:Q", format=",.0f"),
                             alt.Tooltip("Trung vị:Q", format=",.0f"), alt.Tooltip("Q3:Q", format=",.0f")],
                )
                interval = base.mark_rule(color=TIKI_BLUE, strokeWidth=5).encode(
                    x=alt.X("Q1:Q", title="Giá (VNĐ)", scale=alt.Scale(type="log"),
                            axis=alt.Axis(format="~s")), x2="Q3:Q")
                median = base.mark_circle(color=GOLD, size=105).encode(
                    x=alt.X("Trung vị:Q", scale=alt.Scale(type="log")))
                _chart(alt.layer(interval, median).properties(height=max(280, 32 * len(price_categories))))
                st.caption("Vạch là khoảng 25–75% giá sản phẩm, chấm là giá trung vị. Trục giá dùng thang logarit để đọc được cả danh mục giá thấp và cao.")

    with service_tab:
        st.subheader("Độ phủ dịch vụ giao hàng")
        if service_mix.empty:
            st.info("Chưa có đủ cờ TikiNOW và Freeship Xtra hợp lệ trong phạm vi lọc.")
        else:
            total = service_mix["Sản phẩm"].sum()
            coverage = st.columns(3)
            coverage[0].metric("SP có TikiNOW", f"{service_mix.loc[service_mix['TikiNOW'].eq('Có'), 'Sản phẩm'].sum() / total * 100:.1f}%")
            coverage[1].metric("SP có Freeship Xtra", f"{service_mix.loc[service_mix['Freeship Xtra'].eq('Có'), 'Sản phẩm'].sum() / total * 100:.1f}%")
            coverage[2].metric("SP có cả hai", f"{service_mix.loc[service_mix['TikiNOW'].eq('Có') & service_mix['Freeship Xtra'].eq('Có'), 'Sản phẩm'].sum() / total * 100:.1f}%")
            st.caption(f"Mẫu gồm {total:,} sản phẩm có đủ hai cờ dịch vụ trong phạm vi lọc.")
            with st.container(border=True):
                st.markdown("**Tỷ trọng sản phẩm so với doanh thu ước tính**")
                mix_long = service_mix.melt(id_vars="Nhóm dịch vụ",
                                            value_vars=["Tỷ trọng sản phẩm (%)", "Tỷ trọng doanh thu (%)"],
                                            var_name="Chỉ số", value_name="Tỷ trọng (%)")
                chart = alt.Chart(mix_long).mark_bar(cornerRadiusEnd=3).encode(
                    x=alt.X("Tỷ trọng (%):Q", title="Tỷ trọng trong phạm vi lọc (%)",
                            scale=alt.Scale(domain=[0, 100])),
                    y=alt.Y("Nhóm dịch vụ:N", sort=service_mix["Nhóm dịch vụ"].tolist(), title=None,
                            axis=alt.Axis(labelLimit=220)),
                    yOffset="Chỉ số:N",
                    color=alt.Color("Chỉ số:N", scale=alt.Scale(
                        domain=["Tỷ trọng sản phẩm (%)", "Tỷ trọng doanh thu (%)"], range=[TIKI_BLUE, GOLD]),
                                    title=None),
                    tooltip=["Nhóm dịch vụ:N", "Chỉ số:N", alt.Tooltip("Tỷ trọng (%):Q", format=".1f")],
                ).properties(height=300)
                _chart(chart)
            with st.container(border=True):
                st.markdown("**Lượng đã bán bình quân mỗi sản phẩm**")
                active_groups = service_mix[service_mix["Sản phẩm"].gt(0)]
                benchmark = active_groups["Đã bán"].sum() / active_groups["Sản phẩm"].sum()
                bars = alt.Chart(active_groups).mark_bar(color=TIKI_BLUE, cornerRadiusEnd=3).encode(
                    x=alt.X("Đã bán/SP:Q", title="Số lượng đã bán / sản phẩm", axis=alt.Axis(format="~s")),
                    y=alt.Y("Nhóm dịch vụ:N", sort=service_mix["Nhóm dịch vụ"].tolist(), title=None,
                            axis=alt.Axis(labelLimit=220)),
                    tooltip=["Nhóm dịch vụ:N", "Sản phẩm:Q", alt.Tooltip("Đã bán:Q", format=",.0f"),
                             alt.Tooltip("Đã bán/SP:Q", format=",.1f")],
                )
                reference = alt.Chart(pd.DataFrame({"Mốc chung": [benchmark]})).mark_rule(
                    color=GOLD, strokeWidth=2, strokeDash=[5, 5]).encode(x="Mốc chung:Q")
                _chart(alt.layer(bars, reference).properties(height=260))
                st.caption("Đường vàng là bình quân toàn bộ sản phẩm có cờ dịch vụ hợp lệ. Đây là lượng bán tích lũy, chưa loại trừ ảnh hưởng giá và danh mục.")

    with concentration_tab:
        st.subheader("Doanh thu tập trung vào bao nhiêu sản phẩm?")
        if concentration.empty:
            st.info("Chưa có doanh thu ước tính dương trong phạm vi lọc.")
        else:
            concentration_metrics = st.columns(3)
            concentration_metrics[0].metric("Top 1% sản phẩm", f"{concentration.iloc[1, 1]:.1f}%",
                                            help="Tỷ trọng doanh thu ước tính của 1% sản phẩm đứng đầu, làm tròn số sản phẩm lên.")
            concentration_metrics[1].metric("Top 10% sản phẩm", f"{concentration.iloc[10, 1]:.1f}%")
            active = _revenue(products).gt(0).sum()
            concentration_metrics[2].metric("SP có doanh thu ước tính", f"{active / len(products) * 100:.1f}%")
            st.caption("Xếp sản phẩm theo doanh thu ước tính giảm dần; mẫu số là toàn bộ sản phẩm sau lọc. Doanh thu âm được tính bằng 0 trong phân tích này.")
            with st.container(border=True):
                st.markdown("**Đường tích lũy doanh thu theo tỷ lệ sản phẩm đứng đầu**")
                base = alt.Chart(concentration).encode(
                    x=alt.X("Tỷ lệ sản phẩm đứng đầu (%):Q", scale=alt.Scale(domain=[0, 100]),
                            title="Tỷ lệ sản phẩm đứng đầu (%)"),
                )
                equal_share = base.mark_line(color="#a9b8c8", strokeDash=[5, 5]).encode(
                    y=alt.Y("Tỷ lệ sản phẩm đứng đầu (%):Q", scale=alt.Scale(domain=[0, 100]),
                            title="Tỷ lệ doanh thu lũy kế (%)"))
                curve = base.mark_line(color=TIKI_BLUE, strokeWidth=3).encode(
                    y=alt.Y("Tỷ lệ doanh thu lũy kế (%):Q", scale=alt.Scale(domain=[0, 100])),
                    tooltip=[alt.Tooltip("Tỷ lệ sản phẩm đứng đầu (%):Q", format=".0f"),
                             alt.Tooltip("Tỷ lệ doanh thu lũy kế (%):Q", format=".1f")],
                )
                _chart(alt.layer(equal_share, curve).properties(height=320))
                st.caption("Đường xám biểu thị mức phân bổ đều. Đường xanh càng dốc ở đầu thì doanh thu càng tập trung vào ít sản phẩm.")
            with st.container(border=True):
                st.markdown("**Danh mục trong nhóm 10% sản phẩm dẫn đầu**")
                top_categories = top_product_categories.head(8)
                chart = alt.Chart(top_categories).mark_bar(color=GOLD, cornerRadiusEnd=3).encode(
                    x=alt.X("Doanh thu ước tính:Q", title="Doanh thu ước tính (VNĐ)", axis=alt.Axis(format="~s")),
                    y=alt.Y("Danh mục:N", sort=top_categories["Danh mục"].tolist(), title=None,
                            axis=alt.Axis(labelLimit=210)),
                    tooltip=["Danh mục:N", "Sản phẩm:Q",
                             alt.Tooltip("Doanh thu ước tính:Q", format=",.0f")],
                ).properties(height=max(260, 34 * len(top_categories)))
                _chart(chart)
                st.caption("Chỉ hiển thị tối đa 8 danh mục; bảng chi tiết và tệp Excel chứa toàn bộ danh mục trong nhóm dẫn đầu.")

    with coverage_tab:
        st.subheader("Sản phẩm nào đã có phản hồi?")
        if review_coverage.empty:
            st.info("Chưa có số lượt đánh giá trên sản phẩm hợp lệ trong phạm vi lọc.")
        else:
            known = review_coverage["Sản phẩm"].sum()
            unreviewed = review_coverage.loc[review_coverage["Lượt đánh giá/SP"].eq("0"), "Sản phẩm"].sum()
            no_review_sold = (_number(products, "review_count").eq(0) &
                              _number(products, "quantity_sold").gt(0)).sum()
            coverage_metrics = st.columns(3)
            coverage_metrics[0].metric("SP có đánh giá", f"{(known - unreviewed) / known * 100:.1f}%")
            coverage_metrics[1].metric("Đã bán, chưa đánh giá", f"{no_review_sold:,}")
            coverage_metrics[2].metric("SP có ≥100 đánh giá",
                                       f"{review_coverage.loc[review_coverage['Lượt đánh giá/SP'].eq('≥100'), 'Sản phẩm'].sum() / known * 100:.1f}%")
            st.caption(f"Mẫu gồm {known:,} sản phẩm có số lượt đánh giá hợp lệ. Đây là tổng đánh giá gắn với sản phẩm tại thời điểm thu thập; bộ lọc ngày đánh giá không áp dụng cho tab này.")
            with st.container(border=True):
                st.markdown("**Độ phủ đánh giá và tỷ trọng doanh thu**")
                long = review_coverage.melt(id_vars="Lượt đánh giá/SP",
                                            value_vars=["Tỷ trọng sản phẩm (%)", "Tỷ trọng doanh thu (%)"],
                                            var_name="Chỉ số", value_name="Tỷ trọng (%)")
                chart = alt.Chart(long).mark_bar(cornerRadiusEnd=3).encode(
                    x=alt.X("Tỷ trọng (%):Q", title="Tỷ trọng trong phạm vi lọc (%)",
                            scale=alt.Scale(domain=[0, 100])),
                    y=alt.Y("Lượt đánh giá/SP:N", sort=["0", "1–9", "10–99", "≥100"], title=None),
                    yOffset="Chỉ số:N",
                    color=alt.Color("Chỉ số:N", scale=alt.Scale(
                        domain=["Tỷ trọng sản phẩm (%)", "Tỷ trọng doanh thu (%)"], range=[TIKI_BLUE, GOLD]),
                                    title=None),
                    tooltip=["Lượt đánh giá/SP:N", "Chỉ số:N", alt.Tooltip("Tỷ trọng (%):Q", format=".1f")],
                ).properties(height=290)
                _chart(chart)
            with st.container(border=True):
                st.markdown("**Tỷ lệ sản phẩm có đánh giá theo danh mục**")
                eligible = review_coverage_categories[review_coverage_categories["Sản phẩm"].ge(20)]
                if eligible.empty:
                    st.info("Cần ít nhất 20 sản phẩm có lượt đánh giá hợp lệ mỗi danh mục để so sánh.")
                else:
                    chart = alt.Chart(eligible).mark_bar(color=TIKI_BLUE, cornerRadiusEnd=3).encode(
                        x=alt.X("Tỷ lệ có đánh giá (%):Q", title="Sản phẩm có ít nhất 1 đánh giá (%)",
                                scale=alt.Scale(domain=[0, 100])),
                        y=alt.Y("Danh mục:N", sort=eligible["Danh mục"].tolist(), title=None,
                                axis=alt.Axis(labelLimit=210)),
                        tooltip=["Danh mục:N", "Sản phẩm:Q", "Có đánh giá:Q",
                                 alt.Tooltip("Tỷ lệ có đánh giá (%):Q", format=".1f")],
                    ).properties(height=max(280, 32 * len(eligible)))
                    _chart(chart)
                    st.caption("Chỉ so sánh danh mục có ít nhất 20 sản phẩm. Chưa có đánh giá không đồng nghĩa với sản phẩm kém chất lượng.")

    with st.expander("Bảng chi tiết và sản phẩm nổi bật"):
        detail_tables = {
            "Danh mục": table, "Phân khúc": segments, "Giảm giá": discount_bands,
            "Khoảng giá": price_categories, "Dịch vụ": service_mix,
            "Tập trung doanh thu": concentration, "Danh mục trong Top 10%": top_product_categories,
            "Độ phủ đánh giá": review_coverage, "Độ phủ theo danh mục": review_coverage_categories,
            "Đánh giá": review_categories, "Nhà bán": sellers,
        }
        selected_detail = st.selectbox("Chọn bảng dữ liệu", [*detail_tables, "Sản phẩm nổi bật"])
        if selected_detail == "Sản phẩm nổi bật":
            detail = products.copy()
            detail["Doanh thu ước tính"] = _revenue(detail)
            columns = [c for c in ("product_id", "name", "category_name", "price", "quantity_sold",
                                   "rating_average", "Doanh thu ước tính") if c in detail]
            st.dataframe(detail.nlargest(20, "Doanh thu ước tính")[columns], hide_index=True, width="stretch")
            st.caption("Xếp hạng theo doanh thu ước tính của sản phẩm trong ảnh chụp hiện tại.")
        else:
            st.dataframe(detail_tables[selected_detail], hide_index=True, width="stretch")

    with st.container(border=True):
        st.markdown("**Xuất dữ liệu đã lọc**")
        st.caption("Các tệp dùng cùng phạm vi sản phẩm và đánh giá đang hiển thị.")
        report = pd.DataFrame([
            ("Doanh thu ước tính (VNĐ)", summary["revenue"]), ("Sản phẩm", summary["products"]),
            ("Số lượng đã bán", summary["sold"]), ("Lượt đánh giá", summary["reviews"]),
            ("Điểm đánh giá trung bình", summary["rating"]), ("Nhà bán", summary["sellers"]),
            ("Sản phẩm điểm thấp đã bán", summary["risk"]),
            ("Tỷ lệ đánh giá 1–2 sao (%)", summary["negative_rate"]),
            ("Tỷ lệ sản phẩm đã bán có điểm thấp (%)", summary["risk_rate"]),
        ], columns=["Chỉ số", "Giá trị"])
        a, b, c = st.columns(3)
        a.download_button("KPI · CSV", dataframe_to_csv(report), "tikilens_kpi.csv", "text/csv", width="stretch")
        b.download_button("Danh mục · CSV", dataframe_to_csv(table), "tikilens_danh_muc.csv", "text/csv", width="stretch")
        c.download_button("Báo cáo · Excel", lambda: excel_workbook_bytes({
            "KPI": report, "Danh muc": table, "Phan khuc": segments,
            "Giam gia": discount_bands, "Gia theo DM": price_categories, "Dich vu": service_mix,
            "Tap trung SP": concentration, "Top DM 10pct": top_product_categories,
            "Do phu DG": review_coverage, "Do phu theo DM": review_coverage_categories,
            "Danh gia theo DM": review_categories, "Nha ban": sellers,
            "San pham": products, "Danh gia": reviews,
        }), "tikilens_bao_cao.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                          width="stretch")

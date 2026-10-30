from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


NUMERIC_FEATURES = [
    "price", "original_price", "discount", "discount_rate", "rating_average", "review_count",
]
CATEGORICAL_FEATURES = [
    "price_segment", "seller_type", "is_official_store", "is_authentic", "is_freeship_xtra",
]
# Fixed Chapter 4 snapshot; live product edits do not alter the reported evaluation.
REFERENCE_DATA = Path(__file__).resolve().parents[1] / "data" / "forecast_reference.csv"


@st.cache_data(show_spinner=False)
def _load_reference_products() -> pd.DataFrame:
    return pd.read_csv(REFERENCE_DATA, low_memory=False)


def _evaluation_frame(actual, predicted) -> pd.DataFrame:
    """Prepare actual, estimated, and residual values for forecast charts."""
    evaluation = pd.DataFrame(
        {
            "Thực tế": pd.to_numeric(pd.Series(actual).reset_index(drop=True), errors="coerce"),
            "Ước lượng": pd.to_numeric(pd.Series(predicted).reset_index(drop=True), errors="coerce"),
        }
    ).dropna()
    evaluation["Sai số"] = evaluation["Ước lượng"] - evaluation["Thực tế"]
    return evaluation.reset_index(drop=True)


@st.cache_resource(show_spinner=False)
def _build_model(df_products):
    numeric_features = NUMERIC_FEATURES
    categorical_features = CATEGORICAL_FEATURES
    required = numeric_features + categorical_features + ["quantity_sold"]
    missing = [column for column in required if column not in df_products.columns]
    if missing:
        return None, None, None, f"Dữ liệu thiếu cột: {', '.join(missing)}."

    data = df_products[required].copy()
    for column in numeric_features + ["quantity_sold"]:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data.dropna().copy()
    if len(data) < 50:
        return None, None, None, "Cần ít nhất 50 sản phẩm đủ dữ liệu để huấn luyện."

    pipeline = Pipeline(
        steps=[
            ("preprocessor", ColumnTransformer(transformers=[
                ("num", StandardScaler(), numeric_features),
                ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_features),
            ])),
            ("regressor", RandomForestRegressor(n_estimators=100, random_state=42)),
        ]
    )
    X = data[numeric_features + categorical_features]
    y = data["quantity_sold"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    pipeline.fit(X_train, y_train)
    prediction = pipeline.predict(X_test)
    metrics = {
        "MAE": mean_absolute_error(y_test, prediction),
        "RMSE": np.sqrt(mean_squared_error(y_test, prediction)),
        "R2": r2_score(y_test, prediction),
    }
    evaluation = _evaluation_frame(y_test, prediction)
    return pipeline, metrics, (numeric_features, categorical_features, X, y, evaluation), None


def show():
    st.title("Dự báo số lượng bán")
    try:
        df_products = _load_reference_products()
    except FileNotFoundError:
        st.error("Không tìm thấy bộ dữ liệu tham chiếu của Chương 4.")
        return
    if df_products.empty:
        st.warning("Bộ dữ liệu tham chiếu không có sản phẩm.")
        return

    with st.spinner("Đang huấn luyện và đánh giá mô hình..."):
        pipeline, metrics, details, error = _build_model(df_products)
    if error:
        st.info(error)
        return

    mae, rmse, r2 = st.columns(3)
    mae.metric("MAE", f"{metrics['MAE']:,.2f}")
    rmse.metric("RMSE", f"{metrics['RMSE']:,.2f}")
    r2.metric("R²", f"{metrics['R2']:.6f}")
    st.caption(
        f"Dữ liệu tham chiếu Chương 4: {len(details[2]):,} sản phẩm; "
        f"{len(details[2]) - len(details[4]):,} huấn luyện / {len(details[4]):,} kiểm tra. "
        "Random Forest 100 cây trên ảnh chụp cố định; không phải dự báo doanh số tương lai."
    )

    numeric_features, categorical_features, X, y, evaluation = details
    if not evaluation.empty:
        st.subheader("Đánh giá trực quan trên tập kiểm tra")
        minimum = float(min(evaluation["Thực tế"].min(), evaluation["Ước lượng"].min()))
        maximum = float(max(evaluation["Thực tế"].max(), evaluation["Ước lượng"].max()))
        if minimum == maximum:
            maximum = minimum + 1.0
        reference = pd.DataFrame({"Giá trị": [minimum, maximum]})

        actual_chart, residual_chart = st.columns((3, 2))
        with actual_chart:
            diagonal = alt.Chart(reference).mark_line(
                color="#7a8795", strokeDash=[5, 4]
            ).encode(x="Giá trị:Q", y="Giá trị:Q")
            points = alt.Chart(evaluation).mark_circle(
                color="#0b74e5", opacity=0.7, size=58, stroke="white", strokeWidth=0.5
            ).encode(
                x=alt.X("Thực tế:Q", title="Số lượng bán thực tế", scale=alt.Scale(domain=[minimum, maximum])),
                y=alt.Y("Ước lượng:Q", title="Số lượng bán ước lượng", scale=alt.Scale(domain=[minimum, maximum])),
                tooltip=[
                    alt.Tooltip("Thực tế:Q", format=",.0f"),
                    alt.Tooltip("Ước lượng:Q", format=",.0f"),
                    alt.Tooltip("Sai số:Q", format=",.0f"),
                ],
            )
            st.altair_chart((diagonal + points).properties(height=330).interactive(), use_container_width=True)
        with residual_chart:
            residuals = alt.Chart(evaluation).mark_bar(color="#d99a4e", cornerRadiusEnd=3).encode(
                x=alt.X("Sai số:Q", bin=alt.Bin(maxbins=24), title="Sai số (ước lượng − thực tế)"),
                y=alt.Y("count():Q", title="Số sản phẩm"),
                tooltip=[alt.Tooltip("count():Q", title="Số sản phẩm")],
            ).properties(height=330)
            st.altair_chart(residuals, use_container_width=True)

    st.subheader("Ước tính cho một cấu hình sản phẩm")
    st.caption("Thay đổi các thuộc tính để xem mô hình ước tính số lượng bán tương ứng.")
    with st.form("forecast_input"):
        input_values = {}
        columns = st.columns(3)
        for index, feature in enumerate(numeric_features):
            values = pd.to_numeric(X[feature], errors="coerce").dropna()
            default = float(values.median()) if not values.empty else 0.0
            minimum = float(values.min()) if not values.empty else 0.0
            maximum = float(values.max()) if not values.empty else max(default, 1.0)
            if minimum == maximum:
                maximum = minimum + 1.0
            with columns[index % len(columns)]:
                input_values[feature] = st.number_input(
                    feature.replace("_", " ").title(),
                    min_value=minimum,
                    max_value=maximum,
                    value=min(max(default, minimum), maximum),
                )
        for index, feature in enumerate(categorical_features):
            options = sorted(X[feature].unique().tolist(), key=str)
            with columns[(index + len(numeric_features)) % len(columns)]:
                input_values[feature] = st.selectbox(
                    feature.replace("_", " ").title(), options,
                    format_func=lambda value: "Có" if value is True else "Không" if value is False else str(value),
                )
        submitted = st.form_submit_button("Ước tính")

    if submitted:
        input_frame = pd.DataFrame([input_values], columns=numeric_features + categorical_features)
        estimate = max(0, float(pipeline.predict(input_frame)[0]))
        st.metric("Số lượng bán ước tính", f"{estimate:,.0f}")

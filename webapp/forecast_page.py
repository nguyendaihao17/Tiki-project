import numpy as np
import pandas as pd
import streamlit as st
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


NUMERIC_CANDIDATES = ["price", "original_price", "discount_rate", "rating_average", "review_count"]
CATEGORICAL_CANDIDATES = ["category_name", "price_segment", "seller_type", "is_tiki_now", "is_freeship_xtra"]


def _build_model(df_products):
    if "quantity_sold" not in df_products.columns:
        return None, None, None, "Không có cột quantity_sold trong dữ liệu."

    numeric_features = [column for column in NUMERIC_CANDIDATES if column in df_products.columns]
    categorical_features = [column for column in CATEGORICAL_CANDIDATES if column in df_products.columns]
    if not numeric_features and not categorical_features:
        return None, None, None, "Không có đặc trưng phù hợp để huấn luyện mô hình."

    columns = numeric_features + categorical_features + ["quantity_sold"]
    data = df_products[columns].copy()
    data["quantity_sold"] = pd.to_numeric(data["quantity_sold"], errors="coerce")
    data = data.dropna(subset=["quantity_sold"])
    if len(data) < 50:
        return None, None, None, "Cần ít nhất 50 sản phẩm có số lượng bán để huấn luyện."

    for column in numeric_features:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    for column in categorical_features:
        data[column] = data[column].fillna("Không xác định").astype(str)

    transformers = []
    if numeric_features:
        numeric_pipeline = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]
        )
        transformers.append(("numeric", numeric_pipeline, numeric_features))
    if categorical_features:
        categorical_pipeline = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("onehot", OneHotEncoder(handle_unknown="ignore")),
            ]
        )
        transformers.append(("categorical", categorical_pipeline, categorical_features))

    pipeline = Pipeline(
        steps=[
            ("preprocessor", ColumnTransformer(transformers=transformers)),
            ("regressor", RandomForestRegressor(n_estimators=150, random_state=42, n_jobs=-1)),
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
    return pipeline, metrics, (numeric_features, categorical_features, X, y), None


def show(df_products):
    st.title("Dự báo số lượng bán")
    st.warning(
        "Dữ liệu hiện tại là ảnh chụp sản phẩm, không có chuỗi doanh số theo ngày/tháng. "
        "Mô hình bên dưới ước tính số lượng bán từ thuộc tính sản phẩm, không dự báo doanh số tương lai theo thời gian."
    )
    if df_products.empty:
        st.warning("Không có dữ liệu sản phẩm.")
        return

    with st.spinner("Đang huấn luyện và đánh giá mô hình..."):
        pipeline, metrics, details, error = _build_model(df_products)
    if error:
        st.info(error)
        return

    mae, rmse, r2 = st.columns(3)
    mae.metric("MAE", f"{metrics['MAE']:,.2f}")
    rmse.metric("RMSE", f"{metrics['RMSE']:,.2f}")
    r2.metric("R²", f"{metrics['R2']:.3f}")
    st.caption("Các chỉ số được tính trên tập kiểm tra giữ lại (20%), không phải số liệu tương lai.")

    numeric_features, categorical_features, X, y = details
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
            options = sorted(X[feature].dropna().astype(str).unique().tolist())
            if not options:
                options = ["Không xác định"]
            with columns[(index + len(numeric_features)) % len(columns)]:
                input_values[feature] = st.selectbox(feature.replace("_", " ").title(), options)
        submitted = st.form_submit_button("Ước tính")

    if submitted:
        input_frame = pd.DataFrame([input_values], columns=numeric_features + categorical_features)
        estimate = max(0, float(pipeline.predict(input_frame)[0]))
        st.metric("Số lượng bán ước tính", f"{estimate:,.0f}")

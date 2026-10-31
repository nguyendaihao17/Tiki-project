from datetime import timedelta

import pandas as pd
import numpy as np
import streamlit as st
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from src.database import get_clean_collection

PRODUCT_DATA_PROJECTION = {
    "_id": 0,
    "product_id": 1,
    "name": 1,
    "category_id": 1,
    "category_name": 1,
    "origin": 1,
    "price": 1,
    "original_price": 1,
    "discount": 1,
    "discount_rate": 1,
    "quantity_sold": 1,
    "historical_sold": 1,
    "rating_average": 1,
    "review_count": 1,
    "revenue_estimate": 1,
    "seller_id": 1,
    "seller_type": 1,
    "is_official_store": 1,
    "is_authentic": 1,
    "is_tiki_now": 1,
    "is_freeship_xtra": 1,
    "price_segment": 1,
}
REVIEW_DATA_PROJECTION = {
    "_id": 0,
    "review_id": 1,
    "customer_id": 1,
    "customer_name": 1,
    "product_id": 1,
    "rating": 1,
    "sentiment": 1,
    "created_at": 1,
    "title": 1,
}
DASHBOARD_REVIEW_PROJECTION = {
    "_id": 0,
    "review_id": 1,
    "customer_id": 1,
    "product_id": 1,
    "rating": 1,
    "created_at": 1,
}


@st.cache_data(ttl=300, show_spinner=False)
def load_products_data():
    products_collection = get_clean_collection("clean_products")
    categories_collection = get_clean_collection("clean_categories")
    if products_collection is None:
        return pd.DataFrame()

    df_products = pd.DataFrame(
        list(
            products_collection.find(
                {"is_deleted": {"$ne": True}},
                PRODUCT_DATA_PROJECTION,
            )
        )
    )
    if not df_products.empty and "category_id" in df_products.columns and categories_collection is not None:
        df_categories = pd.DataFrame(
            list(categories_collection.find({}, {"_id": 0, "category_id": 1, "category_name": 1}))
        )
        if {"category_id", "category_name"}.issubset(df_categories.columns):
            root_categories = dict(
                zip(
                    df_categories["category_id"].astype(str).str.replace(r"\.0$", "", regex=True),
                    df_categories["category_name"],
                )
            )
            product_category_ids = (
                df_products["category_id"].astype(str).str.replace(r"\.0$", "", regex=True)
            )
            df_products["root_category_name"] = product_category_ids.map(root_categories)
            if "category_name" in df_products.columns:
                df_products["root_category_name"] = df_products["root_category_name"].fillna(
                    df_products["category_name"]
                )
    
    if not df_products.empty:
        df_products['price'] = pd.to_numeric(
            df_products.get('price', pd.Series(0, index=df_products.index)),
            errors='coerce',
        ).fillna(0)
        df_products['quantity_sold'] = pd.to_numeric(
            df_products.get('quantity_sold', df_products.get('historical_sold', pd.Series(0, index=df_products.index))),
            errors='coerce',
        ).fillna(0)
        df_products['rating_average'] = pd.to_numeric(
            df_products.get('rating_average', pd.Series(0, index=df_products.index)),
            errors='coerce',
        ).fillna(0)
        df_products['discount_rate'] = pd.to_numeric(
            df_products.get('discount_rate', pd.Series(0, index=df_products.index)),
            errors='coerce',
        ).fillna(0)
        calculated_revenue = df_products['price'] * df_products['quantity_sold']
        if 'revenue_estimate' in df_products.columns:
            recorded_revenue = pd.to_numeric(df_products['revenue_estimate'], errors='coerce')
            df_products['estimated_revenue'] = recorded_revenue.fillna(calculated_revenue)
        else:
            df_products['estimated_revenue'] = calculated_revenue

    return df_products


@st.cache_data(ttl=300, show_spinner=False)
def load_reviews_data():
    reviews_collection = get_clean_collection("clean_reviews")
    if reviews_collection is None:
        return pd.DataFrame()
    return pd.DataFrame(
        list(reviews_collection.find({}, REVIEW_DATA_PROJECTION))
    )


@st.cache_data(ttl=300, show_spinner=False)
def load_dashboard_reviews_data():
    """Load only the review fields used by the dashboard and data-quality pages."""
    reviews_collection = get_clean_collection("clean_reviews")
    if reviews_collection is None:
        return pd.DataFrame()
    return pd.DataFrame(
        list(reviews_collection.find({}, DASHBOARD_REVIEW_PROJECTION))
    )


def load_analytics_data():
    """Load products and reviews using the cached collection loaders."""
    df_products = load_products_data()
    df_reviews = load_reviews_data()
    return df_products, df_reviews

def calculate_core_kpis(df_products, df_reviews):
    total_revenue = (
        pd.to_numeric(
            df_products.get("estimated_revenue", pd.Series(dtype=float)),
            errors="coerce",
        )
        .fillna(0)
        .sum()
    )
    total_products = len(df_products)
    total_reviews = len(df_reviews)
    rating = pd.to_numeric(
        df_products.get("rating_average", pd.Series(index=df_products.index, dtype=float)),
        errors="coerce",
    )
    avg_rating = rating[rating > 0].mean() if not df_products.empty else 0
    aov = total_revenue / total_products if total_products > 0 else 0
    
    # Product Risk Rate (Sản phẩm bán được nhưng rating <= 3.0)
    quantity = pd.to_numeric(
        df_products.get("quantity_sold", pd.Series(index=df_products.index, dtype=float)),
        errors="coerce",
    )
    risky_count = int((quantity.gt(0) & rating.gt(0) & rating.le(3.0)).sum())
    risk_rate = (risky_count / total_products * 100) if total_products > 0 else 0
    
    return {
        "Total Revenue": total_revenue,
        "Total Products": total_products,
        "Total Reviews": total_reviews,
        "Avg Rating": avg_rating,
        "AOV": aov,
        "Product Risk Rate": risk_rate
    }

def run_kmeans_rfm(df_products):
    """Mô hình học không giám sát: Phân cụm RFM nhà bán hàng"""
    if df_products.empty or 'seller_id' not in df_products.columns:
        return None, None
    
    snapshot_date = pd.to_datetime('2026-10-01') # Ngày mốc giả định tương ứng dataset
    if 'crawled_at' in df_products.columns:
        df_products['crawled_dt'] = pd.to_datetime(df_products['crawled_at'], errors='coerce')
        snapshot_date = df_products['crawled_dt'].max() + pd.to_datetime(timedelta(days=1)) if not df_products['crawled_dt'].isna().all() else snapshot_date

    rfm_df = df_products.groupby('seller_id').agg({
        'product_id': 'count',
        'estimated_revenue': 'sum'
    }).reset_index()
    
    rfm_df.rename(columns={'product_id': 'Frequency', 'estimated_revenue': 'Monetary'}, inplace=True)
    rfm_df['Recency'] = 1.0 # Giả lập Recency tiêu chuẩn
    
    X_rfm = rfm_df[['Recency', 'Frequency', 'Monetary']]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_rfm)
    
    kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
    rfm_df['Cluster'] = kmeans.fit_predict(X_scaled)
    
    return rfm_df, kmeans

def run_random_forest_regression(df_products):
    """Mô hình học có giám sát: Dự báo số lượng bán"""
    target = 'quantity_sold'
    num_features = ['price', 'original_price', 'discount', 'discount_rate', 'rating_average', 'review_count']
    cat_features = ['price_segment', 'seller_type', 'is_official_store', 'is_authentic', 'is_freeship_xtra']
    
    cols_needed = [target] + num_features + cat_features
    model_df = df_products[[c for c in cols_needed if c in df_products.columns]].dropna().copy()
    
    if len(model_df) < 50:
        return None, None, None
        
    X = model_df[num_features + [c for c in cat_features if c in model_df.columns]]
    y = model_df[target]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    numeric_transformer = StandardScaler()
    cat_cols_present = [c for c in cat_features if c in X.columns]
    categorical_transformer = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, num_features),
            ('cat', categorical_transformer, cat_cols_present)
        ]
    )
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    pipeline = Pipeline(steps=[('preprocessor', preprocessor), ('regressor', model)])
    
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)
    
    metrics = {
        "MAE": mean_absolute_error(y_test, y_pred),
        "RMSE": np.sqrt(mean_squared_error(y_test, y_pred)),
        "R2 Score": r2_score(y_test, y_pred)
    }
    return pipeline, metrics, (y_test, y_pred)

def run_isolation_forest(df_products):
    """Mô hình phát hiện bất thường: Isolation Forest (Contamination = 2%)"""
    features = ['price', 'discount_rate', 'quantity_sold', 'revenue_estimate', 'review_count']
    sub_df = df_products[[c for c in features if c in df_products.columns]].dropna()
    
    if sub_df.empty:
        return df_products
        
    iso = IsolationForest(contamination=0.02, random_state=42)
    preds = iso.fit_predict(sub_df[features])
    df_products['Outlier'] = ["Yes" if p == -1 else "No" for p in preds]
    return df_products

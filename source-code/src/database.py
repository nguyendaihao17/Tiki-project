import os
from pymongo import MongoClient
import streamlit as st

# Ưu tiên biến môi trường khi triển khai; secrets.toml chỉ dùng cục bộ.
MONGO_URI = os.environ.get("TIKI_MONGO_URI")
DB_NAME = "tikilens_vn"

CLEAN_COLLECTIONS = frozenset(
    {
        "clean_categories",
        "clean_causasent",
        "clean_causasent_before_dedup",
        "clean_products",
        "clean_reviews",
        "clean_reviews_quality",
        "clean_sellers",
    }
)

@st.cache_resource(ttl=60)
def get_db_connection():
    """Tạo kết nối Singleton đến MongoDB Atlas"""
    try:
        uri = MONGO_URI or st.secrets.get("mongo_uri")
    except FileNotFoundError:
        uri = None
    if not uri:
        st.error("Chưa cấu hình kết nối dữ liệu. Đặt TIKI_MONGO_URI hoặc mongo_uri trong .streamlit/secrets.toml.")
        return None
    try:
        client = MongoClient(
            uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=20000,
        )
        db = client[DB_NAME]
        # Ping thử kết nối
        client.admin.command('ping')
        return db
    except Exception:
        st.error("Không thể kết nối MongoDB. Kiểm tra cấu hình và kết nối mạng.")
        return None


def get_clean_collection(collection_name):
    """Lấy collection đã làm sạch; từ chối collection ngoài allowlist."""
    if collection_name not in CLEAN_COLLECTIONS:
        raise ValueError(f"Collection không được phép truy cập: {collection_name}")

    db = get_db_connection()
    if db is None:
        return None
    return db[collection_name]

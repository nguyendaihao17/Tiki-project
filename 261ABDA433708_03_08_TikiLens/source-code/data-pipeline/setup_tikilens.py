from pathlib import Path

from dotenv import dotenv_values
from pymongo import MongoClient

# Doc cau hinh MongoDB Atlas
config = dotenv_values(Path(__file__).resolve().parent / ".env")
uri = config.get("MONGO_URI")

if not uri:
    raise ValueError("Khong tim thay MONGO_URI")

# Ket noi Atlas
with MongoClient(uri, serverSelectionTimeoutMS=10000) as client:
    client.admin.command("ping")

    # Tao database cho do an
    db = client["tikilens_vn"]

    # Tao collection dau tien de luu san pham Tiki
    if "raw_products" not in db.list_collection_names():
        db.create_collection("raw_products")

    print("TAO DATABASE THANH CONG!")
    print("Database:", db.name)
    print("Collections:", db.list_collection_names())
    print("So san pham hien tai:", db["raw_products"].count_documents({}))


import csv
from pathlib import Path
from dotenv import dotenv_values
from pymongo import MongoClient, ReplaceOne

# 1. Duong dan file
folder = Path(__file__).resolve().parent
csv_file = folder / "tiki_categories.csv"

if not csv_file.exists():
    raise FileNotFoundError("Khong tim thay tiki_categories.csv")

# 2. Doc thong tin ket noi MongoDB Atlas
uri = dotenv_values(folder / ".env").get("MONGO_URI")

if not uri:
    raise ValueError("Khong tim thay MONGO_URI")

# 3. Doc du lieu danh muc
operations = []

with csv_file.open("r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)

    for stt, row in enumerate(reader, start=1):
        row["_source_file"] = csv_file.name
        row["_source_row"] = stt
        row["_source_url"] = (
            "https://github.com/phamkhoa18/tiki-data-analysis"
        )

        operations.append(
            ReplaceOne(
                {
                    "_source_file": csv_file.name,
                    "_source_row": stt
                },
                row,
                upsert=True
            )
        )

print("So danh muc doc tu CSV:", len(operations))

# 4. Ket noi va luu vao Atlas
with MongoClient(uri, serverSelectionTimeoutMS=10000) as client:
    client.admin.command("ping")

    db = client["tikilens_vn"]
    collection = db["raw_categories"]

    if operations:
        collection.bulk_write(operations, ordered=False)

    # 5. Thong ke ca 4 collections
    products = db["raw_products"].count_documents({})
    reviews = db["raw_reviews"].count_documents({})
    sellers = db["raw_sellers"].count_documents({})
    categories = db["raw_categories"].count_documents({})

    print("\nNHAP CATEGORIES THANH CONG!")
    print("Products:", products)
    print("Reviews:", reviews)
    print("Sellers:", sellers)
    print("Categories:", categories)
    print("TONG DOCUMENTS:", products + reviews + sellers + categories)

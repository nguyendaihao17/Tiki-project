
import csv
from pathlib import Path
from dotenv import dotenv_values
from pymongo import MongoClient, ReplaceOne

# 1. Duong dan
folder = Path(__file__).resolve().parent
csv_file = folder / "tiki_sellers.csv"

# 2. Kiem tra file
if not csv_file.exists():
    raise FileNotFoundError("Khong tim thay tiki_sellers.csv")

# 3. Doc ket noi MongoDB Atlas
config = dotenv_values(folder / ".env")
uri = config.get("MONGO_URI")

if not uri:
    raise ValueError("Khong tim thay MONGO_URI")

# 4. Doc CSV va chuan bi du lieu
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

print("So sellers doc tu CSV:", len(operations))

# 5. Luu vao MongoDB Atlas
with MongoClient(uri, serverSelectionTimeoutMS=10000) as client:
    client.admin.command("ping")

    db = client["tikilens_vn"]
    collection = db["raw_sellers"]

    if operations:
        collection.bulk_write(operations, ordered=False)

    # 6. Thong ke du lieu
    products = db["raw_products"].count_documents({})
    reviews = db["raw_reviews"].count_documents({})
    sellers = collection.count_documents({})

    print("\nNHAP SELLERS THANH CONG!")
    print("Products:", products)
    print("Reviews:", reviews)
    print("Sellers:", sellers)
    print("Tong documents:", products + reviews + sellers)

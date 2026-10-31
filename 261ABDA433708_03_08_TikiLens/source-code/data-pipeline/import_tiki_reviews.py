
import csv
from pathlib import Path
from dotenv import dotenv_values
from pymongo import MongoClient, ReplaceOne

# 1. Duong dan du lieu va cau hinh
folder = Path(__file__).resolve().parent
csv_file = folder / "tiki_reviews.csv"

config = dotenv_values(folder / ".env")
uri = config.get("MONGO_URI")

if not csv_file.exists():
    raise FileNotFoundError("Khong tim thay tiki_reviews.csv")

if not uri:
    raise ValueError("Khong tim thay MONGO_URI")

# 2. Ham luu tung lo du lieu
def save_batch(collection, operations):
    if operations:
        collection.bulk_write(operations, ordered=False)
        operations.clear()

# 3. Ket noi MongoDB Atlas
with MongoClient(uri, serverSelectionTimeoutMS=10000) as client:
    client.admin.command("ping")

    db = client["tikilens_vn"]
    collection = db["raw_reviews"]

    total_read = 0
    operations = []

    # 4. Doc file CSV
    with csv_file.open(
        "r", encoding="utf-8-sig", newline=""
    ) as f:

        reader = csv.DictReader(f)

        for row_number, row in enumerate(reader, start=1):
            row["_source_file"] = csv_file.name
            row["_source_row"] = row_number
            row["_source_url"] = (
                "https://github.com/"
                "phamkhoa18/tiki-data-analysis"
            )

            # Upsert de tranh trung khi chay lai
            operations.append(
                ReplaceOne(
                    {
                        "_source_file": csv_file.name,
                        "_source_row": row_number
                    },
                    row,
                    upsert=True
                )
            )

            total_read += 1

            # Luu theo lo 500 ban ghi
            if len(operations) >= 500:
                save_batch(collection, operations)
                print("Da xu ly:", total_read)

        # Luu lo cuoi
        save_batch(collection, operations)

    # 5. Kiem tra ket qua
    total_reviews = collection.count_documents({
        "_source_file": csv_file.name
    })

    total_products = db["raw_products"].count_documents({})

    print("\nNHAP REVIEWS THANH CONG!")
    print("Reviews da doc:", total_read)
    print("Reviews da luu:", total_reviews)
    print("Products:", total_products)
    print("Tong documents:", total_products + total_reviews)

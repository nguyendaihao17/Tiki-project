
import csv
from pathlib import Path
from dotenv import dotenv_values
from pymongo import MongoClient, ReplaceOne

# Duong dan file CSV da tai
csv_file = Path(
    Path(__file__).resolve().parent / "tiki_products_clean_full.csv"
)

# Doc cau hinh ket noi Atlas
config = dotenv_values(
    Path(__file__).resolve().parent / ".env"
)
uri = config.get("MONGO_URI")

if not csv_file.exists():
    raise FileNotFoundError("Khong tim thay file CSV!")

if not uri:
    raise ValueError("Khong tim thay MONGO_URI!")

# Doc du lieu CSV
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

print("Da doc", len(operations), "dong tu CSV")

# Luu vao MongoDB Atlas
with MongoClient(uri, serverSelectionTimeoutMS=10000) as client:
    client.admin.command("ping")

    db = client["tikilens_vn"]
    collection = db["raw_products"]

    if operations:
        collection.bulk_write(operations, ordered=False)

    total = collection.count_documents({
        "_source_file": csv_file.name
    })

    print("NHAP DU LIEU THANH CONG!")
    print("Database:", db.name)
    print("Collection:", collection.name)
    print("So san pham da luu:", total)

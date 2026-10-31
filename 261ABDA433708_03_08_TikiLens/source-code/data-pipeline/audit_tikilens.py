
from pathlib import Path
from dotenv import dotenv_values
from pymongo import MongoClient

folder = Path(__file__).resolve().parent
uri = dotenv_values(folder / ".env").get("MONGO_URI")

if not uri:
    raise ValueError("Khong tim thay MONGO_URI")

collections = [
    "raw_products",
    "raw_reviews",
    "raw_sellers",
    "raw_categories"
]

with MongoClient(uri, serverSelectionTimeoutMS=10000) as client:
    client.admin.command("ping")
    db = client["tikilens_vn"]

    tong = 0
    report = ["BAO CAO KIEM TRA DU LIEU TIKILENS VN", ""]

    for name in collections:
        col = db[name]
        count = col.count_documents({})
        sample = col.find_one({}, {"_id": 0})

        tong += count

        # Chi in ten truong, khong in thong tin khach hang
        fields = list(sample.keys()) if sample else []

        report.append(f"COLLECTION: {name}")
        report.append(f"So documents: {count}")
        report.append(f"So truong trong ban ghi mau: {len(fields)}")
        report.append("Danh sach truong:")

        for field in fields:
            report.append(f"  - {field}")

        report.append("")

    report.append(f"TONG DOCUMENTS: {tong}")

    output = folder / "audit_tikilens.txt"
    output.write_text(
        "\n".join(report),
        encoding="utf-8"
    )

    print("KIEM TRA THANH CONG!")
    print("Tong documents:", tong)
    print("Da tao file:", output)

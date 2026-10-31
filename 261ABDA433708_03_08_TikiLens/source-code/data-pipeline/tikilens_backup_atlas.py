# -*- coding: utf-8 -*-
r"""TIKILENS VN - Sao luu 5 collections MongoDB Atlas ve JSONL Extended JSON.

Chay: py tikilens_backup_atlas.py
Can: pymongo, python-dotenv. File .env co MONGO_URI nam cung thu muc script.
Chi doc MongoDB, khong sua hay xoa du lieu Atlas.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from bson import json_util
from dotenv import dotenv_values
from pymongo import MongoClient


DATABASE = "tikilens_vn"
COLLECTIONS = [
    "raw_products",
    "raw_reviews",
    "raw_sellers",
    "raw_categories",
    "raw_causasent_ate_v2",
]


def backup_collection(collection, output_path: Path):
    """Xuat BSON duoi dang MongoDB Extended JSON Lines, giu _id va kieu BSON."""
    digest = hashlib.sha256()
    written = 0

    # Ghi binary de ma SHA-256 luon khop chinh xac noi dung file.
    with output_path.open("wb") as output:
        cursor = collection.find({}, batch_size=500)
        try:
            for document in cursor:
                encoded = (
                    json_util.dumps(document, ensure_ascii=False, separators=(",", ":"))
                    + "\n"
                ).encode("utf-8")
                output.write(encoded)
                digest.update(encoded)
                written += 1
        finally:
            cursor.close()

    return written, digest.hexdigest()


def main():
    folder = Path(__file__).resolve().parent
    uri = dotenv_values(folder / ".env").get("MONGO_URI")
    if not uri:
        print("LOI: Khong tim thay MONGO_URI trong file .env cung thu muc.")
        return

    started_at = datetime.now(timezone.utc)
    timestamp = started_at.strftime("%Y%m%d_%H%M%S_%f")
    backup_dir = folder / "tikilens_backups" / f"backup_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=False)

    print("TIKILENS VN - SAO LUU MONGODB ATLAS")
    print("Che do: CHI DOC MongoDB; xuat ra file tren may tinh.")
    print("Khong chia se thu muc backup: du lieu co the chua thong tin khach hang.")

    manifest = {
        "format": "MongoDB Extended JSON Lines",
        "backup_method": "application_level_export_via_pymongo",
        "database": DATABASE,
        "created_at_utc": started_at.isoformat(),
        "complete": False,
        "collections": {},
        "total_documents": 0,
        "notes": [
            "Backup tung collection, khong phai snapshot nhat quan khi co ghi dong thoi.",
            "Can thu nghiem restore rieng truoc khi coi la backup da kiem chung.",
            "Khong bao gom index definitions, users/roles hay cau hinh cluster.",
            "File backup co the chua du lieu ca nhan; giu rieng tu va khong commit len GitHub.",
        ],
    }

    try:
        with MongoClient(uri, serverSelectionTimeoutMS=15000) as client:
            client.admin.command("ping")
            db = client[DATABASE]
            available = set(db.list_collection_names())
            missing = [name for name in COLLECTIONS if name not in available]
            if missing:
                raise RuntimeError("Thieu collection: " + ", ".join(missing))

            for name in COLLECTIONS:
                collection = db[name]
                expected = collection.count_documents({})
                file_name = name + ".jsonl"
                destination = backup_dir / file_name
                print(f"Dang sao luu {name}: {expected} documents...")

                count, sha256 = backup_collection(collection, destination)
                after = collection.count_documents({})
                if count != expected or count != after:
                    raise RuntimeError(
                        f"{name}: so luong thay doi khi backup: "
                        f"truoc={expected}, trong_file={count}, sau={after}. "
                        "Hay dung thao tac nhap du lieu va chay lai."
                    )

                manifest["collections"][name] = {
                    "filename": file_name,
                    "count": count,
                    "sha256": sha256,
                    "size_bytes": destination.stat().st_size,
                }
                manifest["total_documents"] += count
                print(f"  Da luu: {count} | SHA256: {sha256[:16]}...")

            manifest["complete"] = True
            manifest_path = backup_dir / "backup_manifest.json"
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
            )

            print("\nSAO LUU THANH CONG!")
            print("Database:", DATABASE)
            print("So collections:", len(manifest["collections"]))
            print("Tong documents:", manifest["total_documents"])
            print("Thu muc backup:", backup_dir)
            print("Manifest:", manifest_path)
            print("MongoDB Atlas: KHONG BI THAY DOI.")
            print("BUOC SAU: Thu nghiem khoi phuc vao collection/database rieng.")

    except Exception as exc:
        print("\nSAO LUU CHUA HOAN TAT!")
        print("Loai loi:", type(exc).__name__)
        # Khong in exception de tranh ro ri URI/password trong thong bao.
        print("Thu muc dang do:", backup_dir)
        print("Khong su dung ban sao luu nay cho restore.")


if __name__ == "__main__":
    main()

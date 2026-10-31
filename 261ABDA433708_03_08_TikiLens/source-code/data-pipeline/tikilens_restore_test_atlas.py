# -*- coding: utf-8 -*-
"""TIKILENS VN - Kiem thu khoi phuc MongoDB Atlas tu backup Extended JSONL.

Can: pymongo, python-dotenv (da cai o nhung buoc truoc).
Dat file nay trong thu muc script, cung thu muc .env va tikilens_backups.
Chay: py tikilens_restore_test_atlas.py

An toan:
- KHONG ghi vao database goc `tikilens_vn`.
- CHI ghi vao database test `tikilens_restore_test`.
- KHONG xoa database, collection, hay document.
- Kiem tra SHA-256 va so dong cua CA 5 file truoc khi ghi.
- Co the chay lai voi CUNG backup nhung khong nhan ban records.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from bson import json_util
from dotenv import dotenv_values
from pymongo import MongoClient, ReplaceOne

SOURCE_DB = "tikilens_vn"
TARGET_DB = "tikilens_restore_test"
EXPECTED_COLLECTIONS = (
    "raw_products",
    "raw_reviews",
    "raw_sellers",
    "raw_categories",
    "raw_causasent_ate_v2",
)
BATCH_SIZE = 300


def sha256_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    lines = 0
    with path.open("rb") as f:
        for chunk in f:
            digest.update(chunk)
            lines += 1
    return digest.hexdigest(), lines


def find_backup(root: Path) -> tuple[Path, dict, str]:
    candidates = []
    for folder in root.glob("backup_*"):
        manifest_path = folder / "backup_manifest.json"
        if folder.is_dir() and manifest_path.is_file():
            candidates.append(folder)
    candidates.sort(reverse=True)
    for folder in candidates:
        manifest_path = folder / "backup_manifest.json"
        try:
            data = manifest_path.read_bytes()
            manifest = json.loads(data.decode("utf-8"))
            if manifest.get("complete") is True and manifest.get("database") == SOURCE_DB:
                return folder, manifest, hashlib.sha256(data).hexdigest()
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
    raise RuntimeError("Khong tim thay backup hoan chinh cua tikilens_vn")


def validate_backup(folder: Path, manifest: dict) -> int:
    rows = manifest.get("collections", {})
    if set(rows) != set(EXPECTED_COLLECTIONS):
        raise ValueError("Danh sach collection trong manifest khong du 5 bo du lieu")

    total = 0
    for name in EXPECTED_COLLECTIONS:
        info = rows[name]
        # Chi cho phep ten file co dinh, khong tin duong dan ben ngoai manifest.
        expected_filename = name + ".jsonl"
        if info.get("filename") != expected_filename:
            raise ValueError("Ten file backup khong dung: " + name)
        path = folder / expected_filename
        if not path.is_file():
            raise FileNotFoundError("Thieu file backup: " + expected_filename)
        if path.stat().st_size != info.get("size_bytes"):
            raise ValueError("Sai kich thuoc file backup: " + name)
        digest, lines = sha256_file(path)
        if digest != info.get("sha256") or lines != info.get("count"):
            raise ValueError("Sai SHA-256 hoac so dong file backup: " + name)
        total += lines
        print(f"  OK {name}: {lines} documents; SHA-256 hop le")

    if total != manifest.get("total_documents"):
        raise ValueError("Tong so documents khong khop backup_manifest.json")
    return total


def batches_of_backup(path: Path):
    current = []
    first = None
    last = None
    with path.open("r", encoding="utf-8") as f:
        for number, line in enumerate(f, 1):
            document = json_util.loads(line)
            if not isinstance(document, dict) or "_id" not in document:
                raise ValueError(f"Document khong co _id tai dong {number}")
            if first is None:
                first = document
            last = document
            current.append(
                ReplaceOne({"_id": document["_id"]}, document, upsert=True)
            )
            if len(current) == BATCH_SIZE:
                yield current, first, last
                current = []
        if current:
            yield current, first, last


def main():
    script_dir = Path(__file__).resolve().parent
    uri = dotenv_values(script_dir / ".env").get("MONGO_URI")
    if not uri:
        print("LOI: Khong tim thay MONGO_URI trong file .env")
        return

    print("TIKILENS VN - KIEM THU RESTORE TOAN BO BACKUP")
    print("Database GOC :", SOURCE_DB, "(KHONG SUA)")
    print("Database TEST:", TARGET_DB, "(SE GHI DU LIEU)")
    print("Luu y: Restore tao ban sao du lieu tren Atlas va dung them dung luong.")

    try:
        folder, manifest, fingerprint = find_backup(script_dir / "tikilens_backups")
        print("Thu muc backup:", folder)
        print("Dang kiem tra SHA-256 va so dong tat ca file...")
        total_expected = validate_backup(folder, manifest)
        print("BACKUP HOP LE, tong:", total_expected)

        with MongoClient(uri, serverSelectionTimeoutMS=15000) as client:
            client.admin.command("ping")
            database_names = set(client.list_database_names())
            test_db = client[TARGET_DB]

            # An toan: khong su dung database test da ton tai neu khong co marker cua script.
            if TARGET_DB in database_names:
                marker = test_db["_restore_control"].find_one({"_id": "tikilens_restore"})
                if not marker or marker.get("manifest_sha256") != fingerprint:
                    raise RuntimeError(
                        "Database tikilens_restore_test da ton tai nhung khong khop ban sao luu nay. "
                        "Khong tu dong ghi de database do."
                    )
            else:
                test_db["_restore_control"].insert_one(
                    {"_id": "tikilens_restore", "manifest_sha256": fingerprint,
                     "backup_folder": folder.name, "source_database": SOURCE_DB}
                )

            report = [
                "TIKILENS VN - BIEN BAN KIEM THU KHOI PHUC",
                "Database goc: " + SOURCE_DB + " (khong thay doi)",
                "Database thu nghiem: " + TARGET_DB,
                "Thu muc backup: " + str(folder),
                "Manifest SHA-256: " + fingerprint,
                "Backup: DA KIEM TRA SHA-256 CA 5 FILE",
                "",
            ]
            restored_total = 0
            for name in EXPECTED_COLLECTIONS:
                path = folder / (name + ".jsonl")
                col = test_db[name]
                expected = manifest["collections"][name]["count"]
                first_doc = None
                last_doc = None
                processed = 0
                print(f"Dang khoi phuc {name}: {expected} documents...")
                for operations, first, last in batches_of_backup(path):
                    col.bulk_write(operations, ordered=False)
                    processed += len(operations)
                    if first_doc is None:
                        first_doc = first
                    last_doc = last
                    if processed % 3000 == 0 or processed == expected:
                        print(f"  Da ghi: {processed}/{expected}")

                actual = col.count_documents({})
                if processed != expected or actual != expected:
                    raise RuntimeError(f"Restore chua khop so luong: {name}")
                for sample in (first_doc, last_doc):
                    if sample is not None:
                        restored = col.find_one({"_id": sample["_id"]})
                        if restored != sample:
                            raise RuntimeError("Ban ghi mau khac backup o collection: " + name)
                report.append(f"{name}: backup={expected}, restore={actual}, mau BSON=KHOP")
                restored_total += actual
                print(f"  HOAN THANH: {actual} docs, kiem tra mau _id va BSON KHOP")

            if restored_total != total_expected:
                raise RuntimeError("Tong ban ghi restore khong khop")
            report.append("")
            report.append("TONG RESTORE: " + str(restored_total))
            report.append("KET LUAN: KHOI PHUC THU THANH CONG")
            report.append("Gioi han: chi backup documents; chua sao luu indexes, quyen, cau hinh Atlas.")
            receipt = folder / "restore_verification.txt"
            receipt.write_text("\n".join(report) + "\n", encoding="utf-8")
            print("\nKHOI PHUC THU THANH CONG!")
            print("Database TEST:", TARGET_DB)
            print("So collections du lieu:", len(EXPECTED_COLLECTIONS))
            print("Tong documents da khoi phuc:", restored_total)
            print("Bien ban:", receipt)
            print("Database goc tikilens_vn: KHONG BI THAY DOI.")
            print("Luu y: Chi xoa database TEST khi ban da luu minh chung va chu dong quyet dinh.")

    except Exception as exc:
        print("\nKHOI PHUC THU CHUA HOAN TAT!")
        print("Loai loi:", type(exc).__name__)
        # Tuyet doi khong in URI/password tu chuoi loi.
        print("Khong xoa hay sua database goc tikilens_vn.")
        print("Neu dung luong Atlas khong du, dung chay lai va bao minh biet.")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""TIKILENS VN - Nhap CausaSent ATE v2 vao collection RIENG tren MongoDB Atlas.

- Giu nguyen 4 collections Tiki: raw_products, raw_reviews, raw_sellers, raw_categories.
- Kiem tra tinh toan ven file nguon qua SHA-256 truoc khi ghi.
- Giu nguyen nhan khia canh va _dataset_split (train / val / test).
- Nhap theo lo, co the chay lai an toan nhờ _id on dinh.
- Khong hien thi URI, mat khau hoac noi dung danh gia.

Yeu cau: py -m pip install pymongo python-dotenv
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from dotenv import dotenv_values
from pymongo import MongoClient, ReplaceOne

ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "tikilens_source2"
DATA_FILE = SOURCE_DIR / "causasent_ate_v2.jsonl"
MANIFEST = SOURCE_DIR / "source_manifest.json"
ENV = ROOT / ".env"
RECEIPT = SOURCE_DIR / "atlas_import_receipt.txt"
DATASET = "Tamir39/causasent-ate-v2"
DATASET_URL = "https://huggingface.co/datasets/Tamir39/causasent-ate-v2"
COLLECTION_NAME = "raw_causasent_ate_v2"
EXPECTED_SPLITS = {"train": 5647, "val": 700, "test": 719}
BATCH_SIZE = 300


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validated_records():
    """Xac minh xong TOAN BO file truoc khi thay doi DB."""
    if not DATA_FILE.is_file():
        raise FileNotFoundError("Chua co tikilens_source2/causasent_ate_v2.jsonl")
    if not MANIFEST.is_file():
        raise FileNotFoundError("Chua co tikilens_source2/source_manifest.json")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))
    if manifest.get("dataset_id") != DATASET:
        raise ValueError("Manifest khong dung bo du lieu CausaSent.")
    actual_digest = sha256(DATA_FILE)
    if actual_digest != manifest.get("combined_sha256"):
        raise ValueError("SHA-256 file JSONL khong khop manifest, DUNG nhap va tai lai.")

    seen = set()
    rows = []
    split_counts = Counter()
    source_counts = Counter()
    with DATA_FILE.open("r", encoding="utf-8-sig") as f:
        for line_number, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as ex:
                raise ValueError(f"JSONL loi o dong {line_number}.") from ex
            if not isinstance(item, dict):
                raise ValueError(f"Dong {line_number} khong phai JSON object.")
            if any(k not in item for k in ("id", "source", "review", "annotations", "_dataset_split")):
                raise ValueError(f"Dong {line_number} thieu truong bat buoc.")
            rid = str(item["id"]).strip()
            if not rid or rid.lower() in {"none", "null", "nan"}:
                raise ValueError(f"ID trong o dong {line_number}.")
            if rid in seen:
                raise ValueError(f"Trung ID noi bo trong file o dong {line_number}.")
            if "_id" in item:
                raise ValueError(f"Dong {line_number} co san truong _id cua MongoDB.")
            seen.add(rid)
            split = str(item["_dataset_split"]).strip()
            if split not in EXPECTED_SPLITS:
                raise ValueError(f"Split khong hop le o dong {line_number}: {split}")
            if not isinstance(item["annotations"], list):
                raise ValueError(f"annotations khong phai danh sach o dong {line_number}.")
            split_counts[split] += 1
            source_counts[str(item["source"])] += 1

            # _id gan theo namespace de khong trung voi raw_reviews (Tiki).
            item["_id"] = f"causasent-v2:{rid}"
            item["_source_repository"] = DATASET_URL
            item["_source_file"] = DATA_FILE.name
            item["_source_row"] = line_number
            # Giu _dataset_split do downloader da luu tu ba file JSON goc.
            rows.append(item)

    if dict(split_counts) != EXPECTED_SPLITS:
        raise ValueError(f"So dong theo split sai: {dict(split_counts)}, dung nhap.")
    if len(rows) != 7066:
        raise ValueError(f"Phai co 7066 reviews, hien co {len(rows)}.")
    if manifest.get("split_counts") != EXPECTED_SPLITS:
        raise ValueError("Split trong manifest khong trung voi bo da tai.")
    if manifest.get("source_counts") != dict(source_counts):
        raise ValueError("Source counts khac manifest, dung nhap.")
    return rows, split_counts, source_counts, actual_digest


def main() -> int:
    print("TIKILENS VN - NHAP NGUON CAUSASENT VAO COLLECTION RIENG")
    print("Giu nguyen raw_reviews va 3 collections Tiki con lai.")
    try:
        rows, splits, sources, digest = validated_records()
        print("Da xac minh JSONL va manifest bang SHA-256.")
        print("Tong ban ghi:", len(rows))
        print("Split:", dict(splits))
        print("Nguon:", dict(sources))
        uri = dotenv_values(ENV).get("MONGO_URI")
        if not uri:
            raise ValueError("Khong tim thay MONGO_URI trong file .env")

        with MongoClient(uri, serverSelectionTimeoutMS=12000) as client:
            client.admin.command("ping")
            db = client["tikilens_vn"]
            before_reviews = db["raw_reviews"].count_documents({})
            col = db[COLLECTION_NAME]
            before = col.count_documents({})

            now_utc = datetime.now(timezone.utc).isoformat()
            for start in range(0, len(rows), BATCH_SIZE):
                chunk = rows[start:start + BATCH_SIZE]
                operations = []
                for obj in chunk:
                    doc = dict(obj)
                    doc["_imported_at_utc"] = now_utc
                    operations.append(ReplaceOne({"_id": doc["_id"]}, doc, upsert=True))
                col.bulk_write(operations, ordered=False)
                print("Da nhap:", min(start + len(chunk), len(rows)))

            col.create_index("_dataset_split")
            col.create_index("source")
            after = col.count_documents({})
            after_reviews = db["raw_reviews"].count_documents({})
            if after_reviews != before_reviews:
                raise RuntimeError("raw_reviews thay doi trong khi dang nhap; can kiem tra.")
            if after < len(rows):
                raise RuntimeError("Collection CausaSent thieu ban ghi sau khi nhap.")

        lines = [
            "TIKILENS VN - PHIEU XAC NHAN NHAP NGUON 2 VAO MONGODB ATLAS",
            f"Thoi diem UTC: {now_utc}",
            "Database: tikilens_vn",
            f"Collection: {COLLECTION_NAME}",
            f"Nguon: {DATASET_URL}",
            f"SHA256 JSONL: {digest}",
            f"So ban ghi dau vao: {len(rows)}",
            f"Phan chia nguon: {dict(sources)}",
            f"Phan chia train/val/test: {dict(splits)}",
            f"So ban ghi CausaSent truoc nhap: {before}",
            f"So ban ghi CausaSent sau nhap: {after}",
            f"raw_reviews Tiki truoc/sau: {before_reviews}/{after_reviews}",
            "Luu y: Hai bo du lieu co giao nhau va khong chung minh hai san TMDT doc lap.",
            "Khong gop CausaSent vao raw_reviews; giu nguyen train/val/test.",
        ]
        RECEIPT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("\nNHAP NGUON 2 THANH CONG!")
        print("Collection:", COLLECTION_NAME)
        print("So documents CausaSent:", after)
        print("raw_reviews Tiki van la:", after_reviews)
        print("Bien ban:", RECEIPT)
        return 0
    except Exception as exc:
        print("\nCHUA HOAN THANH BUOC NHAP.")
        print("Loai loi:", type(exc).__name__)
        # Chi tiet tu loi du lieu local la an toan; khong in thong bao loi MongoDB.
        if isinstance(exc, (ValueError, FileNotFoundError, RuntimeError)):
            print("Chi tiet:", str(exc))
        print("Neu gap loi, gui thong bao tren; khong gui URI hoac mat khau.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

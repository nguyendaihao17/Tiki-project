"""TIKILENS VN - tai mot bo du lieu nghien cuu thu cap tu Hugging Face.

Nguon: Tamir39/causasent-ate-v2 (CC BY-SA 4.0 theo dataset card).
Thao tac: GET API cong khai, ghi JSONL va metadata. Khong can MongoDB,
khong thay doi raw_* collections, khong gui mat khau/URI.

Ghi chu: Du lieu co the trung review voi nguon Tiki da co; KHONG duoc
cong cong vao so review doc lap truoc khi kiem tra trung lap.
"""

import hashlib
import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    print("THIEU THU VIEN: Chay lenh py -m pip install requests")
    sys.exit(1)

DATASET_ID = "Tamir39/causasent-ate-v2"
DATASET_URL = "https://huggingface.co/datasets/Tamir39/causasent-ate-v2"
API = "https://datasets-server.huggingface.co/rows"
OUTPUT_DIR = Path(__file__).resolve().parent / "tikilens_source2"
OUTPUT_FILE = OUTPUT_DIR / "causasent_ate_v2.jsonl"
MANIFEST_FILE = OUTPUT_DIR / "source_manifest.json"
SPLITS = ("train", "val", "test")
PAGE_SIZE = 100


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # Ghi file tam truoc, khong thay the du lieu cu neu tai that bai.
    tmp_file = OUTPUT_DIR / "causasent_ate_v2.jsonl.part"
    session = requests.Session()
    retry = Retry(
        total=5, connect=5, read=5, backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"], respect_retry_after_header=True,
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    counts = Counter()
    source_counts = Counter()
    ids = set()

    print("DANG TAI NGUON 2:", DATASET_URL)
    print("Khong ket noi va khong sua du lieu MongoDB.")

    try:
        with tmp_file.open("w", encoding="utf-8", newline="\n") as out:
            for split in SPLITS:
                offset = 0
                total = None
                while total is None or offset < total:
                    params = dict(
                        dataset=DATASET_ID,
                        config="default",
                        split=split,
                        offset=offset,
                        length=PAGE_SIZE,
                    )
                    response = session.get(API, params=params, timeout=35)
                    response.raise_for_status()
                    payload = response.json()
                    rows = payload.get("rows", [])
                    total = payload.get("num_rows_total")
                    if not isinstance(total, int):
                        raise ValueError("API khong tra so dong cua split " + split)
                    if not rows and offset < total:
                        raise ValueError("API tra ve trang rong bat thuong tai " + split)

                    for item in rows:
                        record = item.get("row", {})
                        if not isinstance(record, dict):
                            raise ValueError("Ban ghi khong hop le tai " + split)
                        for key in ("id", "source", "review", "annotations"):
                            if key not in record:
                                raise ValueError("Thieu truong " + key + " tai " + split)
                        record_id = str(record["id"])
                        if record_id in ids:
                            raise ValueError("Ma ID trung giua splits: " + record_id)
                        ids.add(record_id)
                        doc = dict(record)
                        doc["_dataset_split"] = split
                        doc["_dataset_id"] = DATASET_ID
                        out.write(json.dumps(doc, ensure_ascii=False) + "\n")
                        counts[split] += 1
                        source_counts[str(record.get("source", ""))] += 1

                    offset += len(rows)
                    if offset > total:
                        raise ValueError("API tra ve qua so dong du kien cho " + split)
                    if offset % 1000 < PAGE_SIZE or offset == total:
                        print(f"  {split}: {offset}/{total}")
                    time.sleep(0.05)

        sha256 = hashlib.sha256()
        with tmp_file.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                sha256.update(chunk)

        # Chi tao manifest khi tai du cac split thanh cong.
        manifest = {
            "dataset_id": DATASET_ID,
            "dataset_url": DATASET_URL,
            "api_endpoint": API,
            "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
            "license_as_declared_by_publisher": "CC-BY-SA-4.0",
            "attribution": "Tamir39/causasent-ate-v2; original CausaSent project",
            "split_counts": dict(counts),
            "source_counts": dict(source_counts),
            "total_rows": sum(counts.values()),
            "file_name": OUTPUT_FILE.name,
            "sha256": sha256.hexdigest(),
            "cautions": [
                "Secondary published dataset, not original scraping by this project.",
                "Tiki-origin reviews may overlap existing raw_reviews.",
                "Gold and silver annotation quality differs; verify before ML.",
                "Keep train/val/test splits separate to avoid evaluation leakage.",
                "Check terms and attribution before redistributing.",
            ],
        }
        tmp_file.replace(OUTPUT_FILE)
        MANIFEST_FILE.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print("\nTAI NGUON 2 THANH CONG!")
        print("Tong ban ghi:", sum(counts.values()))
        print("Theo split:", dict(counts))
        print("Theo nguon goc:", dict(source_counts))
        print("File JSONL:", OUTPUT_FILE)
        print("Bao cao nguon:", MANIFEST_FILE)
        print("CHUA NHAP MONGODB; KHONG THAY DOI DU LIEU GOC.")
    except (requests.RequestException, ValueError, KeyError, OSError) as e:
        print("\nTAI DU LIEU THAT BAI, CHUA HOAN TAT.")
        print("Loai loi:", type(e).__name__)
        print("Thong bao:", str(e)[:400])
        print("Da giu nguyen du lieu MongoDB va file tai hoan chinh truoc do.")
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()

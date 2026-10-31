"""TIKILENS VN - Thu thap lai du lieu tham khao Tiki tu GitHub.

Day la chuong trinh tai lai cac CSV CONG KHAI do ben thu ba phat hanh,
KHONG phai crawler truc tiep tu website/API Tiki.
Khong truy cap hoac thay doi MongoDB Atlas.

Yeu cau: py -m pip install requests
Chay: py tikilens_thu_thap_tiki_github.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "tikilens_acquisition"
BASE = "https://raw.githubusercontent.com/phamkhoa18/tiki-data-analysis/main/"
REPO = "https://github.com/phamkhoa18/tiki-data-analysis"
FILES = {
    "tiki_products_clean_full.csv": "dataset/tiki_products_clean_full.csv",
    "tiki_reviews.csv": "dataset/raw/tiki_reviews.csv",
    "tiki_sellers.csv": "dataset/raw/tiki_sellers.csv",
    "tiki_categories.csv": "dataset/raw/tiki_categories.csv",
}


def download_csv(session: requests.Session, url: str, destination: Path) -> dict:
    temp = destination.with_name(destination.name + ".part")
    for attempt in range(1, 4):
        try:
            with session.get(url, stream=True, timeout=(15, 120)) as response:
                if response.status_code == 404:
                    raise RuntimeError("Nguon khong ton tai (HTTP 404): " + url)
                if response.status_code in (429, 500, 502, 503, 504):
                    raise requests.HTTPError(f"HTTP {response.status_code}")
                response.raise_for_status()
                headers = {
                    "etag": response.headers.get("ETag"),
                    "last_modified": response.headers.get("Last-Modified"),
                }
                with temp.open("wb") as f:
                    for chunk in response.iter_content(chunk_size=1024 * 256):
                        if chunk:
                            f.write(chunk)
                temp.replace(destination)
                return headers
        except (requests.RequestException, OSError) as exc:
            if temp.exists():
                temp.unlink()
            if attempt == 3:
                raise RuntimeError(f"Tai that bai sau 3 lan: {url} ({type(exc).__name__})") from exc
            delay = attempt * 5
            print(f"  Loi mang {type(exc).__name__}. Cho {delay} giay de thu lai...", flush=True)
            time.sleep(delay)
    raise RuntimeError("Khong the tai file")


def describe_csv(path: Path) -> dict:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    # Some product descriptions can be long.
    csv.field_size_limit(10_000_000)
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header:
            raise RuntimeError("File CSV rong: " + path.name)
        n_rows = sum(1 for _ in reader)
    return {
        "sha256": digest.hexdigest(),
        "bytes": path.stat().st_size,
        "data_rows": n_rows,
        "column_count": len(header),
        "columns": header,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    manifest = {
        "project": "TIKILENS VN",
        "retrieved_at_utc": now,
        "publisher_repository": REPO,
        "acquisition_method": "Download CSV files from a third-party public GitHub repository via HTTPS",
        "not_a_tiki_web_crawler": True,
        "independent_original_sources_claimed": 1,
        "license_and_redistribution": "Verify upstream rights before public redistribution",
        "privacy": "Reviews may contain personal information. Do not publish raw files.",
        "files": [],
    }
    session = requests.Session()
    session.headers.update({"User-Agent": "TIKILENS-VN-Education-Source-Audit/1.0"})
    print("TIKILENS - CHUONG TRINH THU THAP LAI CSV TU GITHUB")
    print("Khong thu thap truc tiep tu Tiki, khong truy cap MongoDB.")
    try:
        for filename, relative_path in FILES.items():
            url = BASE + relative_path
            destination = OUT_DIR / filename
            print(f"Dang tai {filename}...", flush=True)
            headers = download_csv(session, url, destination)
            metrics = describe_csv(destination)
            info = {"filename": filename, "source_url": url, **headers, **metrics}
            manifest["files"].append(info)
            print(
                f"  OK: {metrics['data_rows']} dong | "
                f"{metrics['column_count']} cot | SHA-256 {metrics['sha256'][:16]}...",
                flush=True,
            )
    finally:
        session.close()
    total = sum(x["data_rows"] for x in manifest["files"])
    manifest["total_rows_across_csv"] = total
    manifest_file = OUT_DIR / "acquisition_manifest.json"
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nTHU THAP LAI THANH CONG!")
    print("So file:", len(manifest["files"]))
    print("Tong dong du lieu:", total)
    print("Thu muc:", OUT_DIR)
    print("Manifest:", manifest_file)
    print("MongoDB Atlas: KHONG BI THAY DOI.")
    print("LUU Y: Day la 1 nguon repository; KHONG chung minh da crawl truc tiep Tiki.")
    print("LUU Y: Khong chia se file raw reviews co thong tin ca nhan.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("\nTHU THAP CHUA HOAN TAT!")
        print("Loai loi:", type(exc).__name__)
        print("Chi tiet:", exc)
        print("Khong co thay doi nao tren MongoDB Atlas.")
        sys.exit(1)

# -*- coding: utf-8 -*-
"""TIKILENS VN - kiem tra giao nhau giua CausaSent ATE v2 va reviews Tiki.
Chi doc MongoDB Atlas; KHONG them, sua hay xoa documents.
Khong in noi dung review, thong tin khach hang hay chuoi ket noi.
"""

import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

from dotenv import dotenv_values
from pymongo import MongoClient

FOLDER = Path(__file__).resolve().parent
SOURCE2 = FOLDER / "tikilens_source2" / "causasent_ate_v2.jsonl"
REPORT = FOLDER / "tikilens_source2" / "source2_overlap_report.txt"


def norm(value):
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value)).casefold()
    text = re.sub(r"\s+", " ", text).strip()
    if text in {"", "nan", "none", "null", "n/a", "-"}:
        return ""
    return text


def digest(value):
    value = norm(value)
    return hashlib.sha256(value.encode("utf-8")).hexdigest() if value else ""


def valid_text_hash(value):
    value = norm(value)
    # Loai bo tieu de qua ngan / chung chung kho xac dinh la trung review.
    return hashlib.sha256(value.encode("utf-8")).hexdigest() if len(value) >= 20 else ""


def main():
    if not SOURCE2.is_file():
        raise FileNotFoundError(f"Chua thay file nguon 2: {SOURCE2}")

    uri = dotenv_values(FOLDER / ".env").get("MONGO_URI")
    if not uri:
        raise ValueError("Khong tim thay MONGO_URI trong .env")

    print("Dang doc bo du lieu CausaSent... (khong in noi dung review)")
    source_data = []
    source_counts = Counter()
    split_counts = Counter()
    id_counts = Counter()
    text_counts = Counter()
    annotation_counts = Counter()
    missing_text = 0
    missing_id = 0
    bad_span = 0
    malformed_annotation = 0

    with SOURCE2.open("r", encoding="utf-8-sig") as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"JSON khong hop le tai dong {line_num}: {e}") from e
            if not isinstance(obj, dict):
                raise ValueError(f"Dong {line_num} khong phai JSON object")
            if isinstance(obj.get("data"), dict) and "review" not in obj:
                obj = {**obj["data"], "split": obj.get("split", "")}

            sid = norm(obj.get("id"))
            origin = norm(obj.get("source")) or "unknown"
            review = obj.get("review", "")
            text_hash = digest(review)
            split = norm(obj.get("split"))
            annotations = obj.get("annotations", [])

            source_counts[origin] += 1
            if split:
                split_counts[split] += 1
            if sid:
                id_counts[sid] += 1
            else:
                missing_id += 1
            if text_hash:
                text_counts[text_hash] += 1
            else:
                missing_text += 1

            if isinstance(annotations, list):
                for item in annotations:
                    if not isinstance(item, dict):
                        malformed_annotation += 1
                        continue
                    annotation_counts[norm(item.get("sentiment")) or "unknown"] += 1
                    span = item.get("aspect_term_span")
                    term = item.get("aspect_term")
                    if (
                        not isinstance(span, list)
                        or len(span) != 2
                        or not all(isinstance(x, int) for x in span)
                        or span[0] < 0
                        or span[1] < span[0]
                        or not isinstance(review, str)
                        or review[span[0] : span[1]] != term
                    ):
                        bad_span += 1
            else:
                malformed_annotation += 1

            source_data.append((sid, origin, valid_text_hash(review), split))

    print("Dang doi chieu voi raw_reviews tren Atlas (chi doc)...")
    mongo_ids = set()
    content_hashes = set()
    title_hashes = set()
    with MongoClient(uri, serverSelectionTimeoutMS=12000) as client:
        client.admin.command("ping")
        cursor = client["tikilens_vn"]["raw_reviews"].find(
            {}, {"_id": 0, "review_id": 1, "content": 1, "title": 1}, batch_size=1000
        )
        mongo_rows = 0
        for row in cursor:
            mongo_rows += 1
            rid = norm(row.get("review_id"))
            if rid:
                mongo_ids.add(rid)
            hc = valid_text_hash(row.get("content"))
            ht = valid_text_hash(row.get("title"))
            if hc:
                content_hashes.add(hc)
            if ht:
                title_hashes.add(ht)

    match_id = match_content = match_title = match_any_text = 0
    match_by_source = Counter()
    for sid, origin, h, split in source_data:
        if origin == "tiki" and sid:
            candidates = {sid}
            if sid.startswith("tiki-"):
                candidates.add(sid[5:])
            if any(item in mongo_ids for item in candidates):
                match_id += 1
        in_content = bool(h and h in content_hashes)
        in_title = bool(h and h in title_hashes)
        if in_content:
            match_content += 1
        if in_title:
            match_title += 1
        if in_content or in_title:
            match_any_text += 1
            match_by_source[origin] += 1

    duplicated_ids = sum(v - 1 for v in id_counts.values() if v > 1)
    duplicated_text = sum(v - 1 for v in text_counts.values() if v > 1)

    lines = [
        "TIKILENS VN - KIEM TRA TRUNG LAP VA NGUON GOC CAUSASENT",
        "CHE DO: CHI DOC MONGODB; KHONG GHI, SUA, XOA DU LIEU",
        "",
        "I. THONG KE NGUON 2",
        f"Tong so dong: {len(source_data)}",
        f"Theo source: {dict(sorted(source_counts.items()))}",
        f"Theo split (neu JSONL co truong split): {dict(sorted(split_counts.items()))}",
        f"Thieu id: {missing_id}; thieu review: {missing_text}",
        f"Ban ghi co id trung (ngoai ban dau): {duplicated_ids}",
        f"Ban ghi co text trung chinh xac sau chuan hoa (ngoai ban dau): {duplicated_text}",
        f"Tong annotations theo nhan: {dict(sorted(annotation_counts.items()))}",
        f"Annotations sai aspect_term_span: {bad_span}; annotation khong hop le: {malformed_annotation}",
        "",
        "II. DOI CHIEU VOI raw_reviews HIEN CO",
        f"So raw_reviews tren Atlas: {mongo_rows}",
        f"CausaSent 'tiki' co review id khop voi raw_reviews: {match_id}",
        f"CausaSent review co van ban khop CHINH XAC content raw_reviews: {match_content}",
        f"CausaSent review co van ban khop CHINH XAC title raw_reviews: {match_title}",
        f"Tong review khop text (content HOAC title): {match_any_text}",
        f"Trong so trung text, phan bo theo source: {dict(sorted(match_by_source.items()))}",
        "",
        "III. GIOI HAN VA KHUYEN NGHI",
        "- So sanh van ban chi theo NFKC, viet thuong, bo khoang trang du; khong bat duoc cau viet lai.",
        "- Chi doi chieu van ban dai tu 20 ky tu de giam khop nham cac tieu de qua ngan.",
        "- Khop van ban khong chung minh cung nguoi mua; khong khop khong chung minh doc lap.",
        "- 'gold' cua CausaSent co ca hotel, nha hang, dien thoai; khong tu dong gop vao san pham Tiki.",
        "- 5.934 dong 'tiki' cua CausaSent van co nguon goc Tiki; bo nay khong chung minh 2 san TMDT doc lap.",
        "- Neu dung du lieu CausaSent cho NLP, giu nguyen split train/val/test, tranh ro ri du lieu.",
        "- Luu raw_reviews nguyen trang; khong tu dong gop/xoa ban ghi trung.",
        "",
        "Nguon: https://huggingface.co/datasets/Tamir39/causasent-ate-v2",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("KIEM TRA NGUON 2 THANH CONG!")
    print("Tong nguon 2:", len(source_data))
    print("Trung review ID voi Tiki:", match_id)
    print("Trung van ban (content hoac title):", match_any_text)
    print("Bao cao:", REPORT)
    print("MongoDB: KHONG BI THAY DOI")


if __name__ == "__main__":
    main()

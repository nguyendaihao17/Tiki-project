"""TIKILENS VN - kiem tra chat luong 4 collection trong MongoDB Atlas.

Cach chay (Windows CMD):
    py kiem_tra_chat_luong_tikilens.py

Dat file .env co bien MONGO_URI trong cung thu muc voi file nay.
Chuong trinh CHI DOC du lieu MongoDB, KHONG chinh sua / xoa documents.
Bao cao luu tai tikilens_quality_report.txt trong cung thu muc.
"""

from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

from dotenv import dotenv_values
from pymongo import MongoClient


BASE = Path(__file__).resolve().parent
REPORT_FILE = BASE / "tikilens_quality_report.txt"
DB_NAME = "tikilens_vn"

# Chi lay cac truong phuc vu audit. Khong lay thong tin dinh danh khach hang.
FIELDS = {
    "raw_products": [
        "product_id", "name", "sku", "category_id", "category_name",
        "seller_id", "seller_name", "price", "original_price",
        "discount_rate", "quantity_sold", "revenue_estimate",
        "rating_average", "review_count", "crawled_at", "_source_file",
    ],
    "raw_reviews": [
        "review_id", "product_id", "seller_id", "rating", "content",
        "sentiment", "created_at", "crawled_at", "_source_file",
    ],
    "raw_sellers": [
        "seller_id", "seller_name", "total_products", "avg_rating",
        "total_reviews", "_source_file",
    ],
    "raw_categories": [
        "category_id", "category_name", "parent_id", "level",
        "total_products", "crawled_at", "_source_file",
    ],
}

KEYS = {
    "raw_products": "product_id",
    "raw_reviews": "review_id",
    "raw_sellers": "seller_id",
    "raw_categories": "category_id",
}

NUMERIC = {
    "raw_products": [
        "price", "original_price", "discount_rate", "quantity_sold",
        "revenue_estimate", "rating_average", "review_count",
    ],
    "raw_reviews": ["rating"],
    "raw_sellers": ["total_products", "avg_rating", "total_reviews"],
    "raw_categories": ["level", "total_products"],
}

MISSING_VALUES = {"", "null", "none", "nan", "n/a", "-"}


def missing(value):
    return value is None or (
        isinstance(value, str) and value.strip().lower() in MISSING_VALUES
    )


def normalized_key(value):
    if missing(value):
        return None
    return str(value).strip()


def can_parse_number(value):
    if missing(value) or isinstance(value, bool):
        return False
    try:
        n = Decimal(str(value).strip().replace(",", ""))
        return n.is_finite()
    except (InvalidOperation, ValueError):
        return False


def collect_data(db):
    stats = {}
    ids = {}
    references = {
        "reviews_to_products": Counter(),
        "reviews_to_sellers": Counter(),
        "products_to_sellers": Counter(),
        "products_to_categories": Counter(),
    }

    for name, fields in FIELDS.items():
        print("Dang kiem tra:", name, flush=True)
        key_name = KEYS[name]
        field_missing = Counter()
        key_counter = Counter()
        source_files = Counter()
        numeric_summary = {
            f: Counter() for f in NUMERIC.get(name, [])
        }
        documents = 0

        projection = {f: 1 for f in fields}
        projection["_id"] = 0

        for row in db[name].find({}, projection, batch_size=500):
            documents += 1

            for f in fields:
                if missing(row.get(f)):
                    field_missing[f] += 1

            key = normalized_key(row.get(key_name))
            if key is not None:
                key_counter[key] += 1

            source_name = normalized_key(row.get("_source_file"))
            source_files[source_name or "(missing)"] += 1

            for f in numeric_summary:
                v = row.get(f)
                if missing(v):
                    numeric_summary[f]["missing"] += 1
                elif isinstance(v, str):
                    if can_parse_number(v):
                        numeric_summary[f]["text_numeric"] += 1
                    else:
                        numeric_summary[f]["invalid_text"] += 1
                elif can_parse_number(v):
                    numeric_summary[f]["numeric_type"] += 1
                else:
                    numeric_summary[f]["other_type"] += 1

            if name == "raw_reviews":
                p = normalized_key(row.get("product_id"))
                s = normalized_key(row.get("seller_id"))
                references["reviews_to_products"][p] += 1
                references["reviews_to_sellers"][s] += 1
            elif name == "raw_products":
                s = normalized_key(row.get("seller_id"))
                cat = normalized_key(row.get("category_id"))
                references["products_to_sellers"][s] += 1
                references["products_to_categories"][cat] += 1

        duplicates = sum(n - 1 for n in key_counter.values() if n > 1)
        repeated_keys = sum(1 for n in key_counter.values() if n > 1)
        stats[name] = {
            "documents": documents,
            "field_missing": field_missing,
            "key_missing": field_missing[key_name],
            "duplicate_extra": duplicates,
            "repeated_keys": repeated_keys,
            "sources": source_files,
            "numeric_summary": numeric_summary,
        }
        ids[name] = set(key_counter)

    return stats, ids, references


def describe_links(ref_counts, target_keys):
    total = sum(ref_counts.values())
    blank = ref_counts.get(None, 0)
    matched = sum(count for k, count in ref_counts.items()
                  if k is not None and k in target_keys)
    unmatched = total - blank - matched
    percentage = (100 * matched / (total - blank)) if (total - blank) else 0
    return total, blank, matched, unmatched, percentage


def make_report(stats, ids, references):
    lines = [
        "TIKILENS VN - BAO CAO KIEM TRA CHAT LUONG DU LIEU",
        "Database: tikilens_vn | Che do: CHI DOC",
        "Phuong phap: quet cac truong quan trong trong tung collection.",
        "Luu y: cac ban ghi dau vao la CSV; kieu chuoi co the can chuan hoa.",
        "",
        "I. SO LUONG, MA THIEU, MA TRUNG",
    ]
    total = 0
    for name, s in stats.items():
        total += s["documents"]
        lines.append(
            f"{name}: {s['documents']} documents; "
            f"thieu {KEYS[name]}: {s['key_missing']}; "
            f"ban ghi trung ma (ngoai ban ghi dau): {s['duplicate_extra']}; "
            f"so ma bi lap: {s['repeated_keys']}"
        )
    lines.append(f"TONG DOCUMENTS: {total}")

    lines.extend(["", "II. GIA TRI THIEU O CAC TRUONG DUOC KIEM TRA"])
    for name, s in stats.items():
        lines.append(f"[{name}]")
        for field in FIELDS[name]:
            n = s["field_missing"][field]
            pct = 100 * n / s["documents"] if s["documents"] else 0
            lines.append(f"  {field}: {n}/{s['documents']} ({pct:.2f}%)")

    lines.extend(["", "III. LIEN KET GIUA CAC COLLECTION"])
    checks = [
        ("raw_reviews.product_id => raw_products.product_id",
         "reviews_to_products", "raw_products"),
        ("raw_reviews.seller_id => raw_sellers.seller_id",
         "reviews_to_sellers", "raw_sellers"),
        ("raw_products.seller_id => raw_sellers.seller_id",
         "products_to_sellers", "raw_sellers"),
        ("raw_products.category_id => raw_categories.category_id",
         "products_to_categories", "raw_categories"),
    ]
    for label, ref_name, target_name in checks:
        t, b, m, u, p = describe_links(references[ref_name], ids[target_name])
        lines.append(
            f"{label}\n  tong: {t}; ma trong: {b}; khop: {m}; "
            f"khong khop: {u}; ty le khop tren ma khong trong: {p:.2f}%"
        )

    lines.extend(["", "IV. KIEM TRA KIEU DU LIEU SO"])
    for name, s in stats.items():
        lines.append(f"[{name}]")
        for field, values in s["numeric_summary"].items():
            lines.append(
                f"  {field}: chuoi so={values['text_numeric']}; "
                f"so thuc su={values['numeric_type']}; "
                f"chuoi khong doc duoc={values['invalid_text']}; "
                f"thieu={values['missing']}; kieu khac={values['other_type']}"
            )

    lines.extend(["", "V. TEN FILE NGUON DA GAN VAO DOCUMENTS"])
    for name, s in stats.items():
        lines.append(f"[{name}]")
        for source, count in s["sources"].most_common():
            lines.append(f"  {source}: {count}")

    lines.extend([
        "",
        "VI. LUU Y KHI DANH GIA",
        "- Ban ghi trung ma duoc dem theo ma nghiep vu, khong phai _id MongoDB.",
        "- Ty le lien ket la so khop CHINH XAC sau khi cat khoang trang; "
        "khong tu suy doan cach ghep hay tu sua khoa.",
        "- Khong khop co the do bo du lieu tham khao la mau, "
        "khong tu dong dong nghia du lieu sai.",
        "- Gia tri thieu tinh None, chuoi rong, null/none/nan/n/a/-; "
        "so 0 khong tinh la thieu.",
        "- 'parent_id' trong danh muc goc co the hop le khi de trong.",
        "- Chuoi so nghia la luu dang TEXT; chua phai kieu so de phan tich.",
        "- Bao cao KHONG phat hien moi sai lech noi dung, "
        "KHONG thay the kiem chung nguon du lieu va quyen su dung.",
        "- Chuong trinh khong chinh sua, xoa, hay ghi documents tren Atlas.",
    ])
    return "\n".join(lines) + "\n"


def main():
    uri = dotenv_values(BASE / ".env").get("MONGO_URI")
    if not uri:
        print("LOI: File .env trong cung thu muc chua co MONGO_URI.")
        return
    try:
        with MongoClient(uri, serverSelectionTimeoutMS=10000) as client:
            client.admin.command("ping")
            db = client[DB_NAME]
            stats, ids, refs = collect_data(db)
        report = make_report(stats, ids, refs)
        REPORT_FILE.write_text(report, encoding="utf-8")
        print("\nKIEM TRA HOAN THANH!")
        print("TONG DOCUMENTS:", sum(s["documents"] for s in stats.values()))
        print("FILE BAO CAO:", REPORT_FILE)
        print("Khong co du lieu MongoDB nao bi thay doi.")
    except Exception as exc:
        # Khong in thong diep co the chua thong tin nhay cam tu URI.
        print("LOI KHI KIEM TRA. Loai loi:", type(exc).__name__)
        print("Neu can, gui chi ten loai loi; KHONG gui URI hoac mat khau.")


if __name__ == "__main__":
    main()

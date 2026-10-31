import os
import json
from collections import Counter

from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

# 1. Ket noi MongoDB
load_dotenv()
uri = os.getenv("MONGO_URI")

if not uri:
    raise RuntimeError("Khong tim thay MONGO_URI")

client = MongoClient(uri, serverSelectionTimeoutMS=10000)
client.admin.command("ping")

db = client["tikilens_vn"]
collection = db["clean_reviews"]

# 2. Bon truong can chuyen doi
fields = [
    "images",
    "product_attributes",
    "vote_agree",
    "vote_disagree"
]

stats = Counter()
errors = []
updates = []

print("Ket noi thanh cong!")
print("Tong documents:", collection.count_documents({}))

# 3. Doc va kiem tra du lieu
for doc in collection.find(
    {},
    {"_id": 1, **{field: 1 for field in fields}}
):
    changes = {}

    for field in fields:
        value = doc.get(field)

        if isinstance(value, list):
            stats[f"{field}_already_array"] += 1
            continue

        if not isinstance(value, str):
            stats[f"{field}_other_type"] += 1
            continue

        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            errors.append((str(doc["_id"]), field, "Invalid JSON"))
            continue

        if not isinstance(parsed, list):
            errors.append((str(doc["_id"]), field, "Not Array"))
            continue

        changes[field] = parsed
        stats[f"{field}_converted"] += 1

    if changes:
        updates.append(
            UpdateOne(
                {"_id": doc["_id"]},
                {"$set": changes}
            )
        )

# 4. In thong ke
print("\n=== KET QUA DRY RUN ===")

for key, value in sorted(stats.items()):
    print(f"{key}: {value}")

print("Documents can cap nhat:", len(updates))
print("So loi:", len(errors))

if errors:
    print("10 loi dau tien:", errors[:10])

# 5. Mac dinh chi xem truoc; chi bat True khi chu dong cap nhat MongoDB.
APPLY_CHANGES = False

if APPLY_CHANGES:
    if errors:
        raise RuntimeError("Co loi JSON, dung cap nhat")

    total_modified = 0

    for i in range(0, len(updates), 500):
        result = collection.bulk_write(
            updates[i:i + 500],
            ordered=False
        )
        total_modified += result.modified_count

    print("Da cap nhat:", total_modified)
else:
    print("DRY RUN: Chua thay doi du lieu MongoDB")

client.close()

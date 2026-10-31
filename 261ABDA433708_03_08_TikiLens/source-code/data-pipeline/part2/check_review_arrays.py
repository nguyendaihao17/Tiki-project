import os
from collections import Counter
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client["tikilens_vn"]
collection = db["clean_reviews"]

fields = [
    "images",
    "product_attributes",
    "vote_agree",
    "vote_disagree"
]

for field in fields:
    counts = Counter()

    for doc in collection.find({}, {field: 1}):
        if field not in doc:
            counts["missing"] += 1
        else:
            counts[type(doc[field]).__name__] += 1

    print(f"\nTruong: {field}")
    for data_type, count in counts.items():
        print(f"  {data_type}: {count}")

client.close()

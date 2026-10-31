import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Đọc URI từ file .env
load_dotenv()

uri = os.getenv("MONGO_URI")

if not uri:
    raise RuntimeError("Không tìm thấy MONGO_URI")

# Kết nối MongoDB Atlas
client = MongoClient(uri, serverSelectionTimeoutMS=10000)

# Kiểm tra kết nối
client.admin.command("ping")
print("Kết nối MongoDB thành công!")

# Truy cập database
db = client["tikilens_vn"]

# Kiểm tra collection clean_reviews
collection = db["clean_reviews"]

print("Database:", db.name)
print("Collection:", collection.name)
print("Số documents:", collection.count_documents({}))

client.close()

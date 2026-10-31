from pathlib import Path

from dotenv import dotenv_values
from pymongo import MongoClient
from pymongo.errors import OperationFailure

# 1. Doc chuoi ket noi tu file .env
config = dotenv_values(Path(__file__).resolve().parent / ".env")
uri = config.get("MONGO_URI")

# 2. Kiem tra cau hinh
if not uri:
    print("LOI: Khong tim thay MONGO_URI!")

else:
    client = None

    try:
        # 3. Ket noi MongoDB Atlas
        client = MongoClient(
            uri,
            serverSelectionTimeoutMS=10000
        )

        # 4. Kiem tra ket noi
        client.admin.command("ping")

        print("KET NOI MONGODB THANH CONG!")

        # 5. Hien thi danh sach database
        for db in client.list_database_names():
            print("Database:", db)

    except OperationFailure as e:
        print("MONGODB TU CHOI THAO TAC!")
        print("Loai loi:", type(e).__name__)
        print("Ma loi:", e.code)
        print("Ten loi:", (e.details or {}).get("codeName"))

    except Exception as e:
        print("KET NOI THAT BAI!")
        print("Loai loi:", type(e).__name__)

    finally:
        if client is not None:
            client.close()

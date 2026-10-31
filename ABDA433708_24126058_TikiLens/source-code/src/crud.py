from datetime import datetime, timezone
import math
from numbers import Integral, Real
import re

import pandas as pd
from bson.int64 import Int64
from pymongo import UpdateOne
from pymongo.errors import BulkWriteError, DuplicateKeyError, PyMongoError

from src.auth import check_permission
from src.analytics import load_products_data
from src.database import get_clean_collection


COLLECTION_NAME = "clean_products"
ACTIVE_FILTER = {"is_deleted": {"$ne": True}}
EDITABLE_FIELDS = {"name", "price", "quantity_sold"}
CREATABLE_FIELDS = {"product_id", "name", "price", "quantity_sold"}
MAX_INT64 = 2**63 - 1


def _parse_product_id(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, Integral):
        product_id = int(value)
        return str(product_id) if product_id > 0 else None
    if isinstance(value, Real):
        numeric_id = float(value)
        if math.isfinite(numeric_id) and numeric_id.is_integer() and numeric_id > 0:
            return str(int(numeric_id))
    if isinstance(value, str) and re.fullmatch(r"\d+", value.strip()):
        product_id = value.strip()
        return product_id if int(product_id) > 0 else None
    return None


def _product_id_query(product_id):
    legacy_id = int(product_id)
    values = [product_id, legacy_id] if product_id == str(legacy_id) else [product_id]
    return {"product_id": {"$in": values}}


def _parse_non_negative_integer(value, label):
    if isinstance(value, bool):
        return None, f"{label} phải là số nguyên không âm."
    try:
        number = int(value)
        if float(value) != number:
            raise ValueError
    except (TypeError, ValueError, OverflowError):
        return None, f"{label} phải là số nguyên không âm."
    if number < 0 or number > MAX_INT64:
        return None, f"{label} phải là số nguyên không âm trong phạm vi Int64."
    return number, None


def _parse_quantity(value):
    return _parse_non_negative_integer(value, "Số lượng bán")


def _revenue(price, quantity):
    revenue = price * quantity
    if revenue > MAX_INT64:
        return None, "Doanh thu ước tính vượt phạm vi Int64."
    return Int64(revenue), None


def _normalize_product(product_data):
    if not isinstance(product_data, dict):
        return None, "Dữ liệu sản phẩm không hợp lệ."
    unsupported = set(product_data) - CREATABLE_FIELDS
    if unsupported:
        return None, f"Không cho phép tạo trường: {', '.join(sorted(unsupported))}."

    product_id = _parse_product_id(product_data.get("product_id"))
    if product_id is None:
        return None, "Mã sản phẩm phải là chuỗi chữ số dương."

    name = product_data.get("name")
    if not isinstance(name, str) or not name.strip():
        return None, "Tên sản phẩm không được để trống."

    price, error = _parse_non_negative_integer(product_data.get("price"), "Giá bán")
    if error:
        return None, error
    quantity, error = _parse_quantity(product_data.get("quantity_sold", 0))
    if error:
        return None, error
    revenue, error = _revenue(price, quantity)
    if error:
        return None, error

    return {
        "product_id": product_id,
        "name": name.strip(),
        "price": Int64(price),
        "quantity_sold": Int64(quantity),
        "revenue_estimate": revenue,
        "rating_average": 0.0,
        "review_count": 0,
        "is_deleted": False,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }, None


def _collection():
    return get_clean_collection(COLLECTION_NAME)


def _invalidate_product_cache():
    load_products_data.clear()


def normalize_product_storage_types():
    """Repair legacy product IDs and numeric fields without merging duplicate records."""
    if not check_permission("admin"):
        return False, "Không có quyền. Chỉ quản trị viên được chuẩn hóa dữ liệu."
    collection = _collection()
    if collection is None:
        return False, "Không thể kết nối CSDL."

    groups = {}
    invalid_count = 0
    try:
        for record in collection.find(
            {}, {"product_id": 1, "price": 1, "quantity_sold": 1, "revenue_estimate": 1}
        ):
            product_id = _parse_product_id(record.get("product_id"))
            if product_id is None:
                invalid_count += 1
            else:
                groups.setdefault(product_id, []).append(record)
    except PyMongoError as error:
        return False, f"Không thể đọc dữ liệu sản phẩm: {error}"

    operations = []
    duplicate_count = 0
    for product_id, records in groups.items():
        if len(records) > 1:
            duplicate_count += len(records)
            continue
        record = records[0]
        price, price_error = _parse_non_negative_integer(record.get("price"), "Giá bán")
        quantity, quantity_error = _parse_quantity(record.get("quantity_sold"))
        revenue, revenue_error = (
            _revenue(price, quantity) if not (price_error or quantity_error) else (None, None)
        )
        if price_error or quantity_error or revenue_error:
            invalid_count += 1
            continue

        updates = {}
        if record["product_id"] != product_id:
            updates["product_id"] = product_id
        if not isinstance(record.get("price"), Int64) or int(record["price"]) != price:
            updates["price"] = Int64(price)
        if not isinstance(record.get("quantity_sold"), Int64) or int(record["quantity_sold"]) != quantity:
            updates["quantity_sold"] = Int64(quantity)
        if not isinstance(record.get("revenue_estimate"), Int64) or int(record.get("revenue_estimate", 0)) != int(revenue):
            updates["revenue_estimate"] = revenue
        if updates:
            updates["updated_at"] = datetime.now(timezone.utc)
            operations.append(
                UpdateOne(
                    {"_id": record["_id"], "product_id": record["product_id"]},
                    {"$set": updates},
                )
            )

    try:
        if operations:
            collection.bulk_write(operations, ordered=True)
    except BulkWriteError as error:
        return False, f"Chuẩn hóa dừng để bảo toàn dữ liệu: {error.details.get('writeErrors', error)}"
    except PyMongoError as error:
        return False, f"Không thể chuẩn hóa dữ liệu: {error}"

    if operations:
        _invalidate_product_cache()
    return True, (
        f"Đã chuẩn hóa {len(operations)} bản ghi (Product ID dạng chuỗi; tiền, số lượng và doanh thu dạng Int64). "
        f"Bỏ qua {duplicate_count} bản ghi trùng mã và {invalid_count} bản ghi không hợp lệ."
    )


def get_all_products_df(include_deleted=False):
    """Read: liệt kê sản phẩm; mặc định chỉ trả về sản phẩm chưa xóa."""
    if not check_permission("user"):
        return pd.DataFrame()
    collection = _collection()
    if collection is None:
        return pd.DataFrame()
    query = {} if include_deleted else ACTIVE_FILTER
    data = list(collection.find(query).sort("product_id", 1))
    frame = pd.DataFrame(data)
    if not frame.empty and "_id" in frame.columns:
        frame["_id"] = frame["_id"].astype(str)
    return frame


def get_product(product_id, include_deleted=False):
    """Read: lấy chi tiết một sản phẩm theo product_id."""
    if not check_permission("user"):
        return None, "Bạn cần đăng nhập để xem dữ liệu sản phẩm."
    parsed_id = _parse_product_id(product_id)
    if parsed_id is None:
        return None, "Mã sản phẩm phải là chuỗi chữ số dương."

    collection = _collection()
    if collection is None:
        return None, "Không thể kết nối cơ sở dữ liệu."
    query = _product_id_query(parsed_id)
    if not include_deleted:
        query.update(ACTIVE_FILTER)
    product = collection.find_one(query)
    if product is None:
        return None, "Không tìm thấy sản phẩm."
    if "_id" in product:
        product["_id"] = str(product["_id"])
    return product, "Đã tìm thấy sản phẩm."


def create_product(product_data):
    """Create: kiểm tra dữ liệu và khóa duy nhất trước khi thêm sản phẩm."""
    if not check_permission("admin"):
        return False, "Không có quyền. Chỉ quản trị viên được thêm sản phẩm."
    product, error = _normalize_product(product_data)
    if error:
        return False, error

    collection = _collection()
    if collection is None:
        return False, "Không thể kết nối CSDL."
    try:
        collection.create_index("product_id", unique=True, name="uq_clean_products_product_id")
    except DuplicateKeyError:
        return False, "Không thể tạo khóa duy nhất vì dữ liệu hiện có chứa product_id trùng lặp."
    except PyMongoError as error:
        return False, f"Không thể kiểm tra khóa sản phẩm: {error}"
    if collection.find_one(_product_id_query(product["product_id"]), {"_id": 1}):
        return False, "Mã sản phẩm đã tồn tại."
    try:
        collection.insert_one(product)
    except DuplicateKeyError:
        return False, "Mã sản phẩm đã tồn tại."
    except PyMongoError as error:
        return False, f"Không thể thêm sản phẩm: {error}"
    _invalidate_product_cache()
    return True, "Thêm sản phẩm thành công."


def update_product(product_id, update_fields):
    """Update: chỉ cho sửa tên, giá, số lượng; tự tính lại doanh thu ước tính."""
    if not check_permission("admin"):
        return False, "Không có quyền. Chỉ quản trị viên được cập nhật sản phẩm."
    parsed_id = _parse_product_id(product_id)
    if parsed_id is None:
        return False, "Mã sản phẩm phải là chuỗi chữ số dương."
    if not isinstance(update_fields, dict) or not update_fields:
        return False, "Vui lòng cung cấp ít nhất một trường cần cập nhật."
    unsupported = set(update_fields) - EDITABLE_FIELDS
    if unsupported:
        return False, f"Không cho phép cập nhật trường: {', '.join(sorted(unsupported))}."

    updates = {}
    if "name" in update_fields:
        name = update_fields["name"]
        if not isinstance(name, str) or not name.strip():
            return False, "Tên sản phẩm không được để trống."
        updates["name"] = name.strip()
    if "price" in update_fields:
        price, error = _parse_non_negative_integer(update_fields["price"], "Giá bán")
        if error:
            return False, error
        updates["price"] = Int64(price)
    if "quantity_sold" in update_fields:
        quantity, error = _parse_quantity(update_fields["quantity_sold"])
        if error:
            return False, error
        updates["quantity_sold"] = Int64(quantity)

    collection = _collection()
    if collection is None:
        return False, "Không thể kết nối CSDL."
    query = {**_product_id_query(parsed_id), **ACTIVE_FILTER}
    try:
        current = collection.find_one(query, {"price": 1, "quantity_sold": 1})
        if current is None:
            return False, "Không tìm thấy sản phẩm đang hoạt động."
        final_price = updates.get("price", current.get("price", 0))
        final_quantity = updates.get("quantity_sold", current.get("quantity_sold", 0))
        final_price, error = _parse_non_negative_integer(final_price, "Giá bán hiện tại")
        if error:
            return False, error
        final_quantity, error = _parse_quantity(final_quantity)
        if error:
            return False, error
        revenue, error = _revenue(final_price, final_quantity)
        if error:
            return False, error
        updates["revenue_estimate"] = revenue
        updates["updated_at"] = datetime.now(timezone.utc)
        result = collection.update_one(query, {"$set": updates})
    except PyMongoError as error:
        return False, f"Không thể cập nhật sản phẩm: {error}"

    if result.modified_count == 0:
        return True, "Dữ liệu đã đúng; không có thay đổi cần lưu."
    _invalidate_product_cache()
    return True, "Cập nhật sản phẩm thành công; doanh thu ước tính đã được tính lại."


def delete_product(product_id):
    """Delete permanently from MongoDB."""
    if not check_permission("admin"):
        return False, "Không có quyền. Chỉ quản trị viên được xóa sản phẩm."
    parsed_id = _parse_product_id(product_id)
    if parsed_id is None:
        return False, "Mã sản phẩm phải là chuỗi chữ số dương."

    collection = _collection()
    if collection is None:
        return False, "Không thể kết nối CSDL."
    try:
        result = collection.delete_one(_product_id_query(parsed_id))
    except PyMongoError as error:
        return False, f"Không thể xóa sản phẩm: {error}"
    if result.deleted_count == 0:
        return False, "Không tìm thấy sản phẩm."
    _invalidate_product_cache()
    return True, "Đã xóa vĩnh viễn sản phẩm khỏi cơ sở dữ liệu."

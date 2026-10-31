import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from bson.int64 import Int64
import pandas as pd

from webapp.admin_page import _product_ids
from src.crud import (
    _normalize_product,
    _product_id_query,
    delete_product,
    normalize_product_storage_types,
    update_product,
)


class AdminPageTests(unittest.TestCase):
    def test_product_ids_sort_mixed_database_types_without_crashing(self):
        frame = pd.DataFrame({"product_id": [20, "3", "alpha", 1, None]})

        self.assertEqual(_product_ids(frame), [1, "3", 20, "alpha"])

    def test_new_product_uses_the_mongodb_storage_types(self):
        product, error = _normalize_product(
            {"product_id": " 42 ", "name": "Sản phẩm", "price": "125000", "quantity_sold": "3"}
        )

        self.assertIsNone(error)
        self.assertEqual(product["product_id"], "42")
        self.assertIsInstance(product["price"], Int64)
        self.assertIsInstance(product["quantity_sold"], Int64)
        self.assertIsInstance(product["revenue_estimate"], Int64)
        self.assertEqual(product["revenue_estimate"], 375000)

    def test_new_product_rejects_fractional_vnd_price(self):
        product, error = _normalize_product(
            {"product_id": "42", "name": "Sản phẩm", "price": 125000.5, "quantity_sold": 3}
        )

        self.assertIsNone(product)
        self.assertIn("số nguyên", error)

    def test_product_id_query_matches_string_and_legacy_number(self):
        self.assertEqual(_product_id_query("42"), {"product_id": {"$in": ["42", 42]}})

    @patch("src.crud._invalidate_product_cache")
    @patch("src.crud._collection")
    @patch("src.crud.check_permission", return_value=True)
    def test_unchanged_update_is_not_reported_as_error(self, _permission, collection, invalidate):
        database = Mock()
        database.find_one.return_value = {"price": 10, "quantity_sold": 2}
        database.update_one.return_value = SimpleNamespace(modified_count=0)
        collection.return_value = database

        success, message = update_product(7, {"name": "Sản phẩm"})

        self.assertTrue(success)
        self.assertIn("không có thay đổi", message)
        invalidate.assert_not_called()

    @patch("src.crud._invalidate_product_cache")
    @patch("src.crud._collection")
    @patch("src.crud.check_permission", return_value=True)
    def test_update_writes_integer_storage_types(self, _permission, collection, invalidate):
        database = Mock()
        database.find_one.return_value = {"price": Int64(10), "quantity_sold": Int64(2)}
        database.update_one.return_value = SimpleNamespace(modified_count=1)
        collection.return_value = database

        success, _ = update_product("7", {"price": 12, "quantity_sold": 3})

        self.assertTrue(success)
        changes = database.update_one.call_args.args[1]["$set"]
        self.assertIsInstance(changes["price"], Int64)
        self.assertIsInstance(changes["quantity_sold"], Int64)
        self.assertIsInstance(changes["revenue_estimate"], Int64)
        self.assertEqual(changes["revenue_estimate"], 36)
        invalidate.assert_called_once()

    @patch("src.crud._invalidate_product_cache")
    @patch("src.crud._collection")
    @patch("src.crud.check_permission", return_value=True)
    def test_delete_removes_the_product_from_mongodb(self, _permission, collection, invalidate):
        database = Mock()
        database.delete_one.return_value = SimpleNamespace(deleted_count=1)
        collection.return_value = database

        success, message = delete_product("7")

        self.assertTrue(success)
        self.assertIn("xóa vĩnh viễn", message)
        database.delete_one.assert_called_once_with({"product_id": {"$in": ["7", 7]}})
        invalidate.assert_called_once()

    @patch("src.crud._invalidate_product_cache")
    @patch("src.crud._collection")
    @patch("src.crud.check_permission", return_value=True)
    def test_normalization_repairs_safe_legacy_storage_types(self, _permission, collection, invalidate):
        database = Mock()
        database.find.return_value = [
            {"_id": "one", "product_id": 1, "price": 10.0, "quantity_sold": 2, "revenue_estimate": 20.0},
            {"_id": "two", "product_id": "2", "price": Int64(10), "quantity_sold": Int64(2), "revenue_estimate": Int64(20)},
            {"_id": "three", "product_id": "bad", "price": 10, "quantity_sold": 2},
            {"_id": "four", "product_id": "4", "price": 1.5, "quantity_sold": 2},
        ]
        collection.return_value = database

        success, message = normalize_product_storage_types()

        self.assertTrue(success)
        self.assertIn("Đã chuẩn hóa 1", message)
        database.bulk_write.assert_called_once()
        self.assertEqual(len(database.bulk_write.call_args.args[0]), 1)
        invalidate.assert_called_once()


if __name__ == "__main__":
    unittest.main()

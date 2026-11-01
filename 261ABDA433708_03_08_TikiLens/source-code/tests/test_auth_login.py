import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import bcrypt
from bson import BSON
from bson.codec_options import CodecOptions

from src import auth


class MongoLoginTests(unittest.TestCase):
    def setUp(self):
        self.failure = {}
        self.codec_options = CodecOptions()
        failures = MagicMock()
        failures.find_one.side_effect = lambda query: (
            BSON.encode(self.failure).decode(self.codec_options) if self.failure else None
        )
        failures.delete_one.side_effect = lambda query: self.failure.clear()

        def replace_failure(query, document, upsert=False):
            self.failure.clear()
            self.failure.update(document)

        def increment_failure(query, changes):
            self.failure["count"] += changes["$inc"]["count"]
            self.failure.update(changes["$set"])

        failures.replace_one.side_effect = replace_failure
        failures.update_one.side_effect = increment_failure
        users = MagicMock()
        users.find_one.return_value = {
            "username": "member",
            "display_name": "Member",
            "role": "user",
            "password_hash": bcrypt.hashpw(b"123456", bcrypt.gensalt(rounds=4)),
        }
        database = MagicMock()
        database.__getitem__.side_effect = {
            "users": users,
            "login_failures": failures,
        }.__getitem__
        for replacement in (
            patch.object(auth, "initialize_auth_store"),
            patch.object(auth, "_uses_sqlite_auth", return_value=False),
            patch.object(auth, "_auth_database", return_value=database),
        ):
            replacement.start()
            self.addCleanup(replacement.stop)

    def seed_failures(self, count, age):
        self.failure.update({
            "_id": "member",
            "count": count,
            "updated_at": datetime.now(timezone.utc) - age,
        })

    def test_correct_pin_after_wrong_pin_logs_in_and_clears_failures(self):
        self.assertIsNone(auth.authenticate("member", "654321"))

        self.assertEqual(auth.authenticate("member", "123456"), {
            "username": "member", "role": "user", "name": "Member",
        })
        self.assertEqual(self.failure, {})

    def test_repeated_wrong_pin_increments_failures(self):
        self.assertIsNone(auth.authenticate("member", "654321"))
        self.assertIsNone(auth.authenticate("member", "654321"))

        self.assertEqual(self.failure["count"], 2)

    def test_ten_recent_failures_still_block_a_correct_pin(self):
        self.seed_failures(10, timedelta(minutes=1))

        self.assertIsNone(auth.authenticate("member", "123456"))
        self.assertEqual(self.failure["count"], 10)

    def test_expired_lock_allows_login_before_mongodb_ttl_cleanup(self):
        self.seed_failures(10, timedelta(minutes=16))

        self.assertIsNotNone(auth.authenticate("member", "123456"))
        self.assertEqual(self.failure, {})

    def test_wrong_pin_after_expired_lock_starts_a_new_count(self):
        self.seed_failures(10, timedelta(minutes=16))

        self.assertIsNone(auth.authenticate("member", "654321"))
        self.assertEqual(self.failure["count"], 1)

    def test_timezone_aware_mongodb_dates_keep_the_same_login_behavior(self):
        for offset in (0, 7):
            with self.subTest(offset=offset):
                self.failure.clear()
                self.codec_options = CodecOptions(
                    tz_aware=True, tzinfo=timezone(timedelta(hours=offset)),
                )
                self.assertIsNone(auth.authenticate("member", "654321"))
                self.assertIsNone(auth.authenticate("member", "654321"))
                self.assertEqual(self.failure["count"], 2)
                self.assertIsNotNone(auth.authenticate("member", "123456"))
                self.assertEqual(self.failure, {})
                self.seed_failures(10, timedelta(minutes=16))
                self.assertIsNotNone(auth.authenticate("member", "123456"))
                self.assertEqual(self.failure, {})


if __name__ == "__main__":
    unittest.main()

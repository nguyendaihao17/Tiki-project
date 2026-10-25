import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from src.auth import (
    _matches_initial_admin_setup_key,
    authenticate,
    create_initial_admin,
    register_user,
    user_count,
)


class RegistrationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.directory.cleanup)
        self.database = Path(self.directory.name) / "users.sqlite3"
        environment = patch.dict(os.environ, {"TIKI_AUTH_DB_PATH": str(self.database)})
        environment.start()
        self.addCleanup(environment.stop)
        self.assertTrue(create_initial_admin("owner", "Owner", "AdminPassword123!")[0])

    def test_registration_creates_standard_user_with_hashed_password(self):
        success, _ = register_user(" new.user ", " New User ", "SafePassword123!")
        self.assertTrue(success)
        self.assertEqual(authenticate("new.user", "SafePassword123!"), {
            "username": "new.user", "role": "user", "name": "New User"
        })
        with closing(sqlite3.connect(self.database)) as connection:
            role, stored_password = connection.execute(
                "SELECT role, password_hash FROM users WHERE username = 'new.user'"
            ).fetchone()
        self.assertEqual(role, "user")
        self.assertNotEqual(stored_password, b"SafePassword123!")

    def test_rejects_duplicate_and_invalid_registration(self):
        self.assertFalse(register_user("ab", "Name", "SafePassword123!")[0])
        self.assertFalse(register_user("member", "Name", "short")[0])
        self.assertTrue(register_user("member", "Name", "SafePassword123!")[0])
        success, message = register_user("MEMBER", "Other", "AnotherPassword123!")
        self.assertFalse(success)
        self.assertIn("đã tồn tại", message)
        self.assertEqual(user_count(), 2)

    def test_initial_admin_setup_key_requires_an_exact_non_empty_match(self):
        self.assertTrue(_matches_initial_admin_setup_key("setup-key", "setup-key"))
        self.assertFalse(_matches_initial_admin_setup_key("wrong-key", "setup-key"))
        self.assertFalse(_matches_initial_admin_setup_key("", "setup-key"))
        self.assertFalse(_matches_initial_admin_setup_key("setup-key", ""))

    def test_initial_admin_can_be_created_after_standard_users_exist(self):
        with closing(sqlite3.connect(self.database)) as connection:
            connection.execute("DELETE FROM users")
            connection.commit()
        self.assertTrue(register_user("member", "Member", "SafePassword123!")[0])

        success, _ = create_initial_admin("admin", "Admin", "AdminPassword123!")

        self.assertTrue(success)
        self.assertEqual(authenticate("admin", "AdminPassword123!")["role"], "admin")


if __name__ == "__main__":
    unittest.main()

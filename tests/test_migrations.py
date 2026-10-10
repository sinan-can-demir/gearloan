"""Smoke test: confirm every app's main table is created by migrate."""
import os
import tempfile
import unittest

import django
from django.test import SimpleTestCase


class MigrationsApplyTest(SimpleTestCase):
    """
    Runs the full migrate command against a fresh SQLite file and checks that
    each app's primary table exists. This catches the class of bug where model
    changes are not committed as migrations.
    """

    def test_migrate_creates_all_tables(self):
        import subprocess
        import sys

        with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as f:
            db_path = f.name

        try:
            env = {
                **os.environ,
                "DEBUG": "True",
                "SECRET_KEY": "test-migrate-smoke-key",
                "DATABASE_URL": f"sqlite:///{db_path}",
            }
            result = subprocess.run(
                [sys.executable, "manage.py", "migrate", "--run-syncdb"],
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(
                result.returncode,
                0,
                msg=f"migrate failed:\n{result.stdout}\n{result.stderr}",
            )

            import sqlite3

            conn = sqlite3.connect(db_path)
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            conn.close()

            expected = {
                "accounts_role",
                "accounts_user",
                "departments_department",
                "courses_term",
                "courses_course",
                "courses_enrollment",
                "inventory_itemtype",
                "inventory_unit",
                "bookings_booking",
                "bookings_conditionlog",
                "fees_fee",
                "audit_auditevent",
            }
            missing = expected - tables
            self.assertFalse(
                missing,
                msg=f"Tables missing after migrate: {sorted(missing)}",
            )
        finally:
            os.unlink(db_path)

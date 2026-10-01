import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.dualrun.fence import FenceError
from scripts.dualrun.snapshot import capture


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="ruoyicrm-crit10-test-")
        self.addCleanup(self.tmp.cleanup)
        self.runtime = Path(self.tmp.name) / "ruoyicrm-crit10-abc123"
        self.runtime.mkdir()
        self.runtime = self.runtime.resolve()
        self.state = self.runtime / "state.json"
        self.stack = {"project": "ruoyicrm-crit10-abc123", "runtime_dir": str(self.runtime),
                      "ports": {"mysql": 50001, "redis": 50002},
                      "containers": {"mysql": "a" * 64, "redis": "b" * 64},
                      "volumes": {"mysql": "ruoyicrm-crit10-abc123_mysql_data",
                                  "redis": "ruoyicrm-crit10-abc123_redis_data"}}
        for name in ("mysql-app.cnf", "redis-password"):
            file = self.runtime / name
            file.write_text("synthetic-secret\n")
            os.chmod(file, 0o600)
        self.identity = patch("scripts.dualrun.snapshot.stack_identity", return_value=self.stack)
        self.urls = patch("scripts.dualrun.snapshot.verify_tenant_urls")
        self.identity.start()
        self.urls.start()
        self.addCleanup(self.identity.stop)
        self.addCleanup(self.urls.stop)

    def fake_backup(self, command, *, stdout=None, env=None):
        if command[0] == "mysqldump":
            self.assertIn("--single-transaction", command)
            self.assertEqual(command[-3:], ["rycrm-master", "rycrm-tenant-1", "rycrm-tenant-2"])
            stdout.write(b"-- MySQL dump synthetic\n")
        elif command[0] == "redis-cli":
            self.assertEqual(env["REDISCLI_AUTH"], "synthetic-secret")
            file = Path(command[-1])
            file.write_bytes(b"REDIS0011synthetic")
            os.chmod(file, 0o600)
        else:
            self.fail("unexpected backup process")

    def test_capture_binds_case_and_private_artifacts(self):
        receipt_path = capture(self.state, "POST", "/system/notice", runner=self.fake_backup, now=time.time())
        receipt = json.loads(receipt_path.read_text())
        self.assertEqual((receipt["method"], receipt["path"]), ("POST", "/system/notice"))
        self.assertEqual(receipt["containers"], self.stack["containers"])
        for name in ("prewrite-snapshot.json", "prewrite-mysql.sql", "prewrite-redis.rdb"):
            self.assertEqual((self.runtime / name).stat().st_mode & 0o077, 0)

    def test_failed_second_backup_invalidates_prior_case_and_artifacts(self):
        capture(self.state, "POST", "/system/notice", runner=self.fake_backup, now=time.time())

        def fail_redis(command, *, stdout=None, env=None):
            if command[0] == "redis-cli":
                raise FenceError("backup command failed")
            self.fake_backup(command, stdout=stdout, env=env)

        with self.assertRaises(FenceError):
            capture(self.state, "POST", "/system/post", runner=fail_redis, now=time.time())
        for name in ("prewrite-snapshot.json", "prewrite-mysql.sql", "prewrite-redis.rdb"):
            self.assertFalse((self.runtime / name).exists())

    def test_wrong_path_and_world_readable_credential_fail_closed(self):
        with self.assertRaises(FenceError):
            capture(self.state, "POST", "/../system/notice", runner=self.fake_backup)
        os.chmod(self.runtime / "redis-password", 0o644)
        with self.assertRaises(FenceError):
            capture(self.state, "POST", "/system/notice", runner=self.fake_backup)


if __name__ == "__main__":
    unittest.main()

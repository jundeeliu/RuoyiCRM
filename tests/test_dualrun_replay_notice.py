import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts.dualrun.fence import FenceError
from scripts.dualrun.replay_notice import ReplayError, notice_fixture, run


class NoticeReplayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="notice-replay-test-")
        self.addCleanup(self.tmp.cleanup)
        self.fixture = Path(self.tmp.name) / "candidate.json"
        self.fixture.write_text(json.dumps({"fixtures": [{"id": "RUOYICRM-059", "http_method": "POST",
            "path_template": "/system/notice", "tenant": "tenant1", "request": {"json": {
            "noticeTitle": "CRIT04 abc123 notice", "noticeType": "1", "noticeContent":
            "Synthetic disposable replay notice abc123", "status": "0"}}}]}))
        self.args = SimpleNamespace(fixture=self.fixture, source_state=Path("source"), target_state=Path("target"),
                                    source_app=Path("source-app"), target_app=Path("target-app"),
                                    source_url="http://127.0.0.1:50111", target_url="http://127.0.0.1:50222",
                                    source_snapshot=Path("source-snapshot"), target_snapshot=Path("target-snapshot"))
        self.tokens = patch.dict(os.environ, {"CRIT04_BASELINE_TOKEN": "synthetic-left",
                                           "CRIT04_TARGET_TOKEN": "synthetic-right"})
        self.tokens.start()
        self.addCleanup(self.tokens.stop)

    def test_fixture_rejects_business_title(self):
        data = json.loads(self.fixture.read_text())
        data["fixtures"][0]["request"]["json"]["noticeTitle"] = "Customer notice"
        self.fixture.write_text(json.dumps(data))
        with self.assertRaises(ReplayError):
            notice_fixture(self.fixture)

    def test_failed_fence_never_sends_http(self):
        with patch("scripts.dualrun.replay_notice.authorize_write", side_effect=ReplayError("blocked")), \
             patch("scripts.dualrun.replay_notice.post_notice") as post:
            with self.assertRaises(ReplayError):
                run(self.args)
            post.assert_not_called()

    def test_exact_row_and_http_match_pass(self):
        body = notice_fixture(self.fixture)
        row = ["1", body["noticeTitle"], "1", body["noticeContent"].encode().hex().upper(), "0",
               "synthetic-admin", "2026-10-02 03:00:00", "", "NULL", "NULL"]
        response = {"status": 200, "content_type": "application/json", "body_sha256": "a" * 64, "json_code": 200}
        with patch("scripts.dualrun.replay_notice.authorize_write", return_value={"status": "LOCAL_WRITE_FENCE_PASSED"}) as gate, \
             patch("scripts.dualrun.replay_notice.notice_rows", side_effect=[[], [], [row], [row]]), \
             patch("scripts.dualrun.replay_notice.storage_metadata", return_value={"mysql_version": "8.4.11", "server_charset": "utf8mb4", "session_timezone": "SYSTEM", "system_timezone": "UTC", "table_engine": "InnoDB"}), \
             patch("scripts.dualrun.replay_notice.notice_counts", side_effect=[
                 {"rycrm-tenant-1": 0, "rycrm-tenant-2": 0}, {"rycrm-tenant-1": 0, "rycrm-tenant-2": 0},
                 {"rycrm-tenant-1": 1, "rycrm-tenant-2": 0}, {"rycrm-tenant-1": 1, "rycrm-tenant-2": 0}]), \
             patch("scripts.dualrun.replay_notice.post_notice", return_value=response) as post:
            result = run(self.args)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(gate.call_count, 3)
        self.assertEqual(post.call_count, 2)

    def test_target_row_drift_fails(self):
        body = notice_fixture(self.fixture)
        row = ["1", body["noticeTitle"], "1", body["noticeContent"].encode().hex().upper(), "0",
               "synthetic-admin", "2026-10-02 03:00:00", "", "NULL", "NULL"]
        response = {"status": 200, "content_type": "application/json", "body_sha256": "a" * 64, "json_code": 200}
        with patch("scripts.dualrun.replay_notice.authorize_write", return_value={"status": "LOCAL_WRITE_FENCE_PASSED"}), \
             patch("scripts.dualrun.replay_notice.notice_rows", side_effect=[[], [], [row], [row[:-1] + ["wrong"]]]), \
             patch("scripts.dualrun.replay_notice.storage_metadata", return_value={"mysql_version": "8.4.11", "server_charset": "utf8mb4", "session_timezone": "SYSTEM", "system_timezone": "UTC", "table_engine": "InnoDB"}), \
             patch("scripts.dualrun.replay_notice.notice_counts", side_effect=[
                 {"rycrm-tenant-1": 0, "rycrm-tenant-2": 0}, {"rycrm-tenant-1": 0, "rycrm-tenant-2": 0},
                 {"rycrm-tenant-1": 1, "rycrm-tenant-2": 0}, {"rycrm-tenant-1": 1, "rycrm-tenant-2": 0}]), \
             patch("scripts.dualrun.replay_notice.post_notice", return_value=response):
            result = run(self.args)
        self.assertEqual(result["status"], "FAIL")

    def test_second_fence_error_records_exact_fixed_assertion_and_skips_target(self):
        body = notice_fixture(self.fixture)
        row = ["1", body["noticeTitle"], "1", body["noticeContent"].encode().hex().upper(), "0",
               "synthetic-admin", "2026-10-02 03:00:00", "", "NULL", "NULL"]
        response = {"status": 200, "content_type": "application/json", "body_sha256": "a" * 64, "json_code": 200}
        with patch("scripts.dualrun.replay_notice.authorize_write", side_effect=[
                 {"status": "LOCAL_WRITE_FENCE_PASSED"}, {"status": "LOCAL_WRITE_FENCE_PASSED"},
                 FenceError("application socket proof is incomplete")]), \
             patch("scripts.dualrun.replay_notice.storage_metadata", return_value={"mysql_version": "8.4.11", "server_charset": "utf8mb4", "session_timezone": "SYSTEM", "system_timezone": "UTC", "table_engine": "InnoDB"}), \
             patch("scripts.dualrun.replay_notice.notice_rows", side_effect=[[], [], [row]]), \
             patch("scripts.dualrun.replay_notice.notice_counts", side_effect=[
                 {"rycrm-tenant-1": 0, "rycrm-tenant-2": 0}, {"rycrm-tenant-1": 0, "rycrm-tenant-2": 0},
                 {"rycrm-tenant-1": 1, "rycrm-tenant-2": 0}]), \
             patch("scripts.dualrun.replay_notice.post_notice", return_value=response) as post:
            result = run(self.args)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["error_detail"], "application socket proof is incomplete")
        self.assertEqual(result["write_attempted"], "SOURCE")
        self.assertEqual(post.call_count, 1)


if __name__ == "__main__":
    unittest.main()

import base64
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.dualrun.compare import ComparisonError, compare_http


def jwt(tenant, user_uuid, algorithm="HS512"):
    def segment(obj):
        return base64.urlsafe_b64encode(json.dumps(obj, separators=(",", ":")).encode()).decode().rstrip("=")
    signature = base64.urlsafe_b64encode(b"x" * 64).decode().rstrip("=")
    return segment({"alg": algorithm, "typ": "JWT"}) + "." + segment({"tenant": tenant, "login_user_key": user_uuid}) + "." + signature


def response(obj, status=200):
    return {"status": status, "content_type": "application/json;charset=UTF-8",
            "body": json.dumps(obj, separators=(",", ":")).encode()}


class DualRunCompareTests(unittest.TestCase):
    def test_offline_cli_receipts_do_not_echo_bodies(self):
        with tempfile.TemporaryDirectory(prefix="dualrun-cli-") as directory:
            root = Path(directory)
            envelope = {"status": 200, "content_type": "application/json",
                        "body_base64": base64.b64encode(b'{"secret":"synthetic-sensitive-value","code":200}').decode()}
            for side in ("left", "right"):
                (root / f"{side}.json").write_text(json.dumps(envelope))
            (root / "rules.json").write_text("[]")
            result = subprocess.run([sys.executable, "-m", "scripts.dualrun.cli", "compare",
                                     "--left", str(root / "left.json"), "--right", str(root / "right.json"),
                                     "--rules", str(root / "rules.json")],
                                    capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0)
            self.assertNotIn("synthetic-sensitive-value", result.stdout + result.stderr)
            self.assertTrue(json.loads(result.stdout)["equal"])

    def test_only_allowlisted_ruoyi_dynamic_fields_are_canonicalized(self):
        left = {"code": 200, "msg": "操作成功", "uuid": "123e4567e89b12d3a456426614174000",
                "traceId": "0123456789abcdef", "createdAt": "2026-10-02T10:00:00+08:00",
                "token": jwt("tenant1", "123e4567e89b12d3a456426614174000")}
        right = {**left, "uuid": "123e4567e89b12d3a456426614174001",
                 "traceId": "0123456789abcdee", "createdAt": "2026-10-02T10:00:01+08:00",
                 "token": jwt("tenant1", "123e4567e89b12d3a456426614174001")}
        rules = [{"path": "/uuid", "kind": "uuid"}, {"path": "/traceId", "kind": "trace_id"},
                 {"path": "/createdAt", "kind": "timestamp"}, {"path": "/token", "kind": "token"}]
        self.assertTrue(compare_http(response(left), response(right), rules)["equal"])
        right["msg"] = "权限不足"
        self.assertEqual(compare_http(response(left), response(right), rules)["reason"], "JSON_BEHAVIOR_DRIFT")

    def test_token_normalizer_preserves_tenant_claim(self):
        left = response({"token": jwt("tenant1", "123e4567e89b12d3a456426614174000")})
        right = response({"token": jwt("tenant2", "123e4567e89b12d3a456426614174001")})
        self.assertFalse(compare_http(left, right, [{"path": "/token", "kind": "token"}])["equal"])
        bad = response({"token": jwt("tenant1", "123e4567e89b12d3a456426614174000", "none")})
        with self.assertRaises(ComparisonError):
            compare_http(left, bad, [{"path": "/token", "kind": "token"}])

    def test_wrong_type_missing_path_and_wildcard_fail_closed(self):
        left = response({"items": [{"uuid": "123e4567e89b12d3a456426614174000"}]})
        with self.assertRaises(ComparisonError):
            compare_http(left, left, [{"path": "/items/*/uuid", "kind": "uuid"}])
        with self.assertRaises(ComparisonError):
            compare_http(left, response({"items": []}), [{"path": "/items/0/uuid", "kind": "uuid"}])
        with self.assertRaises(ComparisonError):
            compare_http(left, response({"items": [{"uuid": 123}]}), [{"path": "/items/0/uuid", "kind": "uuid"}])

    def test_strict_json_type_and_duplicate_keys(self):
        self.assertFalse(compare_http(response({"code": 1}), response({"code": True}), [])["equal"])
        duplicate = {"status": 200, "content_type": "application/json;charset=UTF-8", "body": b'{"code":200,"code":500}'}
        with self.assertRaises(ComparisonError):
            compare_http(duplicate, duplicate, [])
        with self.assertRaises(ComparisonError):
            compare_http(response({"x": "not-a-timestamp"}), response({"x": "not-a-timestamp"}),
                         [{"path": "/x", "kind": "timestamp"}])

    def test_status_content_type_and_non_json_are_not_masked(self):
        self.assertEqual(compare_http(response({"code": 200}), response({"code": 200}, 500), [])["reason"], "HTTP_STATUS")
        plain = {"status": 200, "content_type": "text/html", "body": b"<html></html>"}
        with self.assertRaises(ComparisonError):
            compare_http(plain, plain, [])


if __name__ == "__main__":
    unittest.main()

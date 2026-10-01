"""Static source-bound validation for planned, unexecuted non-GET replay cases."""

import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/crit04/ruoyicrm-150.json"
MATRIX = ROOT / "docs/crit04/write-fixture-matrix.json"


def source_cases():
    return {case["id"]: case for case in json.loads(MANIFEST.read_text())["cases"]
            if case["http_method"] != "GET"}


def planned_cases():
    return json.loads(MATRIX.read_text())


def fixture_gaps(row, fixture):
    """Validate a future disposable-only fixture without executing it."""
    if not isinstance(fixture, dict):
        return ["fixture:not_object"]
    contract = row["fixture_contract"]
    gaps = []
    if fixture.get("environment") != "TWO_DISPOSABLE_STACKS_ONLY":
        gaps.append("environment")
    if contract["tenant_header"] and (type(fixture.get("tenant")) is not str or not fixture["tenant"]):
        gaps.append("tenant")
    if contract["auth"] == "tenant_scoped_admin_token" and (type(fixture.get("token_ref")) is not str or not fixture["token_ref"]):
        gaps.append("token_ref")
    if contract["media_type"] == "json":
        body = fixture.get("json")
        if not isinstance(body, dict):
            gaps.append("json")
        else:
            gaps.extend("json." + key for key in contract["json_fields"] if key not in body)
    for group in ("path_params", "form_fields", "multipart_fields"):
        key = {"path_params": "path_params", "form_fields": "form", "multipart_fields": "multipart"}[group]
        data = fixture.get(key, {})
        if not isinstance(data, dict):
            gaps.append(key)
        else:
            gaps.extend(key + "." + item for item in contract[group] if item not in data)
    if type(fixture.get("expected_status")) is not int or not 100 <= fixture["expected_status"] <= 599:
        gaps.append("expected_status")
    expected_hash = fixture.get("expected_body_sha256")
    if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
        gaps.append("expected_body_sha256")
    return gaps


class WriteMatrixTests(unittest.TestCase):
    def test_every_non_get_case_is_bound_to_exact_source_and_unexecuted(self):
        original = source_cases()
        matrix = planned_cases()
        rows = matrix["cases"]
        self.assertEqual(matrix["schema"], "ruoyicrm.crit04.write-fixture-matrix.v1")
        self.assertEqual(matrix["cases_total"], 80)
        self.assertEqual(matrix["execution_status"], "NOT_RUN")
        self.assertEqual(matrix["write_isolation"], "NOT_AUTHORIZED")
        self.assertEqual(len(rows), 80)
        self.assertEqual({row["id"] for row in rows}, set(original))
        for row in rows:
            source = original[row["id"]]
            for field in ("http_method", "path_template", "controller", "controller_line",
                          "controller_sha256", "java_method"):
                self.assertEqual(row[field], source[field], row["id"])
            self.assertEqual(hashlib.sha256((ROOT / row["controller"]).read_bytes()).hexdigest(),
                             row["controller_sha256"], row["id"])
            self.assertIn("public ", row["source_signature"])
            self.assertEqual(row["execution_status"], "NOT_RUN")
            self.assertEqual(row["baseline_oracle"], "NOT_CAPTURED")
            self.assertTrue(row["planning_status"].startswith("BLOCKED_"))
            self.assertEqual(row["storage_scope"], "TWO_DISPOSABLE_STACKS_ONLY")
            self.assertTrue(row["prerequisites"] and row["side_effect_targets"])

    def test_fixture_contract_matches_source_signature_and_paths(self):
        for row in planned_cases()["cases"]:
            contract = row["fixture_contract"]
            expected_path = re.findall(r"\{([^}]+)\}", row["path_template"])
            self.assertEqual(contract["path_params"], expected_path, row["id"])
            if "@RequestBody" in row["source_signature"]:
                self.assertEqual(contract["media_type"], "json", row["id"])
                self.assertTrue(contract["json_fields"], row["id"])
            if "MultipartFile" in row["source_signature"]:
                self.assertEqual(contract["media_type"], "multipart", row["id"])
                self.assertTrue(contract["multipart_fields"], row["id"])
            if "HttpServletResponse" in row["source_signature"]:
                self.assertEqual(row["planning_status"], "BLOCKED_EXPORT_ORACLE", row["id"])
            self.assertFalse(row["id"] == "RUOYICRM-073" and contract["tenant_header"])

    def test_future_fixture_validator_rejects_missing_oracle_and_write_scope(self):
        row = next(row for row in planned_cases()["cases"] if row["id"] == "RUOYICRM-019")
        gaps = fixture_gaps(row, {"json": {"configName": "synthetic"}})
        self.assertIn("environment", gaps)
        self.assertIn("json.configKey", gaps)
        self.assertIn("json.configValue", gaps)
        self.assertIn("expected_body_sha256", gaps)
        self.assertIn("token_ref", gaps)


if __name__ == "__main__":
    unittest.main()

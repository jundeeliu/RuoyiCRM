"""Validate bounded fixture candidates without authorizing or executing writes."""

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "docs/crit04/direct-write-fixtures-candidates.json"
MATRIX = ROOT / "docs/crit04/write-fixture-matrix.json"


class DirectWriteCandidatesTests(unittest.TestCase):
    def test_all_eleven_direct_synthetic_cases_have_source_bound_bounded_payloads(self):
        document = json.loads(CANDIDATES.read_text())
        matrix = json.loads(MATRIX.read_text())
        direct = {row["id"]: row for row in matrix["cases"] if row["classification"] == "DIRECT_SYNTHETIC"}
        self.assertEqual(len(direct), 11)
        self.assertEqual(document["cases_total"], 11)
        self.assertEqual({row["id"] for row in document["fixtures"]}, set(direct))
        self.assertRegex(document["run_nonce"], r"^w[0-9a-f]{8}$")
        for row in document["fixtures"]:
            source = direct[row["id"]]
            self.assertEqual((row["http_method"], row["path_template"], row["controller_sha256"]),
                             (source["http_method"], source["path_template"], source["controller_sha256"]))
            self.assertEqual(row["environment"], "TWO_DISPOSABLE_STACKS_ONLY")
            self.assertEqual(row["request"]["content_type"], "application/json")
            body = row["request"]["json"]
            self.assertLess(len(json.dumps(body).encode()), 2048)
            self.assertTrue(set(source["fixture_contract"]["json_fields"]) <= set(body))
            self.assertEqual(row["tenant"], "tenant1")
            self.assertTrue(row["single_use"])
            self.assertEqual(row["execution_status"], "NOT_RUN")
            self.assertEqual(row["planning_status"], "CANDIDATE_BLOCKED")
            self.assertEqual(row["baseline_oracle"], {"status": "NOT_CAPTURED", "expected_status": None,
                                                       "expected_body_sha256": None})
            self.assertEqual(row["prewrite_snapshot"]["status"], "NOT_CAPTURED")
            self.assertNotEqual(row["execution_status"], "PASS")

    def test_no_embedded_runtime_credentials_or_existing_sample_rows(self):
        document = json.loads(CANDIDATES.read_text())
        data = json.dumps(document)
        self.assertNotIn("root", data)
        self.assertNotIn("localhost:3306", data)
        self.assertNotIn("13800138000", data)
        self.assertEqual(len({json.dumps(row["request"]["json"], sort_keys=True) for row in document["fixtures"]}), 11)
        users = [row for row in document["fixtures"] if row["id"] == "RUOYICRM-094"]
        self.assertEqual(users[0]["request"]["json"]["password"], "$ENV:CRIT04_SYNTHETIC_USER_PASSWORD")
        dept = next(row for row in document["fixtures"] if row["id"] == "RUOYICRM-028")
        self.assertEqual(dept["request"]["json"]["parentId"], "$REF:synthetic_active_dept_id")
        self.assertFalse(any(re.fullmatch(r"[0-9a-f]{64}", str(row["baseline_oracle"]["expected_body_sha256"]))
                             for row in document["fixtures"]))


if __name__ == "__main__":
    unittest.main()

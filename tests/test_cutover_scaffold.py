import importlib.util
import json
import time
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
CUTOVER = ROOT / "deploy" / "cutover"
spec = importlib.util.spec_from_file_location("rollback_sentinel", CUTOVER / "rollback_sentinel.py")
sentinel = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sentinel)


class CutoverScaffoldTests(unittest.TestCase):
    def test_actual_schema_expand_preserves_legacy_host_and_contract_is_separate(self):
        source = (ROOT / "sql" / "rycrm-master.sql").read_text()
        mapper = (ROOT / "ruoyi-tenant/src/main/resources/mapper/tenant/MasterTenantMapper.xml").read_text()
        expand = (CUTOVER / "sql/01_expand.sql").read_text()
        contract = (CUTOVER / "sql/99_contract_manual.sql").read_text()
        self.assertIn("`host` varchar(64)", source)
        self.assertIn("host_name", mapper)
        self.assertIn("ADD COLUMN host_name", expand)
        self.assertNotIn("DROP COLUMN", expand)
        self.assertIn("DROP COLUMN host", contract)
        self.assertIn("ALGORITHM=INSTANT, LOCK=DEFAULT", expand)

    def test_canary_stages_have_exact_two_destinations_and_rollback_zero(self):
        rule = json.loads((CUTOVER / "istio/destination-rule.json").read_text())
        self.assertEqual({s["name"] for s in rule["spec"]["subsets"]}, {"legacy", "boot4"})
        for weight in (0, 1, 10, 50, 100):
            route = json.loads((CUTOVER / f"istio/{weight:03d}-boot4.json").read_text())
            entries = route["spec"]["http"][0]["route"]
            self.assertEqual([item["weight"] for item in entries], [100 - weight, weight])
            self.assertEqual([item["destination"]["subset"] for item in entries], ["legacy", "boot4"])
            self.assertEqual(route["metadata"]["annotations"]["cutover.ruoyicrm.io/plan-id"], sentinel.PLAN_ID)

    def test_thresholds_and_insufficient_sample_choose_rollback(self):
        good = {"new_requests_per_minute": 100, "new_5xx_per_minute": 1,
                "new_p95_ms": 100, "old_p95_ms": 100}
        self.assertEqual(sentinel.decision(good)[0], "HOLD")
        self.assertEqual(sentinel.decision({**good, "new_5xx_per_minute": 5})[0], "ROLLBACK")
        self.assertEqual(sentinel.decision({**good, "new_p95_ms": 200})[0], "ROLLBACK")
        self.assertEqual(sentinel.decision({**good, "new_requests_per_minute": 1})[0], "ROLLBACK")

    def test_stale_nan_and_ambiguous_prometheus_samples_fail_closed(self):
        now = time.time()
        def response(ts, value, rows=1):
            return {"status": "success", "data": {"resultType": "vector",
                    "result": [{"metric": {}, "value": [ts, value]}] * rows}}
        for payload in (response(now - 31, "1"), response(now, "NaN"), response(now, "1", 2)):
            with self.assertRaises(sentinel.UnsafeState):
                sentinel.sample(payload, now)
        with self.assertRaises(sentinel.UnsafeState):
            sentinel.validate_endpoint("http://prometheus.example.com")
        with self.assertRaises(sentinel.UnsafeState):
            sentinel.validate_endpoint("https://prometheus.example.com/unsafe/path")

    def test_missing_telemetry_rolls_back_in_dry_run_without_kubectl(self):
        config = json.loads((CUTOVER / "prometheus-queries.json").read_text())
        with patch.object(sentinel, "apply_rollback") as apply:
            result = sentinel.run(config, "http://127.0.0.1:9090", False, None, None,
                                  fetch=lambda *_: (_ for _ in ()).throw(OSError("offline")))
        self.assertEqual(result["decision"], "ROLLBACK")
        self.assertFalse(result["applied"])
        apply.assert_not_called()

    def test_watch_rechecks_hold_and_stops_at_rollback(self):
        decisions = iter([{"decision": "HOLD"}, {"decision": "ROLLBACK"}])
        sleeps = []
        result = sentinel.monitor({}, "https://example.test", False, None, None, 5,
                                  evaluate=lambda *_: next(decisions), sleep=sleeps.append)
        self.assertEqual(result["decision"], "ROLLBACK")
        self.assertEqual(sleeps, [5])
        with self.assertRaises(sentinel.UnsafeState):
            sentinel.monitor({}, "https://example.test", False, None, None, 0)

    def test_apply_requires_context_uid_owned_route_and_uses_resource_version(self):
        route = json.loads((CUTOVER / "istio/010-boot4.json").read_text())
        route["metadata"]["resourceVersion"] = "42"
        calls = []
        def fake_kubectl(*args, input_text=None):
            calls.append((args, input_text))
            if args == ("config", "current-context"):
                return "test-context"
            if "namespace" in args:
                return json.dumps({"metadata": {"uid": "test-uid"}})
            if "get" in args:
                return json.dumps(route)
            return ""
        with patch.object(sentinel, "kubectl", side_effect=fake_kubectl):
            with self.assertRaises(sentinel.UnsafeState):
                sentinel.apply_rollback("wrong-context", "test-uid")
            sentinel.apply_rollback("test-context", "test-uid")
        replaced = json.loads(calls[-1][1])
        self.assertEqual(replaced["metadata"]["resourceVersion"], "42")
        self.assertEqual([x["weight"] for x in replaced["spec"]["http"][0]["route"]], [100, 0])
        route["metadata"]["annotations"].clear()
        with self.assertRaises(sentinel.UnsafeState):
            sentinel.validate_route(route)


if __name__ == "__main__":
    unittest.main()

"""Bounded local checks for source inventory and HTTP replay semantics."""

from __future__ import annotations

import json
import hashlib
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from scripts import crit02_scc_audit, crit04_replay


class _Handler(BaseHTTPRequestHandler):
    body = b'{"code":200,"message":"stable"}'

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(self.body)

    def log_message(self, *_args):
        pass


class DeliveryBoundaryTests(unittest.TestCase):
    def test_150_cases_and_mapper_statements_are_source_bound(self):
        saved = json.loads((crit04_replay.ROOT / "docs/crit04/ruoyicrm-150.json").read_text())
        self.assertEqual(saved, crit04_replay.build_manifest())
        self.assertEqual(150, len(saved["cases"]))
        self.assertEqual(150, sum(len(m["statements"]) for m in saved["mapper_sources"]))
        self.assertEqual("/system/user/", saved["cases"][91]["path_template"])
        for case in saved["cases"]:
            source = (crit04_replay.ROOT / case["controller"]).read_text().splitlines()
            self.assertIn("Mapping", source[case["controller_line"] - 1])

    def test_missing_physical_runtimes_leave_all_cases_not_run(self):
        manifest = crit04_replay.build_manifest()
        receipt = crit04_replay.replay(manifest, None, None, {}, False)
        self.assertEqual((150, 0, 0, 150),
                         (receipt["planned"], receipt["passed"], receipt["failed"], receipt["not_run"]))
        self.assertEqual("NOT_RUN", receipt["external_evidence"])

    def test_two_distinct_local_http_stacks_are_actually_compared(self):
        class ChangedHandler(_Handler):
            body = b'{"code":500,"message":"changed"}'

        servers = [ThreadingHTTPServer(("127.0.0.1", 0), cls) for cls in (_Handler, ChangedHandler, _Handler)]
        threads = [threading.Thread(target=server.serve_forever, daemon=True) for server in servers]
        try:
            for thread in threads:
                thread.start()
            manifest = crit04_replay.build_manifest()
            manifest["cases"] = [manifest["cases"][0]]
            case_id = manifest["cases"][0]["id"]
            base = f"http://127.0.0.1:{servers[0].server_port}"
            target = f"http://127.0.0.1:{servers[1].server_port}"
            expected = {"expected_status": 200, "expected_body_sha256": hashlib.sha256(_Handler.body).hexdigest()}
            receipt = crit04_replay.replay(manifest, base, target, {case_id: expected}, False)
            self.assertEqual("FAIL", receipt["results"][0]["status"])
            self.assertEqual("BEHAVIOR_DRIFT", receipt["results"][0]["reason"])
            equivalent_target = f"http://127.0.0.1:{servers[2].server_port}"
            same = crit04_replay.replay(manifest, base, equivalent_target, {case_id: expected}, False)
            self.assertEqual("PASS", same["results"][0]["status"])
        finally:
            for server in servers:
                server.shutdown()
                server.server_close()
            for thread in threads:
                thread.join(timeout=2)

    def test_scc_detector_finds_a_cycle_and_reports_real_source_scope(self):
        self.assertEqual([["A", "B"]], crit02_scc_audit.tarjan({"A": {"B"}, "B": {"A"}}))
        report = crit02_scc_audit.audit()
        self.assertEqual("ZERO_STATIC_SCC", report["status"])
        self.assertEqual("NOT_RUN", report["runtime_startup"])
        self.assertGreater(report["resolved_edges"], 0)
        self.assertGreater(len(report["unresolved_edges"]), 0)

    def test_json_key_order_diagnostic_does_not_weaken_exact_oracle(self):
        class ReorderedHandler(_Handler):
            body = b'{"message":"stable","code":200}'

        servers = [ThreadingHTTPServer(("127.0.0.1", 0), cls) for cls in (_Handler, ReorderedHandler)]
        threads = [threading.Thread(target=server.serve_forever, daemon=True) for server in servers]
        try:
            for thread in threads:
                thread.start()
            manifest = crit04_replay.build_manifest()
            manifest["cases"] = [manifest["cases"][0]]
            case_id = manifest["cases"][0]["id"]
            urls = [f"http://127.0.0.1:{server.server_port}" for server in servers]
            fixture = {case_id: {"expected_status": 200,
                                "expected_body_sha256": hashlib.sha256(_Handler.body).hexdigest()}}
            receipt = crit04_replay.replay(manifest, urls[0], urls[1], fixture, False)
            result = receipt["results"][0]
            self.assertEqual("FAIL", result["status"])
            self.assertEqual(["BODY_BYTES"], result["difference_dimensions"])
            self.assertEqual(result["baseline"]["canonical_json_sha256"],
                             result["target"]["canonical_json_sha256"])
        finally:
            for server in servers:
                server.shutdown()
                server.server_close()
            for thread in threads:
                thread.join(timeout=2)

    def test_download_header_drift_fails_even_when_body_matches(self):
        class DownloadHandler(_Handler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Disposition", "attachment; filename=first.txt")
                self.end_headers()
                self.wfile.write(self.body)

        class ChangedHeaderHandler(DownloadHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Disposition", "attachment; filename=second.txt")
                self.end_headers()
                self.wfile.write(self.body)

        servers = [ThreadingHTTPServer(("127.0.0.1", 0), cls) for cls in (DownloadHandler, ChangedHeaderHandler)]
        threads = [threading.Thread(target=server.serve_forever, daemon=True) for server in servers]
        try:
            for thread in threads:
                thread.start()
            manifest = crit04_replay.build_manifest()
            manifest["cases"] = [manifest["cases"][0]]
            case_id = manifest["cases"][0]["id"]
            urls = [f"http://127.0.0.1:{server.server_port}" for server in servers]
            fixture = {case_id: {"expected_status": 200,
                                "expected_body_sha256": hashlib.sha256(_Handler.body).hexdigest()}}
            result = crit04_replay.replay(manifest, urls[0], urls[1], fixture, False)["results"][0]
            self.assertEqual("FAIL", result["status"])
            self.assertEqual(["CONTENT_DISPOSITION"], result["difference_dimensions"])
        finally:
            for server in servers:
                server.shutdown()
                server.server_close()
            for thread in threads:
                thread.join(timeout=2)

    def test_captured_unauthorized_business_code_is_valid_negative_oracle(self):
        class DeniedHandler(_Handler):
            body = b'{"code":401,"message":"unauthorized"}'

        servers = [ThreadingHTTPServer(("127.0.0.1", 0), DeniedHandler) for _ in range(2)]
        threads = [threading.Thread(target=server.serve_forever, daemon=True) for server in servers]
        try:
            for thread in threads:
                thread.start()
            manifest = crit04_replay.build_manifest()
            case = next(item for item in manifest["cases"] if item["auth_variant"] == "UNAUTHENTICATED")
            manifest["cases"] = [case]
            fixture = {"tenant": "tenant1", "expected_status": 200, "expected_json_code": 401,
                       "expected_body_sha256": hashlib.sha256(DeniedHandler.body).hexdigest()}
            urls = [f"http://127.0.0.1:{server.server_port}" for server in servers]
            receipt = crit04_replay.replay(manifest, urls[0], urls[1], {case["id"]: fixture}, False)
            self.assertEqual("PASS", receipt["results"][0]["status"])
            missing = crit04_replay.replay(manifest, urls[0], urls[1], {case["id"]: {"tenant": "tenant1"}}, False)
            self.assertEqual("BASELINE_ORACLE_MISSING", missing["results"][0]["reason"])
        finally:
            for server in servers:
                server.shutdown()
                server.server_close()
            for thread in threads:
                thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()

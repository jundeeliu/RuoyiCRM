#!/usr/bin/env python3
"""Source-bound RuoyiCRM HTTP replay inventory and fail-closed dual-run harness.

The manifest is a plan, not a Golden Master receipt. Use only disposable,
loopback-bound source and target stacks with independent MySQL/Redis data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAPPING = re.compile(r"@(Get|Post|Put|Delete|Patch|Request)Mapping(?:\((.*)\))?")
METHOD = re.compile(r"\b(?:public|protected)\s+(?:[\w<>, ?\[\].]+\s+)+(\w+)\s*\(")
PATH_VAR = re.compile(r"\{([^{}]+)\}")
MAX_RESPONSE = 2 * 1024 * 1024


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_inventory(root: Path = ROOT) -> dict:
    """Read actual controller mapping lines and Mapper XML source files."""
    endpoints = []
    for path in sorted(root.glob("ruoyi-*/src/main/java/**/controller/**/*.java")):
        lines = path.read_text(encoding="utf-8").splitlines()
        class_line = next((i for i, line in enumerate(lines) if re.search(r"\bclass\s+\w+", line)), None)
        if class_line is None:
            continue
        class_prefix = ""
        for line in lines[:class_line]:
            hit = MAPPING.search(line)
            if hit and hit.group(1) == "Request":
                paths = re.findall(r'"([^"\n]+)"', hit.group(2) or "")
                if len(paths) == 1:
                    class_prefix = paths[0]
        for i, line in enumerate(lines):
            hit = MAPPING.search(line)
            if not hit or i <= class_line:
                continue
            verb = hit.group(1).upper()
            if verb == "REQUEST":
                specified = re.search(r"RequestMethod\.(GET|POST|PUT|DELETE|PATCH)", hit.group(2) or "")
                verb = specified.group(1) if specified else "GET"
            paths = re.findall(r'"([^"\n]+)"', hit.group(2) or "")
            if not paths:
                paths = [""]
            signature = None
            for following in lines[i + 1 : min(len(lines), i + 16)]:
                signature = METHOD.search(following)
                if signature:
                    break
            if signature is None:
                raise ValueError(f"Cannot bind mapping to method: {path.relative_to(root)}:{i + 1}")
            permission = None
            for prior in reversed(lines[max(class_line, i - 5) : i]):
                match = re.search(r"@PreAuthorize\(\"([^\"]+)\"\)", prior)
                if match:
                    permission = match.group(1)
                    break
                if MAPPING.search(prior):
                    break
            for subpath in paths:
                full_path = "/" + "/".join(part for part in (class_prefix + "/" + subpath).split("/") if part)
                # `/system/user/` and `/system/user` are distinct under the
                # source and target MVC mappings. Preserve an explicit slash.
                if subpath.endswith("/") and not full_path.endswith("/"):
                    full_path += "/"
                endpoints.append({
                    "http_method": verb,
                    "path_template": full_path,
                    "controller": str(path.relative_to(root)),
                    "controller_line": i + 1,
                    "controller_sha256": digest(path.read_bytes()),
                    "java_method": signature.group(1),
                    "permission_expression": permission,
                })
    mapper_sources = []
    for path in sorted(root.glob("ruoyi-*/src/main/resources/mapper/**/*Mapper.xml")):
        source = path.read_text(encoding="utf-8")
        statements = [
            {"kind": match.group(1), "id": match.group(2), "line": source.count("\n", 0, match.start()) + 1}
            for match in re.finditer(r'<(select|insert|update|delete)\s+[^>]*?id="([^"]+)"', source)
        ]
        mapper_sources.append({"path": str(path.relative_to(root)), "sha256": digest(path.read_bytes()),
                               "statements": statements})
    return {"endpoints": endpoints, "mapper_sources": mapper_sources}


def build_manifest(root: Path = ROOT) -> dict:
    inventory = source_inventory(root)
    endpoints = inventory["endpoints"]
    if len(endpoints) < 139:
        raise ValueError(f"Only {len(endpoints)} source-bound endpoints; cannot build 150 cases")
    cases = []
    for endpoint in endpoints:
        case = dict(endpoint)
        case.update({"id": f"RUOYICRM-{len(cases) + 1:03d}", "auth_variant": "AUTHENTICATED"})
        cases.append(case)
    for endpoint in endpoints:
        if len(cases) >= 150:
            break
        if endpoint["permission_expression"] and endpoint["http_method"] == "GET":
            case = dict(endpoint)
            case.update({"id": f"RUOYICRM-{len(cases) + 1:03d}", "auth_variant": "UNAUTHENTICATED", "expected_status_class": "4xx"})
            cases.append(case)
    if len(cases) < 150:
        raise ValueError("Not enough permissioned GET endpoints for 150 source-bound cases")
    return {
        "schema": "ruoyicrm.crit04.replay-plan.v1",
        "source_revision": "d7423309",
        "evidence_status": "NOT_RUN",
        "execution_contract": "Dual-run only on isolated loopback source and target runtimes; compare status, content type, and exact body bytes.",
        "mapper_sources": inventory["mapper_sources"],
        "cases": cases[:150],
    }


def loopback_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"} or not parsed.port:
        raise ValueError("Only explicit http://localhost:<port> loopback runtimes are allowed")
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment or parsed.username or parsed.password:
        raise ValueError("Runtime URL must contain only scheme, loopback host, and port")
    return url.rstrip("/")


def invoke(base: str, case: dict, fixture: dict, token: str | None) -> dict:
    values = fixture.get("path_params", {})
    path = case["path_template"]
    for variable in PATH_VAR.findall(path):
        if variable not in values:
            raise ValueError(f"Missing path parameter {variable}")
        path = path.replace("{" + variable + "}", urllib.parse.quote(str(values[variable]), safe=""))
    query = urllib.parse.urlencode(fixture.get("query", {}), doseq=True)
    url = base + path + ("?" + query if query else "")
    headers = {"Accept": "application/json"}
    if "tenant" in fixture:
        if fixture["tenant"] not in {"tenant1", "tenant2"}:
            raise ValueError("Only disposable tenant1/tenant2 fixtures are allowed")
        headers["tenant"] = fixture["tenant"]
    if case["auth_variant"] == "AUTHENTICATED" and token:
        headers["Authorization"] = "Bearer " + token
    body = None
    if case["http_method"] != "GET":
        body = json.dumps(fixture["json"], sort_keys=True).encode()
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, headers=headers, method=case["http_method"])
    try:
        response = urllib.request.urlopen(request, timeout=8)
    except urllib.error.HTTPError as exc:
        response = exc
    with response:
        payload = response.read(MAX_RESPONSE + 1)
        if len(payload) > MAX_RESPONSE:
            raise ValueError("Response exceeds 2 MiB bound")
        try:
            parsed = json.loads(payload)
            json_code = parsed.get("code") if isinstance(parsed, dict) else None
            canonical_json_sha256 = digest(json.dumps(parsed, ensure_ascii=False, sort_keys=True,
                                                      separators=(",", ":")).encode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            json_code = None
            canonical_json_sha256 = None
        return {"status": response.status, "content_type": response.headers.get("Content-Type", ""),
                "content_disposition": response.headers.get("Content-Disposition"),
                "download_filename": response.headers.get("download-filename"),
                "body_sha256": digest(payload), "json_code": json_code,
                "canonical_json_sha256": canonical_json_sha256}


def replay(manifest: dict, baseline: str | None, target: str | None, fixtures: dict, allow_writes: bool) -> dict:
    if baseline and target and baseline == target:
        raise ValueError("Baseline and target must be distinct runtimes")
    results = []
    mapper_drift = any(
        not (ROOT / mapper["path"]).is_file()
        or digest((ROOT / mapper["path"]).read_bytes()) != mapper["sha256"]
        for mapper in manifest["mapper_sources"]
    )
    for case in manifest["cases"]:
        result = {"id": case["id"], "status": "NOT_RUN", "reason": None}
        path = ROOT / case["controller"]
        if not path.is_file() or digest(path.read_bytes()) != case["controller_sha256"]:
            result["reason"] = "SOURCE_DRIFT"
        elif mapper_drift:
            result["reason"] = "MAPPER_SOURCE_DRIFT"
        elif not baseline or not target:
            result["reason"] = "RUNTIME_UNAVAILABLE"
        elif case["http_method"] != "GET" and not allow_writes:
            result["reason"] = "WRITE_ISOLATION_NOT_AUTHORIZED"
        elif case["id"] not in fixtures:
            result["reason"] = "FIXTURE_MISSING"
        else:
            fixture = fixtures[case["id"]]
            if "expected_status" not in fixture or "expected_body_sha256" not in fixture:
                result["reason"] = "BASELINE_ORACLE_MISSING"
                results.append(result)
                continue
            if (case["auth_variant"] == "AUTHENTICATED" and case["permission_expression"]
                    and (not os.getenv("CRIT04_BASELINE_TOKEN") or not os.getenv("CRIT04_TARGET_TOKEN"))):
                result["reason"] = "AUTH_TOKEN_MISSING"
                results.append(result)
                continue
            try:
                if case["http_method"] != "GET" and "json" not in fixture:
                    raise ValueError("Write case requires explicit JSON fixture")
                left = invoke(baseline, case, fixture, os.getenv("CRIT04_BASELINE_TOKEN"))
                right = invoke(target, case, fixture, os.getenv("CRIT04_TARGET_TOKEN"))
                result["baseline"] = left
                result["target"] = right
                if (left["status"] != fixture["expected_status"]
                        or ("expected_body_sha256" in fixture and left["body_sha256"] != fixture["expected_body_sha256"])
                        or ("expected_json_code" in fixture and left["json_code"] != fixture["expected_json_code"])):
                    result.update(status="NOT_RUN", reason="BASELINE_FIXTURE_INVALID")
                elif (case.get("expected_status_class") == "4xx" and
                      not (400 <= left["status"] < 500 or
                           (left["status"] == 200 and left["json_code"] in {401, 403}))):
                    result.update(status="FAIL", reason="BASELINE_AUTH_CONTRACT")
                elif (case["auth_variant"] == "AUTHENTICATED" and
                      (not 200 <= left["status"] < 300 or
                       (left["json_code"] is not None and left["json_code"] != 200))):
                    result.update(status="NOT_RUN", reason="BASELINE_NOT_SUCCESSFUL")
                elif left == right:
                    result.update(status="PASS", reason=None)
                else:
                    result.update(status="FAIL", reason="BEHAVIOR_DRIFT")
                    result["difference_dimensions"] = [name for name, differs in (
                        ("HTTP_STATUS", left["status"] != right["status"]),
                        ("CONTENT_TYPE", left["content_type"] != right["content_type"]),
                        ("CONTENT_DISPOSITION", left["content_disposition"] != right["content_disposition"]),
                        ("DOWNLOAD_FILENAME", left["download_filename"] != right["download_filename"]),
                        ("BODY_BYTES", left["body_sha256"] != right["body_sha256"]),
                        ("JSON_VALUES", left["canonical_json_sha256"] != right["canonical_json_sha256"]),
                    ) if differs]
            except (OSError, ValueError, KeyError, urllib.error.URLError) as exc:
                result["reason"] = type(exc).__name__
        results.append(result)
    passed = sum(item["status"] == "PASS" for item in results)
    return {
        "schema": "ruoyicrm.crit04.replay-receipt.v1",
        "status": "LOCAL_EXECUTED_SELF_ATTESTED" if passed == len(results) == 150 else "NOT_RUN_OR_FAILED",
        "planned": len(results), "passed": passed,
        "failed": sum(item["status"] == "FAIL" for item in results),
        "not_run": sum(item["status"] == "NOT_RUN" for item in results),
        "external_evidence": "NOT_RUN", "certification": "NOT_CERTIFIED",
        "comparison_scope": "HTTP status, Content-Type, Content-Disposition, download-filename, and exact body bytes; database and Redis state NOT_RUN",
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["generate", "check", "capture", "replay"])
    parser.add_argument("--manifest", type=Path, default=ROOT / "docs" / "crit04" / "ruoyicrm-150.json")
    parser.add_argument("--baseline")
    parser.add_argument("--target")
    parser.add_argument("--fixtures", type=Path)
    parser.add_argument("--allow-writes", action="store_true")
    parser.add_argument("--case-id")
    parser.add_argument("--baseline-source-root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.mode == "generate":
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(build_manifest(), ensure_ascii=False, indent=2) + "\n")
        print(args.manifest)
        return 0
    manifest = json.loads(args.manifest.read_text())
    if args.mode == "check":
        if manifest != build_manifest():
            print("Manifest drift detected", file=sys.stderr)
            return 1
        print(f"{len(manifest['cases'])} source-bound planned cases; runtime evidence NOT_RUN")
        return 0
    baseline = loopback_url(args.baseline) if args.baseline else None
    target = loopback_url(args.target) if args.target else None
    if baseline and target and baseline == target:
        parser.error("Baseline and target must be distinct loopback runtimes")
    fixtures = json.loads(args.fixtures.read_text()) if args.fixtures else {}
    if args.mode == "capture":
        if not baseline or not args.case_id or not args.baseline_source_root:
            parser.error("capture requires --baseline, --case-id, and --baseline-source-root")
        case = next((item for item in manifest["cases"] if item["id"] == args.case_id), None)
        if case is None:
            parser.error("Unknown case ID")
        if case["http_method"] != "GET" and not args.allow_writes:
            parser.error("Non-GET baseline capture requires explicit --allow-writes")
        if case["auth_variant"] == "AUTHENTICATED" and case["permission_expression"] and not os.getenv("CRIT04_BASELINE_TOKEN"):
            parser.error("Protected baseline capture requires CRIT04_BASELINE_TOKEN")
        fixture = fixtures.get(args.case_id)
        if fixture is None:
            parser.error("Case fixture is required")
        baseline_root = args.baseline_source_root.resolve()
        revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=baseline_root,
                                  capture_output=True, text=True, check=True).stdout.strip()
        if not revision.startswith("d7423309"):
            parser.error("Baseline source root is not d7423309")
        baseline_matches = [item for item in source_inventory(baseline_root)["endpoints"]
                            if all(item[key] == case[key] for key in
                                   ("http_method", "path_template", "java_method", "permission_expression"))]
        if len(baseline_matches) != 1:
            parser.error("Case has no unique matching baseline route")
        observed = invoke(baseline, case, fixture, os.getenv("CRIT04_BASELINE_TOKEN"))
        receipt = {
            "schema": "ruoyicrm.crit04.baseline-oracle.v1",
            "case_id": args.case_id,
            "baseline_source_revision": revision,
            "baseline_controller_sha256": baseline_matches[0]["controller_sha256"],
            "baseline_controller_line": baseline_matches[0]["controller_line"],
            "route": {key: case[key] for key in ("http_method", "path_template", "java_method", "permission_expression")},
            "observation": observed,
            "fixture_expectation": {"expected_status": observed["status"],
                                    "expected_body_sha256": observed["body_sha256"],
                                    **({"expected_json_code": observed["json_code"]} if observed["json_code"] is not None else {})},
            "status": "LOCAL_BASELINE_CAPTURED",
            "external_evidence": "NOT_RUN", "certification": "NOT_CERTIFIED",
        }
        output = json.dumps(receipt, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output)
        else:
            print(output)
        return 0
    receipt = replay(manifest, baseline, target, fixtures, args.allow_writes)
    output = json.dumps(receipt, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output)
    else:
        print(output)
    return 0 if receipt["passed"] == 150 else 2


if __name__ == "__main__":
    raise SystemExit(main())

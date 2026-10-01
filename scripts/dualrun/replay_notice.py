"""One bounded disposable-only RUOYICRM-059 write replay with row reconciliation."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

from .fence import FenceError, authorize_write


class ReplayError(ValueError):
    pass


def notice_fixture(file: Path):
    document = json.loads(file.read_text())
    matches = [item for item in document.get("fixtures", []) if item.get("id") == "RUOYICRM-059"]
    if len(matches) != 1:
        raise ReplayError("exact notice fixture missing")
    case = matches[0]
    body = case["request"]["json"]
    title = body.get("noticeTitle")
    if (case.get("http_method") != "POST" or case.get("path_template") != "/system/notice"
            or case.get("tenant") != "tenant1" or type(body) is not dict
            or not isinstance(title, str) or not re.fullmatch(r"CRIT04 [a-z0-9]+ notice", title)
            or body.get("noticeType") != "1" or body.get("status") != "0"
            or not isinstance(body.get("noticeContent"), str)
            or not body["noticeContent"].startswith("Synthetic disposable replay notice ")):
        raise ReplayError("notice fixture is outside synthetic allowlist")
    return body


def notice_rows(state_path: Path, title: str):
    runtime = Path(state_path).resolve(strict=True).parent
    state = json.loads((runtime / "state.json").read_text())
    port = state["mysql_port"]
    client = runtime / "mysql-app.cnf"
    if type(port) is not int or not 1024 <= port <= 65535 or client.is_symlink() or client.stat().st_mode & 0o077:
        raise ReplayError("private disposable MySQL binding invalid")
    # title has already passed a restrictive character allowlist.
    sql = ("SELECT notice_id,notice_title,notice_type,HEX(notice_content),status,create_by,"
           "create_time,update_by,update_time,remark "
           "FROM sys_notice WHERE notice_title='" + title + "' ORDER BY notice_id")
    result = subprocess.run(["mysql", f"--defaults-extra-file={client}", "--protocol=TCP", "-h", "127.0.0.1",
                             "-P", str(port), "-D", "rycrm-tenant-1", "-N", "-B", "-e", sql],
                            capture_output=True, text=True, timeout=10, check=False)
    if result.returncode:
        raise ReplayError("bounded notice row query failed")
    rows = [line.split("\t") for line in result.stdout.splitlines()]
    if any(len(row) != 10 for row in rows):
        raise ReplayError("notice row shape invalid")
    return rows


def canonical_notice(row):
    """Preserve every column except generated PK and creation timestamp values."""
    if len(row) != 10 or not re.fullmatch(r"[1-9][0-9]*", row[0]):
        raise ReplayError("generated notice ID is invalid")
    try:
        dt.datetime.strptime(row[6], "%Y-%m-%d %H:%M:%S")
    except ValueError as exc:
        raise ReplayError("generated notice creation time is invalid") from exc
    return ["<generated-positive-id>", *row[1:6], "<generated-datetime>", *row[7:]]


def notice_counts(state_path: Path):
    runtime = Path(state_path).resolve(strict=True).parent
    state = json.loads((runtime / "state.json").read_text())
    port = state["mysql_port"]
    client = runtime / "mysql-app.cnf"
    if type(port) is not int or not 1024 <= port <= 65535 or client.is_symlink() or client.stat().st_mode & 0o077:
        raise ReplayError("private disposable MySQL binding invalid")
    counts = {}
    for database in ("rycrm-tenant-1", "rycrm-tenant-2"):
        result = subprocess.run(["mysql", f"--defaults-extra-file={client}", "--protocol=TCP", "-h", "127.0.0.1",
                                 "-P", str(port), "-D", database, "-N", "-B", "-e", "SELECT COUNT(*) FROM sys_notice"],
                                capture_output=True, text=True, timeout=10, check=False)
        value = result.stdout.strip()
        if result.returncode or not re.fullmatch(r"[0-9]+", value):
            raise ReplayError("notice table count query failed")
        counts[database] = int(value)
    return counts


def storage_metadata(state_path: Path):
    runtime = Path(state_path).resolve(strict=True).parent
    state = json.loads((runtime / "state.json").read_text())
    port = state["mysql_port"]
    client = runtime / "mysql-app.cnf"
    if type(port) is not int or not 1024 <= port <= 65535 or client.is_symlink() or client.stat().st_mode & 0o077:
        raise ReplayError("private disposable MySQL binding invalid")
    sql = ("SELECT VERSION(),@@character_set_server,@@time_zone,@@system_time_zone,"
           "(SELECT ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA='rycrm-tenant-1' AND TABLE_NAME='sys_notice')")
    result = subprocess.run(["mysql", f"--defaults-extra-file={client}", "--protocol=TCP", "-h", "127.0.0.1",
                             "-P", str(port), "-D", "rycrm-tenant-1", "-N", "-B", "-e", sql],
                            capture_output=True, text=True, timeout=10, check=False)
    fields = result.stdout.strip().split("\t")
    if result.returncode or len(fields) != 5 or fields[4] != "InnoDB" or any(not field for field in fields):
        raise ReplayError("MySQL engine, version, charset or timezone unavailable")
    return dict(zip(("mysql_version", "server_charset", "session_timezone", "system_timezone", "table_engine"), fields))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise ReplayError("HTTP redirect is outside authorized replay URL")


def post_notice(base: str, body: dict, token: str):
    if not token or len(token) > 8192:
        raise ReplayError("synthetic authorization token missing")
    request = urllib.request.Request(base + "/system/notice",
                                     data=json.dumps(body, sort_keys=True).encode("utf-8"),
                                     headers={"Accept": "application/json", "Content-Type": "application/json",
                                              "tenant": "tenant1", "Authorization": "Bearer " + token},
                                     method="POST")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        response = opener.open(request, timeout=8)
    except urllib.error.HTTPError as exc:
        response = exc
    with response:
        payload = response.read(2_000_001)
        if len(payload) > 2_000_000:
            raise ReplayError("HTTP response exceeds bound")
        content_type = response.headers.get("Content-Type", "")
        try:
            body_json = json.loads(payload)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ReplayError("HTTP response is not JSON") from exc
        return {"status": response.status, "content_type": content_type,
                "body_sha256": hashlib.sha256(payload).hexdigest(),
                "json_code": body_json.get("code") if isinstance(body_json, dict) else None}


def run(args):
    body = notice_fixture(args.fixture)
    title = body["noticeTitle"]
    source_token = os.environ.get("CRIT04_BASELINE_TOKEN")
    target_token = os.environ.get("CRIT04_TARGET_TOKEN")
    if not source_token or not target_token:
        raise ReplayError("synthetic token environment missing")
    settings = (args.source_state, args.target_state, args.source_app, args.target_app,
                args.source_url, args.target_url, "POST", "/system/notice",
                args.source_snapshot, args.target_snapshot)
    result = {"schema": "ruoyicrm.crit04.notice-write-replay.v1", "case_id": "RUOYICRM-059",
              "status": "NOT_RUN", "source_revision": "d7423309", "external_evidence": "NOT_RUN",
              "certification": "NOT_CERTIFIED"}
    result["fence"] = authorize_write(*settings)
    source_before = notice_rows(args.source_state, title)
    target_before = notice_rows(args.target_state, title)
    if source_before or target_before:
        raise ReplayError("synthetic notice already exists before replay")
    result["prewrite_rows"] = {"source": 0, "target": 0}
    source_storage = storage_metadata(args.source_state)
    target_storage = storage_metadata(args.target_state)
    result["storage_metadata"] = {"source": source_storage, "target": target_storage}
    if source_storage != target_storage:
        raise ReplayError("source and target storage metadata differ")
    source_counts_before = notice_counts(args.source_state)
    target_counts_before = notice_counts(args.target_state)
    result["prewrite_table_counts"] = {"source": source_counts_before, "target": target_counts_before}
    # Recheck immediately before each side; an HTTP call is never made on a failed gate.
    try:
        authorize_write(*settings)
        result["write_attempted"] = "SOURCE"
        source = post_notice(args.source_url, body, source_token)
        result["baseline"] = source
        result["source_rows"] = notice_rows(args.source_state, title)
        result["source_table_counts"] = notice_counts(args.source_state)
        if (source["status"] != 200 or source["json_code"] != 200 or len(result["source_rows"]) != 1
                or result["source_table_counts"]["rycrm-tenant-1"] != source_counts_before["rycrm-tenant-1"] + 1
                or result["source_table_counts"]["rycrm-tenant-2"] != source_counts_before["rycrm-tenant-2"]):
            result.update(status="FAIL", reason="BASELINE_WRITE_OR_ROW_INVALID")
            return result
        authorize_write(*settings)
        result["write_attempted"] = "BOTH"
        target = post_notice(args.target_url, body, target_token)
        result["target"] = target
        result["target_rows"] = notice_rows(args.target_state, title)
        result["target_table_counts"] = notice_counts(args.target_state)
    except (FenceError, ReplayError, OSError, ValueError, KeyError, TypeError) as exc:
        result.update(status="FAIL", reason="WRITE_ATTEMPT_INDETERMINATE", error_type=type(exc).__name__,
                      error_detail=str(exc) if type(exc) is FenceError else "NON_FENCE_ERROR")
        return result
    expected_prefix = ["<generated-positive-id>", title, "1", body["noticeContent"].encode().hex().upper(), "0"]
    try:
        source_canonical = canonical_notice(result["source_rows"][0])
        target_canonical = canonical_notice(result["target_rows"][0]) if len(result["target_rows"]) == 1 else None
    except ReplayError as exc:
        result.update(status="FAIL", reason="GENERATED_COLUMN_INVALID", error_type=type(exc).__name__)
        return result
    result["canonical_rows"] = {"source": source_canonical, "target": target_canonical}
    if (target["status"] == 200 and target["json_code"] == 200
            and len(result["target_rows"]) == 1 and source_canonical == target_canonical
            and source_canonical[:5] == expected_prefix
            and result["target_table_counts"]["rycrm-tenant-1"] == target_counts_before["rycrm-tenant-1"] + 1
            and result["target_table_counts"]["rycrm-tenant-2"] == target_counts_before["rycrm-tenant-2"]
            and source == target):
        result["status"] = "PASS"
    else:
        result.update(status="FAIL", reason="HTTP_OR_BUSINESS_ROW_DRIFT")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source-state", "target-state", "source-app", "target-app", "source-snapshot", "target-snapshot", "fixture"):
        parser.add_argument("--" + name, required=True, type=Path)
    for name in ("source-url", "target-url"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = run(args)
    except (FenceError, ReplayError, OSError, ValueError, KeyError, TypeError) as exc:
        result = {"schema": "ruoyicrm.crit04.notice-write-replay.v1", "case_id": "RUOYICRM-059",
                  "status": "NOT_RUN", "reason": type(exc).__name__, "external_evidence": "NOT_RUN",
                  "certification": "NOT_CERTIFIED"}
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "case_id": result["case_id"],
                      "reason": result.get("reason")}))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())

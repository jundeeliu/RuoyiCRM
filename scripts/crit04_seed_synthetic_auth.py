#!/usr/bin/env python3
"""Seed one disposable, synthetic admin in two CRIT-10 tenant databases.

This is only for isolated, loopback-bound local replay stacks. Source sample
INSERTs, real accounts, and production credentials are never read or copied.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import subprocess
from pathlib import Path


def read_stack(path: Path) -> dict:
    state = json.loads(path.read_text())
    runtime = Path(state["runtime_dir"]).resolve()
    if path.resolve() != runtime / "state.json" or not runtime.name.startswith("ruoyicrm-crit10-"):
        raise ValueError("State must be inside its dedicated CRIT-10 runtime")
    if not state["project"].startswith("ruoyicrm-crit10-"):
        raise ValueError("Unexpected Compose project")
    if not (1 <= int(state["mysql_port"]) <= 65535):
        raise ValueError("Invalid loopback MySQL port")
    return state


def mysql(state: dict, sql: str) -> str:
    runtime = Path(state["runtime_dir"])
    cmd = ["mysql", f"--defaults-extra-file={runtime / 'mysql-app.cnf'}", "--protocol=TCP",
           "-h", "127.0.0.1", "-P", str(state["mysql_port"]), "-D", "rycrm-tenant-1", "-N", "-B"]
    proc = subprocess.run(cmd, input=sql, capture_output=True, text=True, timeout=15)
    if proc.returncode:
        # MySQL diagnostics can contain attempted statement values.
        raise RuntimeError(f"MySQL fixture operation failed (exit {proc.returncode})")
    return proc.stdout.strip()


def write_private(path: Path, value: dict) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as out:
        json.dump(value, out, indent=2)
        out.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-state", required=True, type=Path)
    parser.add_argument("--target-state", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    baseline, target = read_stack(args.baseline_state), read_stack(args.target_state)
    if baseline["project"] == target["project"] or baseline["mysql_port"] == target["mysql_port"]:
        parser.error("Source and target must be distinct disposable stacks")
    secret_file = Path(target["runtime_dir"]) / "synthetic-auth-private.json"
    if secret_file.exists() or args.receipt.exists():
        parser.error("Fixture material or receipt already exists; refusing to reseed")
    preflight = "SELECT (SELECT COUNT(*) FROM sys_user)+(SELECT COUNT(*) FROM sys_role)+(SELECT COUNT(*) FROM sys_user_role)+(SELECT COUNT(*) FROM sys_dept);"
    for stack in (baseline, target):
        if mysql(stack, preflight) != "0":
            parser.error("Auth fixture tables are not empty; refusing to overwrite existing data")

    username = "gm_" + secrets.token_hex(4)
    password = secrets.token_urlsafe(32)
    encoded = subprocess.run(["htpasswd", "-nBiC", "10", username], input=password + "\n",
                             capture_output=True, text=True, timeout=15, check=True).stdout.strip()
    prefix, password_hash = encoded.split(":", 1)
    if prefix != username or not re.fullmatch(r"\$2[aby]\$10\$[./A-Za-z0-9]{53}", password_hash):
        raise ValueError("BCrypt fixture encoder returned an unexpected format")
    if not re.fullmatch(r"gm_[0-9a-f]{8}", username):
        raise ValueError("Synthetic username is invalid")
    statements = f"""
START TRANSACTION;
INSERT INTO sys_dept (dept_id,parent_id,ancestors,dept_name,order_num,status,del_flag,create_by,create_time)
VALUES (1,0,'0','Synthetic Replay',1,'0','0','synthetic','2020-01-01 00:00:00');
INSERT INTO sys_role (role_id,role_name,role_key,role_sort,data_scope,status,del_flag,create_by,create_time)
VALUES (1,'Synthetic Replay Admin','admin',1,'1','0','0','synthetic','2020-01-01 00:00:00');
INSERT INTO sys_user (user_id,dept_id,user_name,nick_name,user_type,email,phonenumber,sex,avatar,password,status,del_flag,create_by,create_time)
VALUES (1,1,'{username}','Synthetic Replay','00','','','0','','{password_hash}','0','0','synthetic','2020-01-01 00:00:00');
INSERT INTO sys_user_role (user_id,role_id) VALUES (1,1);
COMMIT;
"""
    completed = []
    for stack in (baseline, target):
        mysql(stack, statements)
        if mysql(stack, preflight) != "4":
            raise RuntimeError("Synthetic auth fixture row count mismatch")
        completed.append(stack["project"])
    write_private(secret_file, {"username": username, "password": password, "tenant": "tenant1"})
    receipt = {
        "schema": "ruoyicrm.crit04.synthetic-auth-seed.v1",
        "status": "LOCAL_SYNTHETIC_FIXTURE_SEEDED",
        "baseline_project": baseline["project"], "target_project": target["project"],
        "tenant": "tenant1", "synthetic_username": username,
        "tables": ["sys_dept", "sys_role", "sys_user", "sys_user_role"],
        "rows_per_stack": 4, "completed_projects": completed,
        "sample_inserts_used": False, "external_evidence": "NOT_RUN", "certification": "NOT_CERTIFIED",
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
    print("Synthetic auth fixture seeded in two disposable tenant1 databases; private material kept outside repository")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

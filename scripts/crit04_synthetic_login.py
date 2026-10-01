#!/usr/bin/env python3
"""Get disposable source/target login tokens without storing their bytes in Git."""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

from crit04_replay import loopback_url
from crit04_seed_synthetic_auth import mysql, read_stack, write_private


def freeze_synthetic_login_date(state: dict, username: str) -> None:
    """Fix only the generated user's volatile login date on a disposable DB."""
    if not re.fullmatch(r"gm_[0-9a-f]{8}", username):
        raise ValueError("Unexpected synthetic username")
    observed = mysql(state, f"UPDATE sys_user SET login_date='2020-01-01 00:00:00' "
                           f"WHERE user_id=1 AND user_name='{username}'; SELECT ROW_COUNT();")
    if observed != "1":
        raise RuntimeError("Synthetic login date update did not touch exactly one user")


def login(state: dict, url: str, material: dict, *, legacy: bool) -> tuple[dict, str | None]:
    runtime = Path(state["runtime_dir"])
    code = secrets.token_hex(4).upper()
    uuid = secrets.token_hex(16)
    key = "captcha_codes:" + uuid
    value = json.dumps(code) if legacy else json.dumps(
        {"version": 1, "kind": "string", "payload": code}, separators=(",", ":")
    )
    redis_env = {**os.environ, "REDISCLI_AUTH": (runtime / "redis-password").read_text().strip()}
    redis = ["redis-cli", "-h", "127.0.0.1", "-p", str(state["redis_port"]), "--no-auth-warning"]
    result = subprocess.run(redis + ["-x", "SET", key], input=value.encode(), capture_output=True,
                            env=redis_env, timeout=5)
    if result.returncode or result.stdout.strip() != b"OK":
        raise RuntimeError("Disposable Redis captcha seed failed")
    result = subprocess.run(redis + ["EXPIRE", key, "180"], capture_output=True, env=redis_env, timeout=5)
    if result.returncode or result.stdout.strip() != b"1":
        raise RuntimeError("Disposable Redis captcha expiry failed")
    request = urllib.request.Request(url + "/login", method="POST",
        data=json.dumps({"username": material["username"], "password": material["password"],
                         "code": code, "uuid": uuid}).encode(),
        headers={"Content-Type": "application/json", "tenant": "tenant1"})
    try:
        response = urllib.request.urlopen(request, timeout=8)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        body = response.read(2 * 1024 * 1024 + 1)
        if len(body) > 2 * 1024 * 1024:
            raise ValueError("Login response exceeds bound")
        data = json.loads(body)
        token = data.get("token")
        return {"http_status": response.status, "json_code": data.get("code"),
                "token_present": isinstance(token, str) and bool(token)}, token


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-state", required=True, type=Path)
    parser.add_argument("--target-state", required=True, type=Path)
    parser.add_argument("--baseline-http", required=True)
    parser.add_argument("--target-http", required=True)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--freeze-login-date", action="store_true",
                        help="Set the disposable synthetic user's login date before and after login")
    args = parser.parse_args()
    baseline, target = read_stack(args.baseline_state), read_stack(args.target_state)
    left, right = loopback_url(args.baseline_http), loopback_url(args.target_http)
    if baseline["project"] == target["project"] or left == right:
        parser.error("Source and target runtimes must be distinct")
    runtime = Path(target["runtime_dir"])
    material = json.loads((runtime / "synthetic-auth-private.json").read_text())
    if args.freeze_login_date:
        for stack in (baseline, target):
            freeze_synthetic_login_date(stack, material["username"])
    observations, tokens = {}, {}
    for label, stack, url, legacy in (("baseline", baseline, left, True),
                                      ("target", target, right, False)):
        observation, token = login(stack, url, material, legacy=legacy)
        observations[label] = observation
        if token:
            tokens[label] = token
    if args.freeze_login_date:
        for stack in (baseline, target):
            freeze_synthetic_login_date(stack, material["username"])
    private = runtime / "synthetic-tokens-private.json"
    if private.exists():
        if private.stat().st_mode & 0o077:
            raise ValueError("Existing private token file has unsafe permissions")
        private.unlink()
    write_private(private, tokens)
    receipt = {"schema": "ruoyicrm.crit04.synthetic-login.v1", "status":
               "LOCAL_BOTH_TOKENS_ISSUED" if len(tokens) == 2 else "BLOCKED_TARGET_OR_BASELINE_LOGIN",
               "observations": observations, "tokens_saved_in_repository": False,
               "synthetic_login_date_fixture": "2020-01-01 00:00:00" if args.freeze_login_date else None,
               "external_evidence": "NOT_RUN", "certification": "NOT_CERTIFIED"}
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    return 0 if len(tokens) == 2 else 2


if __name__ == "__main__":
    raise SystemExit(main())

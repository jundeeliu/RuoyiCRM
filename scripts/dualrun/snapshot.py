"""Capture private, disposable CRIT-10 pre-case backups without replaying writes."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path

from .fence import FenceError, stack_identity, verify_snapshot, verify_tenant_urls


def _run(command, *, stdout=None, env=None):
    try:
        result = subprocess.run(command, stdout=stdout if stdout is not None else subprocess.DEVNULL,
                                stderr=subprocess.PIPE, env=env, timeout=120, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise FenceError("disposable backup command failed") from exc
    if result.returncode:
        # stderr can contain credential-bearing connection details; keep it private.
        raise FenceError("disposable backup command failed")


def _private_file(path: Path):
    if path.is_symlink() or not path.is_file() or path.stat().st_uid != os.getuid() or path.stat().st_mode & 0o077:
        raise FenceError("backup credential file is not private")


def _metadata(path: Path):
    size = path.stat().st_size
    if not 1 <= size <= 100_000_000:
        raise FenceError("backup artifact size invalid")
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"file": path.name, "bytes": size, "sha256": digest}


def capture(state_path: Path, method: str, path: str, *, runner=None, now=None):
    """Create one short-lived per-case receipt; previous receipts are invalidated first."""
    if method not in {"POST", "PUT", "PATCH", "DELETE"} or not isinstance(path, str) or not re.fullmatch(r"/[A-Za-z0-9/_-]+", path):
        raise FenceError("write method/path invalid")
    stack = stack_identity(state_path, now=now)
    verify_tenant_urls(stack)
    runtime = Path(stack["runtime_dir"])
    for name in ("mysql-app.cnf", "redis-password"):
        _private_file(runtime / name)
    receipt_path = runtime / "prewrite-snapshot.json"
    receipt_path.unlink(missing_ok=True)
    nonce = uuid.uuid4().hex
    mysql_tmp = runtime / (".prewrite-mysql-" + nonce + ".sql")
    redis_tmp = runtime / (".prewrite-redis-" + nonce + ".rdb")
    mysql_out = runtime / "prewrite-mysql.sql"
    redis_out = runtime / "prewrite-redis.rdb"
    # Old backups cannot be mistaken for the new case if either capture fails.
    mysql_out.unlink(missing_ok=True)
    redis_out.unlink(missing_ok=True)
    execute = runner or _run
    try:
        fd = os.open(mysql_tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as stream:
            execute(["mysqldump", f"--defaults-extra-file={runtime / 'mysql-app.cnf'}", "--protocol=TCP",
                     "-h", "127.0.0.1", "-P", str(stack["ports"]["mysql"]), "--single-transaction",
                     "--quick", "--routines", "--triggers", "--no-tablespaces", "--set-gtid-purged=OFF",
                     "--databases", "rycrm-master", "rycrm-tenant-1", "rycrm-tenant-2"], stdout=stream)
        with mysql_tmp.open("rb") as stream:
            if stream.read(13) != b"-- MySQL dump":
                raise FenceError("MySQL backup header invalid")
        redis_env = os.environ.copy()
        redis_env["REDISCLI_AUTH"] = (runtime / "redis-password").read_text().strip()
        old_umask = os.umask(0o077)
        try:
            execute(["redis-cli", "-h", "127.0.0.1", "-p", str(stack["ports"]["redis"]),
                     "--no-auth-warning", "--rdb", str(redis_tmp)], env=redis_env)
        finally:
            os.umask(old_umask)
            redis_env.pop("REDISCLI_AUTH", None)
        _private_file(redis_tmp)
        with redis_tmp.open("rb") as stream:
            if stream.read(5) != b"REDIS":
                raise FenceError("Redis backup header invalid")
        mysql_tmp.replace(mysql_out)
        redis_tmp.replace(redis_out)
        captured = dt.datetime.fromtimestamp(now, dt.timezone.utc) if now is not None else dt.datetime.now(dt.timezone.utc)
        receipt = {"schema": "ruoyicrm.crit04.prewrite-snapshot.v1", "project": stack["project"],
                   "method": method, "path": path, "containers": stack["containers"],
                   "volumes": stack["volumes"], "captured_at": captured.isoformat(),
                   "mysql": _metadata(mysql_out), "redis": _metadata(redis_out)}
        fd = os.open(receipt_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as stream:
            json.dump(receipt, stream, sort_keys=True)
            stream.write("\n")
        verify_snapshot(receipt_path, stack, method, path, now=now)
        return receipt_path
    except Exception:
        receipt_path.unlink(missing_ok=True)
        mysql_out.unlink(missing_ok=True)
        redis_out.unlink(missing_ok=True)
        raise
    finally:
        mysql_tmp.unlink(missing_ok=True)
        redis_tmp.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Capture one private disposable CRIT-10 pre-case backup")
    parser.add_argument("capture", choices=["capture"])
    parser.add_argument("--state", required=True, type=Path)
    parser.add_argument("--method", required=True)
    parser.add_argument("--path", required=True)
    args = parser.parse_args(argv)
    try:
        receipt = capture(args.state, args.method, args.path)
    except (FenceError, FileNotFoundError, ValueError):
        print("BLOCKED: pre-case backup not captured", file=sys.stderr)
        return 2
    print(receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Disposable loopback MySQL 8.4 + Redis 7 stack for CRIT-10 preparation.

Only allowlisted DDL is extracted from repository SQL. Sample INSERTs, DROP
statements, credential-bearing tenant rows, and user records are never loaded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "deploy/crit10/compose.yaml"
SOURCE_FILES = ("database.sql", "rycrm-master.sql", "rycrm-tenant.sql", "quartz.sql", "update_20220311.sql")
DATABASES = ("rycrm-master", "rycrm-tenant-1", "rycrm-tenant-2")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def split_sql(source: str) -> list[str]:
    """Split MySQL statements without treating quoted semicolons as delimiters."""
    statements = []
    buffer = []
    quote = None
    line_comment = False
    block_comment = False
    i = 0
    while i < len(source):
        char = source[i]
        next_char = source[i + 1] if i + 1 < len(source) else ""
        if line_comment:
            if char == "\n":
                line_comment = False
                buffer.append("\n")
            i += 1
            continue
        if block_comment:
            if char == "*" and next_char == "/":
                block_comment = False
                i += 2
            else:
                i += 1
            continue
        if quote:
            buffer.append(char)
            if char == "\\" and i + 1 < len(source):
                buffer.append(next_char)
                i += 2
                continue
            if char == quote:
                if next_char == quote and quote in {"'", '"', "`"}:
                    buffer.append(next_char)
                    i += 2
                    continue
                quote = None
            i += 1
            continue
        if char == "-" and next_char == "-" and (i + 2 == len(source) or source[i + 2].isspace()):
            line_comment = True
            i += 2
            continue
        if char == "#":
            line_comment = True
            i += 1
            continue
        if char == "/" and next_char == "*":
            block_comment = True
            i += 2
            continue
        if char in {"'", '"', "`"}:
            quote = char
            buffer.append(char)
            i += 1
            continue
        if char == ";":
            statement = "".join(buffer).strip()
            if statement:
                statements.append(statement)
            buffer = []
        else:
            buffer.append(char)
        i += 1
    if quote or block_comment:
        raise ValueError("Unterminated SQL quote or comment")
    if "".join(buffer).strip():
        raise ValueError("SQL has a non-terminated trailing statement")
    return statements


def extract_schema(root: Path = ROOT) -> tuple[dict, dict]:
    sql_dir = root / "sql"
    source_hashes = {name: sha256((sql_dir / name).read_bytes()) for name in SOURCE_FILES}
    database_statements = split_sql((sql_dir / "database.sql").read_text(encoding="utf-8"))
    found_databases = []
    for statement in database_statements:
        match = re.fullmatch(r"CREATE DATABASE IF NOT EXISTS `([^`]+)` DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_general_ci", statement, re.I)
        if not match:
            raise ValueError(f"Unsupported database DDL: {statement[:80]}")
        found_databases.append(match.group(1))
    if tuple(found_databases) != DATABASES:
        raise ValueError("Database names drifted from the disposable allowlist")

    table_sql = {}
    table_names = {}
    skipped = {}
    for name in ("rycrm-master.sql", "rycrm-tenant.sql", "quartz.sql"):
        statements = split_sql((sql_dir / name).read_text(encoding="utf-8"))
        creates = []
        names = []
        ignored = {"DROP TABLE": 0, "INSERT INTO": 0, "SET": 0, "BEGIN": 0, "COMMIT": 0}
        for statement in statements:
            create = re.match(r"CREATE TABLE\s+`?([A-Za-z0-9_]+)`?\s*\(", statement, re.I)
            if create:
                if any(re.search(rf"\b{verb}\b", statement, re.I) for verb in ("LOAD DATA", "INTO OUTFILE", "CREATE USER", "DEFINER")):
                    raise ValueError(f"Unsafe CREATE TABLE body in {name}")
                names.append(create.group(1).lower())
                creates.append(statement + ";")
                continue
            kind = next((label for label in ignored if statement.upper().startswith(label)), None)
            if kind is None:
                raise ValueError(f"Unrecognized SQL statement in {name}: {statement[:80]}")
            ignored[kind] += 1
        if len(names) != len(set(names)) or not names:
            raise ValueError(f"Duplicate or empty table set in {name}")
        table_sql[name] = creates
        table_names[name] = names
        skipped[name] = ignored

    updates = split_sql((sql_dir / "update_20220311.sql").read_text(encoding="utf-8"))
    if len(updates) != 1 or not re.match(r"ALTER TABLE `master_tenant`\s", updates[0], re.I):
        raise ValueError("Unsupported master_tenant migration")
    if re.search(r"\b(?:DROP TABLE|DROP DATABASE|INSERT|UPDATE|DELETE|LOAD DATA|CREATE USER)\b", updates[0], re.I):
        raise ValueError("Unsafe migration statement")
    return {
        "source_sha256": source_hashes,
        "table_names": table_names,
        "skipped_source_statements": skipped,
        "sample_data_imported": False,
    }, {"tables": table_sql, "master_migration": updates[0] + ";"}


def random_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def write_private(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o600)


def prepare() -> Path:
    audit, schema = extract_schema()
    runtime = Path(tempfile.mkdtemp(prefix="ruoyicrm-crit10-"))
    runtime.chmod(0o700)
    init_dir = runtime / "init"
    init_dir.mkdir(mode=0o700)
    project = "ruoyicrm-crit10-" + secrets.token_hex(5)
    mysql_port, redis_port = random_port(), random_port()
    while redis_port == mysql_port:
        redis_port = random_port()
    root_password = secrets.token_urlsafe(36)
    app_password = secrets.token_urlsafe(36)
    redis_password = secrets.token_urlsafe(36)
    write_private(runtime / "mysql-root-password", root_password + "\n")
    write_private(runtime / "mysql-client.cnf", f"[client]\nuser=root\npassword={root_password}\n")
    write_private(runtime / "mysql-app.cnf", f"[client]\nuser=crit10_app\npassword={app_password}\n")
    write_private(runtime / "redis.acl", f"user default on >{redis_password} ~* +@all\n")
    write_private(runtime / "redis-password", redis_password + "\n")
    env = (
        f"COMPOSE_PROJECT_NAME={project}\nCRIT10_RUNTIME_DIR={runtime}\n"
        f"CRIT10_INIT_DIR={init_dir}\nCRIT10_MYSQL_PORT={mysql_port}\nCRIT10_REDIS_PORT={redis_port}\n"
    )
    write_private(runtime / "compose.env", env)

    sql = [f"CREATE DATABASE `{database}` DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_general_ci;" for database in DATABASES]
    sql.append(f"CREATE USER 'crit10_app'@'%' IDENTIFIED BY '{app_password}';")
    for database in DATABASES:
        sql.append(f"GRANT ALL PRIVILEGES ON `{database}`.* TO 'crit10_app'@'%';")
    write_private(init_dir / "00-databases.sql", "\n".join(sql) + "\n")
    master = ["USE `rycrm-master`;", *schema["tables"]["rycrm-master.sql"], schema["master_migration"]]
    for tenant_number in (1, 2):
        tenant = f"rycrm-tenant-{tenant_number}"
        url = f"jdbc:mysql://127.0.0.1:{mysql_port}/{tenant}?useSSL=false"
        master.append(
            "INSERT INTO `master_tenant` (`tenant`,`url`,`username`,`password`,`database_name`,`host_name`,`status`) "
            f"VALUES ('tenant{tenant_number}','{url}','crit10_app','{app_password}','{tenant}','127.0.0.1','1');"
        )
    write_private(init_dir / "10-master.sql", "\n".join(master) + "\n")
    for tenant_number in (1, 2):
        tenant = f"rycrm-tenant-{tenant_number}"
        statements = [f"USE `{tenant}`;", *schema["tables"]["rycrm-tenant.sql"], *schema["tables"]["quartz.sql"]]
        write_private(init_dir / f"{20 + tenant_number}-tenant.sql", "\n".join(statements) + "\n")
    state = {
        "schema": "ruoyicrm.crit10.local-stack.v1",
        "project": project,
        "runtime_dir": str(runtime),
        "mysql_port": mysql_port,
        "redis_port": redis_port,
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "source_audit": audit,
        "generated_sql_sha256": {path.name: sha256(path.read_bytes()) for path in sorted(init_dir.iterdir())},
        "status": "PREPARED_NOT_RUN",
        "external_evidence": "NOT_RUN",
        "certification": "NOT_CERTIFIED",
    }
    write_private(runtime / "state.json", json.dumps(state, indent=2) + "\n")
    return runtime / "state.json"


def load_state(path: Path) -> dict:
    state = json.loads(path.read_text())
    runtime = Path(state["runtime_dir"])
    if path.resolve() != (runtime / "state.json").resolve() or not runtime.name.startswith("ruoyicrm-crit10-"):
        raise ValueError("State file is outside a dedicated CRIT-10 runtime directory")
    if not state["project"].startswith("ruoyicrm-crit10-"):
        raise ValueError("Unexpected Compose project identity")
    return state


def compose(state: dict, *args: str, timeout: int = 300) -> subprocess.CompletedProcess[str]:
    runtime = Path(state["runtime_dir"])
    return subprocess.run(
        ["docker", "compose", "--env-file", str(runtime / "compose.env"), "-f", str(COMPOSE),
         "-p", state["project"], *args], capture_output=True, text=True, timeout=timeout,
    )


def run_checked(command: list[str], timeout: int = 20, env: dict | None = None) -> str:
    completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout, env=env)
    if completed.returncode:
        raise RuntimeError((completed.stderr or completed.stdout)[-1500:])
    return completed.stdout.strip()


def inspect_bindings(state: dict) -> dict:
    bindings = {}
    for service, container_port, expected_port in (("mysql", "3306/tcp", state["mysql_port"]),
                                                   ("redis", "6379/tcp", state["redis_port"])):
        result = compose(state, "ps", "-q", service)
        container_id = result.stdout.strip()
        if result.returncode or not container_id:
            raise RuntimeError(f"{service} container is unavailable")
        container = json.loads(run_checked(["docker", "inspect", container_id]))[0]
        published = container["NetworkSettings"]["Ports"].get(container_port) or []
        if len(published) != 1 or published[0]["HostIp"] != "127.0.0.1" or int(published[0]["HostPort"]) != expected_port:
            raise RuntimeError(f"{service} is not bound to its dedicated loopback port")
        bindings[service] = {"host": "127.0.0.1", "port": expected_port,
                             "image_id": container["Image"]}
    return bindings


def tcp_probe(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            return True
    except OSError:
        return False


def probe(state: dict) -> dict:
    runtime = Path(state["runtime_dir"])
    result = {
        "schema": "ruoyicrm.crit10.local-probe.v1", "project": state["project"],
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "mysql_tcp": tcp_probe(state["mysql_port"]),
        "redis_tcp": tcp_probe(state["redis_port"]),
        "source_sha256": state["source_audit"]["source_sha256"],
        "sample_data_imported": "UNKNOWN",
        "external_evidence": "NOT_RUN", "certification": "NOT_CERTIFIED",
    }
    try:
        result["bindings"] = inspect_bindings(state)
        mysql = ["mysql", f"--defaults-extra-file={runtime / 'mysql-app.cnf'}", "--protocol=TCP",
                 "-h", "127.0.0.1", "-P", str(state["mysql_port"]), "-N", "-B"]
        version = run_checked(mysql + ["-e", "SELECT VERSION()"])
        if not version.startswith("8.4."):
            raise RuntimeError(f"Unexpected MySQL version: {version}")
        result["mysql_version"] = version
        table_counts = {}
        actual_table_names = {}
        expected = state["source_audit"]["table_names"]
        for database, expected_names in (("rycrm-master", expected["rycrm-master.sql"]),
                                         ("rycrm-tenant-1", expected["rycrm-tenant.sql"] + expected["quartz.sql"]),
                                         ("rycrm-tenant-2", expected["rycrm-tenant.sql"] + expected["quartz.sql"])):
            count = int(run_checked(mysql + ["-e", "SELECT COUNT(*) FROM information_schema.tables "
                                                    f"WHERE table_schema='{database}'"]))
            if count != len(expected_names):
                raise RuntimeError(f"{database} has {count} tables, expected {len(expected_names)}")
            table_counts[database] = count
            observed_names = run_checked(mysql + ["-e", "SELECT TABLE_NAME FROM information_schema.tables "
                                                    f"WHERE table_schema='{database}'"]).splitlines()
            by_lower = {name.lower(): name for name in observed_names}
            if set(by_lower) != set(expected_names):
                raise RuntimeError(f"{database} table names drifted")
            actual_table_names[database] = by_lower
        tenant_rows = int(run_checked(mysql + ["-D", "rycrm-master", "-e", "SELECT COUNT(*) FROM master_tenant"]))
        if tenant_rows != 2:
            raise RuntimeError("Synthetic tenant metadata was not initialized")
        non_synthetic_rows = {}
        for database, names in (("rycrm-master", expected["rycrm-master.sql"]),
                                ("rycrm-tenant-1", expected["rycrm-tenant.sql"] + expected["quartz.sql"]),
                                ("rycrm-tenant-2", expected["rycrm-tenant.sql"] + expected["quartz.sql"])):
            ordinary = [name for name in names if not (database == "rycrm-master" and name == "master_tenant")]
            union = " UNION ALL ".join(f"SELECT COUNT(*) AS c FROM `{database}`.`{actual_table_names[database][name]}`" for name in ordinary)
            row_count = int(run_checked(mysql + ["-e", f"SELECT COALESCE(SUM(c),0) FROM ({union}) AS counted_tables"]))
            non_synthetic_rows[database] = row_count
            if row_count != 0:
                raise RuntimeError(f"{database} contains non-synthetic rows")
        result["mysql_tables"] = table_counts
        result["synthetic_tenant_rows"] = tenant_rows
        result["non_synthetic_rows"] = non_synthetic_rows
        result["sample_data_imported"] = False
        redis_env = dict(os.environ)
        redis_env["REDISCLI_AUTH"] = (runtime / "redis-password").read_text().strip()
        redis = ["redis-cli", "-h", "127.0.0.1", "-p", str(state["redis_port"]), "--no-auth-warning"]
        if run_checked(redis + ["PING"], env=redis_env) != "PONG":
            raise RuntimeError("Redis PING did not return PONG")
        info = run_checked(redis + ["INFO", "server"], env=redis_env)
        match = re.search(r"^redis_version:(7\.[^\r\n]+)", info, re.M)
        if not match:
            raise RuntimeError("Unexpected Redis version")
        result["redis_version"] = match.group(1)
        result["status"] = "LOCAL_PHYSICAL_STACK_READY"
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        result["status"] = "BLOCKED"
        result["reason"] = f"{type(exc).__name__}: {exc}"[:600]
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "up", "probe", "down"])
    parser.add_argument("--state", type=Path)
    args = parser.parse_args()
    if args.action == "prepare":
        path = prepare()
        print(path)
        return 0
    if not args.state:
        parser.error("--state is required")
    state = load_state(args.state)
    if args.action == "down":
        completed = compose(state, "down", "--volumes", "--remove-orphans", timeout=120)
        if completed.returncode:
            print(completed.stderr[-1500:], file=sys.stderr)
            return 1
        runtime = Path(state["runtime_dir"])
        shutil.rmtree(runtime)
        print(f"Destroyed dedicated project {state['project']} and its volumes")
        return 0
    if args.action == "up":
        completed = compose(state, "up", "-d", timeout=600)
        if completed.returncode:
            print(completed.stderr[-1500:], file=sys.stderr)
            return 1
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            receipt = probe(state)
            if receipt["status"] == "LOCAL_PHYSICAL_STACK_READY":
                break
            time.sleep(3)
    else:
        receipt = probe(state)
    receipt_path = Path(state["runtime_dir"]) / "probe-receipt.json"
    write_private(receipt_path, json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"receipt": str(receipt_path), "status": receipt["status"],
                      "mysql_port": state["mysql_port"], "redis_port": state["redis_port"]}))
    return 0 if receipt["status"] == "LOCAL_PHYSICAL_STACK_READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())

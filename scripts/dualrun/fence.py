"""Read-only, fail-closed proof gate for RuoyiCRM HTTP write replay."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
import urllib.parse
from pathlib import Path


class FenceError(ValueError):
    pass


def run_command(*args):
    result = subprocess.run(args, text=True, capture_output=True, timeout=10, check=False)
    if result.returncode:
        raise FenceError("local process/container inspection failed")
    return result.stdout


def private_json(path: Path):
    path = path.resolve(strict=True)
    info = path.stat()
    if info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise FenceError("runtime identity file is not private to current user")
    if path.stat().st_size > 1_000_000:
        raise FenceError("runtime identity file too large")
    return json.loads(path.read_text())


def inspect_container(project, service, runner=run_command):
    ids = runner("docker", "ps", "-q", "--filter", f"label=com.docker.compose.project={project}",
                 "--filter", f"label=com.docker.compose.service={service}").splitlines()
    if len(ids) != 1 or not re.fullmatch(r"[0-9a-f]{12,64}", ids[0]):
        raise FenceError("expected exactly one Compose service container")
    items = json.loads(runner("docker", "inspect", ids[0]))
    if type(items) is not list or len(items) != 1:
        raise FenceError("Docker inspect result malformed")
    if not str(items[0].get("Id", "")).startswith(ids[0]):
        raise FenceError("Docker inspect container ID mismatch")
    return items[0]


def stack_identity(state_path: Path, runner=run_command, now=None):
    path = Path(state_path).resolve(strict=True)
    runtime = path.parent
    if path.name != "state.json" or not runtime.name.startswith("ruoyicrm-crit10-"):
        raise FenceError("state must belong to a dedicated CRIT-10 runtime")
    state = private_json(path)
    receipt = private_json(runtime / "probe-receipt.json")
    project = state.get("project")
    if (state.get("schema") != "ruoyicrm.crit10.local-stack.v1"
            or not isinstance(project, str) or not re.fullmatch(r"ruoyicrm-crit10-[0-9a-f]+", project)
            or not isinstance(state.get("runtime_dir"), str)
            or Path(state["runtime_dir"]).resolve() != runtime
            or receipt.get("schema") != "ruoyicrm.crit10.local-probe.v1"
            or receipt.get("project") != project
            or receipt.get("status") != "LOCAL_PHYSICAL_STACK_READY"
            or receipt.get("sample_data_imported") is not False
            or receipt.get("mysql_tcp") is not True or receipt.get("redis_tcp") is not True
            or set(receipt.get("non_synthetic_rows", {})) != {"rycrm-master", "rycrm-tenant-1", "rycrm-tenant-2"}
            or any(type(v) is not int or v != 0 for v in receipt["non_synthetic_rows"].values())):
        raise FenceError("disposable stack or probe receipt invalid")
    try:
        checked = __import__("datetime").datetime.fromisoformat(receipt["checked_at"])
        age = (now if now is not None else time.time()) - checked.timestamp()
    except (KeyError, TypeError, ValueError) as exc:
        raise FenceError("probe timestamp invalid") from exc
    # The initial zero-row probe precedes synthetic login bootstrap. Recheck
    # live Docker identity now and require a fresh per-case backup later.
    if not -5 <= age <= 3600:
        raise FenceError("initial disposable stack provenance receipt is stale")
    ports = {}
    containers = {}
    volumes = {}
    for service, internal, destination in (("mysql", "3306/tcp", "/var/lib/mysql"),
                                           ("redis", "6379/tcp", "/data")):
        port = state.get(f"{service}_port")
        if type(port) is not int or not 1024 <= port <= 65535:
            raise FenceError("disposable stack port invalid")
        observed = inspect_container(project, service, runner)
        labels = observed.get("Config", {}).get("Labels", {})
        health = observed.get("State", {}).get("Health", {}).get("Status")
        if (labels.get("com.docker.compose.project") != project
                or labels.get("com.docker.compose.service") != service
                or observed.get("State", {}).get("Status") != "running"
                or (service == "mysql" and health != "healthy")):
            raise FenceError("Compose service identity or health mismatch")
        published = observed.get("NetworkSettings", {}).get("Ports", {}).get(internal)
        if (type(published) is not list or len(published) != 1
                or published[0] != {"HostIp": "127.0.0.1", "HostPort": str(port)}):
            raise FenceError("storage service is not bound to expected loopback port")
        mounts = [m for m in observed.get("Mounts", []) if m.get("Destination") == destination]
        if (len(mounts) != 1 or mounts[0].get("Type") != "volume"
                or not mounts[0].get("Name", "").startswith(project + "_")):
            raise FenceError("storage volume does not belong to dedicated project")
        receipt_binding = receipt.get("bindings", {}).get(service, {})
        if (receipt_binding.get("host") != "127.0.0.1" or receipt_binding.get("port") != port
                or receipt_binding.get("image_id") != observed.get("Image")):
            raise FenceError("probe and live Docker binding disagree")
        ports[service] = port
        containers[service] = observed.get("Id")
        volumes[service] = mounts[0]["Name"]
    return {"project": project, "runtime_dir": str(runtime), "ports": ports,
            "containers": containers, "volumes": volumes}


def separate_stacks(source, target):
    if source["project"] == target["project"]:
        raise FenceError("source and target share a Compose project")
    if len(set(source["ports"].values()) | set(target["ports"].values())) != 4:
        raise FenceError("source and target storage ports overlap")
    if len(set(source["containers"].values()) | set(target["containers"].values())) != 4:
        raise FenceError("source and target storage containers overlap")
    if len(set(source["volumes"].values()) | set(target["volumes"].values())) != 4:
        raise FenceError("source and target MySQL/Redis volumes overlap")


def verify_tenant_urls(stack, runner=run_command):
    client = Path(stack["runtime_dir"]) / "mysql-app.cnf"
    if not client.is_file() or client.is_symlink() or client.stat().st_mode & 0o077:
        raise FenceError("private MySQL client credential file unavailable")
    rows = runner("mysql", f"--defaults-extra-file={client}", "--protocol=TCP", "-h", "127.0.0.1",
                  "-P", str(stack["ports"]["mysql"]), "-D", "rycrm-master", "-N", "-B", "-e",
                  "SELECT tenant,url,database_name FROM master_tenant ORDER BY tenant").splitlines()
    if len(rows) != 2:
        raise FenceError("master_tenant does not contain exactly two synthetic tenants")
    for number, row in enumerate(rows, start=1):
        fields = row.split("\t")
        tenant = f"tenant{number}"
        database = f"rycrm-tenant-{number}"
        if len(fields) != 3 or fields[0] != tenant or fields[2] != database:
            raise FenceError("master_tenant synthetic tenant identity mismatch")
        url = fields[1]
        if not url.startswith("jdbc:mysql://"):
            raise FenceError("tenant JDBC URL is not direct MySQL")
        parsed = urllib.parse.urlparse(url[5:])
        if (parsed.hostname != "127.0.0.1" or parsed.port != stack["ports"]["mysql"]
                or parsed.path != "/" + database or parsed.username or parsed.password):
            raise FenceError("tenant JDBC URL points outside dedicated stack")


def verify_snapshot(receipt_path: Path, stack, method, path, now=None):
    """Verify private, recent pre-case MySQL and Redis artifacts; never log their contents."""
    if receipt_path is None:
        raise FenceError("pre-write snapshot receipt is required")
    runtime = Path(stack["runtime_dir"])
    location = Path(receipt_path).resolve(strict=True)
    if location.parent != runtime or location.name != "prewrite-snapshot.json":
        raise FenceError("snapshot receipt must be inside its stack runtime")
    receipt = private_json(location)
    if (receipt.get("schema") != "ruoyicrm.crit04.prewrite-snapshot.v1"
            or receipt.get("project") != stack["project"]
            or receipt.get("method") != method or receipt.get("path") != path
            or receipt.get("containers") != stack["containers"]
            or receipt.get("volumes") != stack["volumes"]):
        raise FenceError("snapshot identity or write case mismatch")
    try:
        captured = __import__("datetime").datetime.fromisoformat(receipt["captured_at"])
        age = (now if now is not None else time.time()) - captured.timestamp()
    except (KeyError, TypeError, ValueError) as exc:
        raise FenceError("snapshot timestamp invalid") from exc
    if not -5 <= age <= 300:
        raise FenceError("pre-write snapshot is stale")
    for kind, magic in (("mysql", b"-- MySQL dump"), ("redis", b"REDIS")):
        artifact = receipt.get(kind, {})
        name = artifact.get("file")
        if type(name) is not str or not re.fullmatch(r"prewrite-(?:mysql|redis)\.(?:sql|rdb)", name):
            raise FenceError("snapshot artifact name invalid")
        file = runtime / name
        if file.is_symlink() or not file.is_file() or file.stat().st_uid != os.getuid() or file.stat().st_mode & 0o077:
            raise FenceError("snapshot artifact is not private")
        if file.stat().st_size < len(magic) or file.stat().st_size > 100_000_000:
            raise FenceError("snapshot artifact size invalid")
        with file.open("rb") as stream:
            if stream.read(len(magic)) != magic:
                raise FenceError("snapshot artifact format invalid")
            stream.seek(0)
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if artifact.get("sha256") != digest or artifact.get("bytes") != file.stat().st_size:
            raise FenceError("snapshot artifact digest mismatch")
    return {"captured_at": receipt["captured_at"], "snapshot_receipt_sha256": hashlib.sha256(location.read_bytes()).hexdigest()}


def app_binding(app_path: Path, stack, runner=run_command):
    """Inspect a live Java PID, its artifact, env port bindings and current sockets."""
    path = Path(app_path).resolve(strict=True)
    if path.parent != Path(stack["runtime_dir"]) or path.name not in {"baseline-app.json", "source-app.json", "target-app.json"}:
        raise FenceError("application receipt is outside its stack runtime")
    app = private_json(path)
    pid, port = app.get("pid"), app.get("port")
    if type(pid) is not int or pid <= 1 or type(port) is not int or not 1024 <= port <= 65535:
        raise FenceError("application PID or HTTP port invalid")
    command = runner("ps", "-p", str(pid), "-o", "command=").strip()
    match = re.search(r"(?:^|\s)-jar\s+(\S+\.jar)(?:\s|$)", command)
    if not match or not re.fullmatch(r"\S*java\s+-jar\s+\S+\.jar", command):
        raise FenceError("application is not a Java jar process")
    jar = Path(match.group(1)).resolve(strict=True)
    if hashlib.sha256(jar.read_bytes()).hexdigest() != app.get("jar_sha256"):
        raise FenceError("running jar does not match application receipt")
    # ps eww is read in memory only. No raw environment, passwords, or token values are logged.
    process = runner("ps", "eww", "-p", str(pid), "-o", "command=")
    needed = {"RUOYI_HTTP_PORT", "RUOYI_MASTER_JDBC_URL", "RUOYI_TENANT_DB_HOST",
              "RUOYI_TENANT_DB_PORT", "RUOYI_REDIS_HOST", "RUOYI_REDIS_PORT"}
    env = {key: match.group(1) for key in needed
           if (match := re.search(r"(?:^|\s)" + key + r"=([^\s]+)", process))}
    if path.name == "baseline-app.json":
        if env or "SPRING_APPLICATION_JSON=" not in process:
            raise FenceError("baseline runtime config is ambiguous")
        def unique_pairs(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise FenceError("duplicate baseline runtime config key")
                result[key] = value
            return result
        raw = process.split("SPRING_APPLICATION_JSON=", 1)[1]
        try:
            config, _ = json.JSONDecoder(object_pairs_hook=unique_pairs).raw_decode(raw)
            flat = {}
            def flatten(node, prefix=""):
                for key, value in node.items():
                    name = prefix + "." + key if prefix else key
                    if isinstance(value, dict):
                        flatten(value, name)
                    else:
                        flat[name] = value
            flatten(config)
        except (ValueError, TypeError, AttributeError) as exc:
            raise FenceError("baseline runtime JSON invalid") from exc
        expected_keys = {"server.port", "ruoyi.profile", "spring.redis.host", "spring.redis.port",
                         "spring.redis.password", "spring.datasource.druid.master.url",
                         "spring.datasource.druid.master.username", "spring.datasource.druid.master.password",
                         "spring.datasource.druid.statViewServlet.enabled", "spring.datasource.druid.webStatFilter.enabled",
                         "spring.main.allow-circular-references", "tenant.database.host", "tenant.database.port",
                         "tenant.database.username", "tenant.database.password", "token.secret"}
        client = (Path(stack["runtime_dir"]) / "mysql-app.cnf").read_text()
        credentials = dict(line.split("=", 1) for line in client.splitlines() if "=" in line)
        redis_password = (Path(stack["runtime_dir"]) / "redis-password").read_text().strip()
        if (set(flat) != expected_keys or type(flat["server.port"]) is not int or flat["server.port"] != port
                or not isinstance(flat["ruoyi.profile"], str)
                or Path(flat["ruoyi.profile"]).resolve() != (Path(stack["runtime_dir"]) / "uploads").resolve()
                or flat["spring.redis.host"] != "127.0.0.1" or flat["spring.redis.port"] != stack["ports"]["redis"]
                or flat["spring.redis.password"] != redis_password
                or flat["spring.datasource.druid.master.username"] != credentials.get("user")
                or flat["spring.datasource.druid.master.password"] != credentials.get("password")
                or flat["tenant.database.host"] != "127.0.0.1" or flat["tenant.database.port"] != stack["ports"]["mysql"]
                or flat["tenant.database.username"] != credentials.get("user")
                or flat["tenant.database.password"] != credentials.get("password")
                or flat["spring.datasource.druid.statViewServlet.enabled"] is not False
                or flat["spring.datasource.druid.webStatFilter.enabled"] is not False
                or flat["spring.main.allow-circular-references"] is not False
                or not isinstance(flat["token.secret"], str) or not flat["token.secret"]):
            raise FenceError("baseline runtime config does not match disposable stack")
        jdbc = flat["spring.datasource.druid.master.url"]
    else:
        if set(env) != needed or int(env["RUOYI_HTTP_PORT"]) != port:
            raise FenceError("application environment lacks exact storage/HTTP bindings")
        if re.search(r"(?:^|\s)(?:SPRING_CONFIG_|SPRING_APPLICATION_JSON|JAVA_TOOL_OPTIONS|SPRING_DATASOURCE_|SPRING_DATA_REDIS_)[A-Z0-9_]*=", process):
            raise FenceError("unreviewed runtime configuration override is present")
        jdbc = env["RUOYI_MASTER_JDBC_URL"]
    if not jdbc.startswith("jdbc:mysql://"):
        raise FenceError("master JDBC URL is not a direct MySQL URL")
    parsed = urllib.parse.urlparse(jdbc[5:])
    if (parsed.hostname != "127.0.0.1" or parsed.port != stack["ports"]["mysql"]
            or parsed.path != "/rycrm-master" or parsed.username or parsed.password
            or (path.name != "baseline-app.json" and
                (env["RUOYI_TENANT_DB_HOST"] != "127.0.0.1"
                 or int(env["RUOYI_TENANT_DB_PORT"]) != stack["ports"]["mysql"]
                 or env["RUOYI_REDIS_HOST"] != "127.0.0.1"
                 or int(env["RUOYI_REDIS_PORT"]) != stack["ports"]["redis"]))):
        raise FenceError("application points outside its dedicated storage stack")
    sockets = runner("lsof", "-Pan", "-p", str(pid), "-iTCP")
    if any("->" in line and "->127.0.0.1:" not in line for line in sockets.splitlines()):
        raise FenceError("application has a non-loopback TCP peer")
    for expected in (f":{port} (LISTEN)", f"->127.0.0.1:{stack['ports']['mysql']} (ESTABLISHED)",
                     f"->127.0.0.1:{stack['ports']['redis']} (ESTABLISHED)"):
        if expected not in sockets:
            raise FenceError("application socket proof is incomplete")
    return {"pid": pid, "http_port": port, "jar_sha256": app["jar_sha256"]}


def authorize_write(source_state, target_state, source_app, target_app, source_url, target_url,
                    method, path, source_snapshot=None, target_snapshot=None, runner=run_command, now=None):
    if method not in {"POST", "PUT", "PATCH", "DELETE"} or not isinstance(path, str) or not path.startswith("/") or ".." in path:
        raise FenceError("write method/path invalid")
    source = stack_identity(source_state, runner, now)
    target = stack_identity(target_state, runner, now)
    separate_stacks(source, target)
    verify_tenant_urls(source, runner)
    verify_tenant_urls(target, runner)
    left_snapshot = verify_snapshot(source_snapshot, source, method, path, now)
    right_snapshot = verify_snapshot(target_snapshot, target, method, path, now)
    left = app_binding(source_app, source, runner)
    right = app_binding(target_app, target, runner)
    expected = (f"http://127.0.0.1:{left['http_port']}", f"http://127.0.0.1:{right['http_port']}")
    if (source_url, target_url) != expected or source_url == target_url:
        raise FenceError("HTTP runtimes do not match independently inspected PIDs")
    return {"status": "LOCAL_WRITE_FENCE_PASSED", "method": method, "path": path,
            "source_project": source["project"], "target_project": target["project"],
            "source_snapshot_sha256": left_snapshot["snapshot_receipt_sha256"],
            "target_snapshot_sha256": right_snapshot["snapshot_receipt_sha256"],
            "source_jar_sha256": left["jar_sha256"], "target_jar_sha256": right["jar_sha256"],
            "external_evidence": "NOT_RUN", "certification": "NOT_CERTIFIED"}

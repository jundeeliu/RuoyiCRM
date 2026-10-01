import hashlib
import json
import os
import tempfile
import time
import unittest
from pathlib import Path

from scripts.dualrun.fence import FenceError, authorize_write, separate_stacks, stack_identity


class Fixture:
    def __init__(self, root):
        self.root = root
        self.now = time.time()
        self.jars = {}
        self.stacks = {}
        for name, mysql, redis, http, pid in (("a", 51001, 51002, 51003, 101),
                                               ("b", 52001, 52002, 52003, 202)):
            project = "ruoyicrm-crit10-" + name.encode().hex()
            runtime = root / project
            runtime.mkdir()
            jar = runtime / "app.jar"
            jar.write_bytes(("synthetic-jar-" + name).encode())
            sha = hashlib.sha256(jar.read_bytes()).hexdigest()
            state = {"schema": "ruoyicrm.crit10.local-stack.v1", "project": project,
                     "runtime_dir": str(runtime), "mysql_port": mysql, "redis_port": redis}
            receipt = {"schema": "ruoyicrm.crit10.local-probe.v1", "project": project,
                       "status": "LOCAL_PHYSICAL_STACK_READY", "sample_data_imported": False,
                       "mysql_tcp": True, "redis_tcp": True, "non_synthetic_rows": {
                           "rycrm-master": 0, "rycrm-tenant-1": 0, "rycrm-tenant-2": 0},
                       "checked_at": __import__("datetime").datetime.fromtimestamp(self.now, __import__("datetime").timezone.utc).isoformat(),
                       "bindings": {"mysql": {"host": "127.0.0.1", "port": mysql, "image_id": "image-mysql"},
                                    "redis": {"host": "127.0.0.1", "port": redis, "image_id": "image-redis"}}}
            for filename, data in (("state.json", state), ("probe-receipt.json", receipt),
                                   ("source-app.json" if name == "a" else "target-app.json",
                                    {"pid": pid, "port": http, "jar_sha256": sha})):
                path = runtime / filename
                path.write_text(json.dumps(data))
                os.chmod(path, 0o600)
            self.stacks[name] = {"project": project, "runtime": runtime, "mysql": mysql,
                                 "redis": redis, "http": http, "pid": pid, "jar": jar}
            client = runtime / "mysql-app.cnf"
            client.write_text("[client]\nuser=synthetic\npassword=synthetic\n")
            os.chmod(client, 0o600)
            artifacts = {}
            for kind, filename, data in (("mysql", "prewrite-mysql.sql", b"-- MySQL dump synthetic\n"),
                                         ("redis", "prewrite-redis.rdb", b"REDIS0011synthetic")):
                artifact = runtime / filename
                artifact.write_bytes(data)
                os.chmod(artifact, 0o600)
                artifacts[kind] = {"file": filename, "bytes": len(data),
                                   "sha256": hashlib.sha256(data).hexdigest()}
            ids = {"mysql": ("a" if name == "a" else "c") * 12,
                   "redis": ("b" if name == "a" else "d") * 12}
            volumes = {service: project + "_" + service + "_data" for service in ("mysql", "redis")}
            snapshot = {"schema": "ruoyicrm.crit04.prewrite-snapshot.v1", "project": project,
                        "method": "POST", "path": "/system/user", "containers": ids, "volumes": volumes,
                        "captured_at": __import__("datetime").datetime.fromtimestamp(self.now, __import__("datetime").timezone.utc).isoformat(),
                        **artifacts}
            snapshot_path = runtime / "prewrite-snapshot.json"
            snapshot_path.write_text(json.dumps(snapshot))
            os.chmod(snapshot_path, 0o600)

    def runner(self, *args):
        if args[:2] == ("docker", "ps"):
            project = args[-3].rsplit("=", 1)[1]
            service = args[-1].rsplit("=", 1)[1]
            key = (project, service)
            return {("ruoyicrm-crit10-61", "mysql"): "a" * 12,
                    ("ruoyicrm-crit10-61", "redis"): "b" * 12,
                    ("ruoyicrm-crit10-62", "mysql"): "c" * 12,
                    ("ruoyicrm-crit10-62", "redis"): "d" * 12}[key] + "\n"
        if args[:2] == ("docker", "inspect"):
            cid = args[-1]
            name = "a" if cid in ("a" * 12, "b" * 12) else "b"
            service = "mysql" if cid in ("a" * 12, "c" * 12) else "redis"
            stack = self.stacks[name]
            port = stack[service]
            inner = "3306/tcp" if service == "mysql" else "6379/tcp"
            dest = "/var/lib/mysql" if service == "mysql" else "/data"
            return json.dumps([{"Id": cid, "Image": "image-" + service,
                                "Config": {"Labels": {"com.docker.compose.project": stack["project"],
                                "com.docker.compose.service": service}},
                                "State": {"Status": "running", "Health": {"Status": "healthy"}},
                                "NetworkSettings": {"Ports": {inner: [{"HostIp": "127.0.0.1", "HostPort": str(port)}]}},
                                "Mounts": [{"Type": "volume", "Destination": dest,
                                            "Name": stack["project"] + "_" + service + "_data"}]}])
        if args[0] == "mysql":
            port = int(args[args.index("-P") + 1])
            return "\n".join(
                f"tenant{number}\tjdbc:mysql://127.0.0.1:{port}/rycrm-tenant-{number}?useSSL=false\trycrm-tenant-{number}"
                for number in (1, 2)) + "\n"
        if args[0] == "ps":
            pid = int(args[args.index("-p") + 1])
            stack = self.stacks["a" if pid == 101 else "b"]
            command = "java -jar " + str(stack["jar"])
            if args[1] == "eww":
                command += (f" RUOYI_HTTP_PORT={stack['http']}"
                            f" RUOYI_MASTER_JDBC_URL=jdbc:mysql://127.0.0.1:{stack['mysql']}/rycrm-master?useSSL=false"
                            f" RUOYI_TENANT_DB_HOST=127.0.0.1 RUOYI_TENANT_DB_PORT={stack['mysql']}"
                            f" RUOYI_REDIS_HOST=127.0.0.1 RUOYI_REDIS_PORT={stack['redis']}")
            return command
        if args[0] == "lsof":
            pid = int(args[args.index("-p") + 1])
            stack = self.stacks["a" if pid == 101 else "b"]
            return (f"TCP *:{stack['http']} (LISTEN)\n"
                    f"TCP 127.0.0.1:1000->127.0.0.1:{stack['mysql']} (ESTABLISHED)\n"
                    f"TCP 127.0.0.1:1001->127.0.0.1:{stack['redis']} (ESTABLISHED)\n")
        raise AssertionError(args)


class DualRunFenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dualrun-test-")
        self.addCleanup(self.temp.cleanup)
        self.fixture = Fixture(Path(self.temp.name))
        self.a = self.fixture.stacks["a"]
        self.b = self.fixture.stacks["b"]

    def authorize(self, runner=None):
        return authorize_write(self.a["runtime"] / "state.json", self.b["runtime"] / "state.json",
                               self.a["runtime"] / "source-app.json", self.b["runtime"] / "target-app.json",
                               f"http://127.0.0.1:{self.a['http']}", f"http://127.0.0.1:{self.b['http']}",
                               "POST", "/system/user", self.a["runtime"] / "prewrite-snapshot.json",
                               self.b["runtime"] / "prewrite-snapshot.json", runner=runner or self.fixture.runner,
                               now=self.fixture.now)

    def test_separate_disposable_projects_volumes_and_app_bindings(self):
        result = self.authorize()
        self.assertEqual(result["status"], "LOCAL_WRITE_FENCE_PASSED")
        self.assertEqual(result["external_evidence"], "NOT_RUN")

    def test_same_volume_or_port_fails(self):
        left = stack_identity(self.a["runtime"] / "state.json", self.fixture.runner, self.fixture.now)
        right = stack_identity(self.b["runtime"] / "state.json", self.fixture.runner, self.fixture.now)
        right["volumes"]["mysql"] = left["volumes"]["mysql"]
        with self.assertRaises(FenceError):
            separate_stacks(left, right)
        right["volumes"]["mysql"] = "other-volume"
        right["ports"]["redis"] = left["ports"]["redis"]
        with self.assertRaises(FenceError):
            separate_stacks(left, right)

    def test_stale_or_nonprivate_receipt_blocks(self):
        path = self.a["runtime"] / "probe-receipt.json"
        data = json.loads(path.read_text())
        data["checked_at"] = "2020-01-01T00:00:00+00:00"
        path.write_text(json.dumps(data))
        with self.assertRaises(FenceError):
            self.authorize()
        data["checked_at"] = __import__("datetime").datetime.fromtimestamp(self.fixture.now, __import__("datetime").timezone.utc).isoformat()
        path.write_text(json.dumps(data))
        os.chmod(path, 0o644)
        with self.assertRaises(FenceError):
            self.authorize()

    def test_missing_or_tampered_prewrite_snapshot_blocks(self):
        path = self.a["runtime"] / "prewrite-snapshot.json"
        path.unlink()
        with self.assertRaises((FenceError, FileNotFoundError)):
            self.authorize()
        path.write_text("{}")
        os.chmod(path, 0o600)
        with self.assertRaises(FenceError):
            self.authorize()

    def test_missing_runtime_storage_socket_or_env_blocks(self):
        def no_redis(*args):
            output = self.fixture.runner(*args)
            if args[0] == "lsof":
                return "\n".join(line for line in output.splitlines() if ":51002" not in line)
            return output
        with self.assertRaises(FenceError):
            self.authorize(no_redis)
        def no_env(*args):
            output = self.fixture.runner(*args)
            return output.replace(" RUOYI_REDIS_PORT=51002", "") if args[:2] == ("ps", "eww") else output
        with self.assertRaises(FenceError):
            self.authorize(no_env)

    def test_tenant_url_pointing_outside_disposable_mysql_blocks(self):
        def wrong_tenant(*args):
            output = self.fixture.runner(*args)
            if args[0] == "mysql" and "51001" in args:
                return output.replace("127.0.0.1:51001/rycrm-tenant-2", "db.production.example:3306/rycrm-tenant-2")
            return output
        with self.assertRaises(FenceError):
            self.authorize(wrong_tenant)

    def test_unbound_http_or_unexpected_path_blocks(self):
        with self.assertRaises(FenceError):
            authorize_write(self.a["runtime"] / "state.json", self.b["runtime"] / "state.json",
                            self.a["runtime"] / "source-app.json", self.b["runtime"] / "target-app.json",
                            "http://127.0.0.1:9999", f"http://127.0.0.1:{self.b['http']}",
                            "POST", "/system/user", runner=self.fixture.runner, now=self.fixture.now)
        with self.assertRaises(FenceError):
            authorize_write(None, None, None, None, "", "", "POST", "/../admin")


if __name__ == "__main__":
    unittest.main()

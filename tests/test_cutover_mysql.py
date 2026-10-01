"""Disposable MySQL 8.4 contract test; never connects to an existing database."""

import os
import secrets
import subprocess
import tempfile
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "deploy/cutover/sql"


def command(*args, input_text=None, check=True):
    return subprocess.run(args, input=input_text, text=True, capture_output=True,
                          timeout=45, check=check)


class DisposableMySqlCutoverTest(unittest.TestCase):
    def test_expand_compatibility_backfill_and_contract(self):
        if command("docker", "info", check=False).returncode:
            self.skipTest("Docker daemon unavailable")
        with tempfile.TemporaryDirectory(prefix="ruoyicrm-cutover-") as temp:
            directory = Path(temp)
            password = secrets.token_urlsafe(32)
            (directory / "password").write_text(password)
            (directory / "client.cnf").write_text("[client]\nuser=root\npassword=" + password + "\n")
            os.chmod(directory / "password", 0o600)
            os.chmod(directory / "client.cnf", 0o600)
            name = "ruoyicrm-cutover-" + secrets.token_hex(6)
            launched = command("docker", "run", "--rm", "-d", "--name", name,
                               "--network", "none", "--mount", f"type=bind,source={temp},target=/run/cutover,readonly",
                               "-e", "MYSQL_ROOT_PASSWORD_FILE=/run/cutover/password",
                               "-e", "MYSQL_DATABASE=cutover_test", "mysql:8.4")
            self.assertEqual(launched.returncode, 0, launched.stderr)
            try:
                def mysql(sql, ok=True):
                    result = command("docker", "exec", "-i", name, "mysql",
                                     "--defaults-extra-file=/run/cutover/client.cnf", "-N", "-B",
                                     "cutover_test", input_text=sql, check=False)
                    if ok:
                        self.assertEqual(result.returncode, 0, result.stderr)
                    return result

                deadline = time.monotonic() + 90
                while time.monotonic() < deadline:
                    if mysql("SELECT 1;", ok=False).returncode == 0:
                        break
                    time.sleep(1)
                else:
                    self.fail("disposable MySQL did not start")

                self.assertTrue(mysql("SELECT VERSION();").stdout.strip().startswith("8.4."))

                source = (ROOT / "sql/rycrm-master.sql").read_text()
                table = source[source.index("CREATE TABLE `master_tenant`"):]
                mysql(table[:table.index(";") + 1])
                mysql("INSERT INTO master_tenant (tenant, host) VALUES ('synthetic-1', 'old.local');")
                mysql((SQL / "01_expand.sql").read_text())
                mysql((SQL / "02_compatibility.sql").read_text())
                mysql((SQL / "03_backfill.sql").read_text())
                self.assertEqual(mysql("SELECT host, host_name FROM master_tenant WHERE tenant='synthetic-1';").stdout.strip(),
                                 "old.local\told.local")
                mysql("INSERT INTO master_tenant (tenant, host_name) VALUES ('synthetic-2', 'new.local');")
                self.assertEqual(mysql("SELECT host, host_name FROM master_tenant WHERE tenant='synthetic-2';").stdout.strip(),
                                 "new.local\tnew.local")
                mysql("UPDATE master_tenant SET host='changed.local' WHERE tenant='synthetic-1';")
                self.assertEqual(mysql("SELECT host, host_name FROM master_tenant WHERE tenant='synthetic-1';").stdout.strip(),
                                 "changed.local\tchanged.local")
                mysql("UPDATE master_tenant SET host_name='other.local' WHERE tenant='synthetic-2';")
                self.assertEqual(mysql("SELECT host, host_name FROM master_tenant WHERE tenant='synthetic-2';").stdout.strip(),
                                 "other.local\tother.local")
                self.assertNotEqual(mysql("INSERT INTO master_tenant (tenant, host, host_name) VALUES ('bad', 'a', 'b');", ok=False).returncode, 0)
                self.assertNotEqual(mysql("UPDATE master_tenant SET host='a', host_name='b' WHERE tenant='synthetic-1';", ok=False).returncode, 0)
                preflight = mysql((SQL / "90_contract_preflight.sql").read_text()).stdout
                self.assertIn("0\n0\n2", preflight)
                mysql((SQL / "99_contract_manual.sql").read_text())
                columns = mysql("SHOW COLUMNS FROM master_tenant;").stdout
                self.assertNotIn("host\t", columns)
                self.assertIn("host_name\t", columns)
            finally:
                command("docker", "rm", "-f", name, check=False)


if __name__ == "__main__":
    unittest.main()

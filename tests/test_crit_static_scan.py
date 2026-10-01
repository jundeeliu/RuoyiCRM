import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SPEC = importlib.util.spec_from_file_location(
    "crit_static_scan", Path(__file__).resolve().parents[1] / "scripts/crit_static_scan.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class StaticScanTest(unittest.TestCase):
    def test_resolved_inventory_rejects_legacy_surfaces(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            java = root / "ruoyi-app/src/main/java/Legacy.java"
            java.parent.mkdir(parents=True)
            java.write_text("import javax.servlet.http.HttpServletRequest;\n"
                            "class Legacy extends WebSecurityConfigurerAdapter {}\n")
            xml = root / "ruoyi-app/src/main/resources/mapper.xml"
            xml.parent.mkdir(parents=True)
            xml.write_text('<beans xmlns="http://www.springframework.org/schema/beans">'
                           '${params.dataScope}</beans>')
            (root / "pom.xml").write_text(
                '<project><dependencies><dependency><groupId>com.netflix.hystrix</groupId>'
                '<artifactId>hystrix-core</artifactId></dependency></dependencies></project>')
            bom = root / "bom.json"
            bom.write_text(json.dumps({"bomFormat": "CycloneDX", "components": [
                {"group": "com.netflix.hystrix", "name": "hystrix-core", "version": "1"}]}))
            report = MODULE.scan(root, bom)
            self.assertEqual("BLOCKED", report["status"])
            self.assertEqual({"LEGACY_OR_UNSAFE_IMPORT", "LEGACY_SECURITY_ADAPTER", "SPRING_BEAN_XML",
                              "RAW_DATA_SCOPE_SQL", "NETFLIX_DECLARED", "NETFLIX_RESOLVED"},
                             {item["code"] for item in report["findings"]})

    def test_missing_resolved_graph_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            java = root / "ruoyi-app/src/main/java/Safe.java"
            java.parent.mkdir(parents=True)
            java.write_text("class Safe {}")
            (root / "pom.xml").write_text("<project/>")
            with self.assertRaisesRegex(ValueError, "SBOM"):
                MODULE.scan(root, root / "missing.json")


if __name__ == "__main__":
    unittest.main()

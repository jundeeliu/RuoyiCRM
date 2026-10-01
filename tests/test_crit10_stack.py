"""Safety properties of the disposable CRIT-10 SQL preparation."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from scripts import crit10_stack


class Crit10StackTests(unittest.TestCase):
    def test_quoted_semicolon_is_not_a_statement_boundary(self):
        source = "-- discard comment\nCREATE TABLE `t` (`note` varchar(20) DEFAULT ';'); /* gone */ INSERT INTO t VALUES ('x;y');"
        self.assertEqual(2, len(crit10_stack.split_sql(source)))

    def test_repository_sql_is_schema_only_and_sample_rows_are_excluded(self):
        audit, schema = crit10_stack.extract_schema()
        self.assertEqual(3, len(schema["tables"]["rycrm-master.sql"]))
        self.assertEqual(22, len(schema["tables"]["rycrm-tenant.sql"]))
        self.assertEqual(11, len(schema["tables"]["quartz.sql"]))
        self.assertEqual(356, sum(v["INSERT INTO"] for v in audit["skipped_source_statements"].values()))
        self.assertFalse(audit["sample_data_imported"])
        generated = "\n".join(sum(schema["tables"].values(), []))
        self.assertNotIn("13800138000", generated)
        self.assertNotIn("DROP TABLE", generated.upper())

    def test_unexpected_sql_mutation_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix="crit10-sql-test-") as directory:
            root = Path(directory)
            sql = root / "sql"
            sql.mkdir()
            for name in crit10_stack.SOURCE_FILES:
                shutil.copyfile(crit10_stack.ROOT / "sql" / name, sql / name)
            with (sql / "rycrm-master.sql").open("a") as stream:
                stream.write("\nDROP DATABASE `rycrm-master`;\n")
            with self.assertRaisesRegex(ValueError, "Unrecognized SQL statement"):
                crit10_stack.extract_schema(root)


if __name__ == "__main__":
    unittest.main()

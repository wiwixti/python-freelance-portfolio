import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "report.py"
SPEC = importlib.util.spec_from_file_location("report", MODULE_PATH)
report = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = report
SPEC.loader.exec_module(report)


class ReportTests(unittest.TestCase):
    def test_numeric_profile(self):
        rows = [{"amount": "10"}, {"amount": "20"}, {"amount": ""}]
        profile = report.profile_column("amount", rows)
        self.assertEqual(profile.kind, "Число")
        self.assertEqual(profile.average, "15.00")
        self.assertEqual(profile.missing, 1)

    def test_html_escapes_input(self):
        with tempfile.TemporaryDirectory() as raw:
            source = Path(raw) / "unsafe.csv"
            source.write_text("name,value\n<script>,2\n", encoding="utf-8")
            page = report.make_report(source)
            self.assertIn("&lt;script&gt;", page)
            self.assertNotIn("<script>", page)

    def test_reads_cp1251_semicolon_csv(self):
        with tempfile.TemporaryDirectory() as raw:
            source = Path(raw) / "sales.csv"
            source.write_bytes("товар;сумма\nРоутер;15980\n".encode("cp1251"))

            headers, rows = report.read_csv(source)

            self.assertEqual(headers, ["товар", "сумма"])
            self.assertEqual(rows[0]["товар"], "Роутер")

    def test_text_column_has_no_numeric_statistics(self):
        rows = [{"name": "Alice"}, {"name": "Bob"}, {"name": ""}]

        profile = report.profile_column("name", rows)

        self.assertEqual(profile.kind, "Текст")
        self.assertEqual(profile.minimum, "—")
        self.assertEqual(profile.missing, 1)


if __name__ == "__main__":
    unittest.main()

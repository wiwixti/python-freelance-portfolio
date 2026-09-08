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


if __name__ == "__main__":
    unittest.main()

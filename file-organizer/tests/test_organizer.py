import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "organizer.py"
SPEC = importlib.util.spec_from_file_location("organizer", MODULE_PATH)
organizer = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = organizer
SPEC.loader.exec_module(organizer)


class OrganizerTests(unittest.TestCase):
    def test_category_is_case_insensitive(self):
        self.assertEqual(organizer.category_for(Path("PHOTO.JPG")), "Images")
        self.assertEqual(organizer.category_for(Path("unknown.bin")), "Other")

    def test_apply_and_undo(self):
        with tempfile.TemporaryDirectory() as raw:
            folder = Path(raw)
            original = folder / "report.pdf"
            original.write_text("demo", encoding="utf-8")
            manifest = folder / "organizer_manifest.json"
            plan = organizer.build_plan(folder, manifest.name)
            organizer.apply_plan(plan, manifest)
            self.assertTrue((folder / "Documents" / "report.pdf").exists())
            self.assertEqual(organizer.undo(manifest), 1)
            self.assertTrue(original.exists())

    def test_existing_destination_gets_unique_name(self):
        with tempfile.TemporaryDirectory() as raw:
            folder = Path(raw)
            (folder / "report.pdf").write_text("new", encoding="utf-8")
            documents = folder / "Documents"
            documents.mkdir()
            (documents / "report.pdf").write_text("old", encoding="utf-8")

            plan = organizer.build_plan(folder, "organizer_manifest.json")

            self.assertEqual(Path(plan[0].destination).name, "report_1.pdf")

    def test_build_plan_rejects_missing_folder(self):
        with tempfile.TemporaryDirectory() as raw:
            missing = Path(raw) / "missing"
            with self.assertRaises(ValueError):
                organizer.build_plan(missing, "organizer_manifest.json")


if __name__ == "__main__":
    unittest.main()

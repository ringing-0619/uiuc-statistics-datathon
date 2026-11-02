import ast
import unittest

from common import ROOT, local_tempdir
from check_public_files import check_tree


class PrivacyTests(unittest.TestCase):
    def test_release_check_flags_data_caches_credentials_and_paths(self):
        with local_tempdir() as directory:
            (directory / "input.csv").write_text("synthetic fixture only")
            (directory / "tracking.db").write_bytes(b"test fixture")
            (directory / ".env").write_text("fixture")
            (directory / "__pycache__").mkdir()
            (directory / "secret.txt").write_text("ghp_" + "A" * 40)
            (directory / "path.txt").write_text("/" + "Users/fixture/example/")
            findings = dict(check_tree(directory))
            for name in ["input.csv", "tracking.db", ".env", "__pycache__", "secret.txt", "path.txt"]:
                self.assertIn(name, findings)

    def test_release_check_flags_database_sidecars_and_additional_spreadsheets(self):
        names = ["input.tsv", "input.xlsm", "tracking.sqlite-wal", "tracking.sqlite3-shm", "tracking.db-journal"]
        with local_tempdir() as directory:
            for name in names:
                (directory / name).write_text("synthetic fixture only")
            findings = dict(check_tree(directory))
            for name in names:
                self.assertIn(name, findings)

    def test_release_check_allows_plain_public_source_and_docs(self):
        with local_tempdir() as directory:
            (directory / "README.md").write_text("Independent synthetic demonstration.")
            (directory / "example.py").write_text("value = 1\n")
            self.assertEqual(check_tree(directory), [])

    def test_model_modules_have_no_print_calls_or_tracking_imports(self):
        for path in (ROOT / "src").glob("*.py"):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    self.assertNotEqual(node.func.id, "print", path.name)
                if isinstance(node, ast.Import):
                    self.assertFalse(any(name.name.split(".")[0] == "mlflow" for name in node.names))
                if isinstance(node, ast.ImportFrom):
                    self.assertNotEqual((node.module or "").split(".")[0], "mlflow")


if __name__ == "__main__":
    unittest.main()

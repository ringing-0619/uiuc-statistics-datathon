"""Check a shareable folder for common data artifacts and credential patterns.

This is a release-folder check, not a proof of anonymity or disclosure permission.
Git history, images and the meaning of written statistics need separate review.
"""
from pathlib import Path
import os
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
LOCAL_DIRECTORIES = {
    "data", "outputs", "mlruns", "mlartifacts", "__pycache__", ".venv",
    "venv", ".pytest_cache", ".test-tmp", ".verification", "htmlcov",
}
ARTIFACT_SUFFIXES = {
    ".csv", ".tsv", ".xlsx", ".xls", ".xlsm", ".parquet", ".db", ".sqlite",
    ".sqlite3", ".pyc", ".pyo", ".pkl", ".pickle", ".joblib", ".log", ".ipynb",
}
PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"),
    "cloud access key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "absolute user-home path": re.compile(r"/(?:Users|home)/[^/\s'\"]+/"),
}


def check_tree(root: Path) -> list[tuple[str, str]]:
    findings = []
    for directory, subdirs, files in os.walk(root, followlinks=False):
        current = Path(directory)
        for name in list(subdirs):
            path = current / name
            if name == ".git":
                subdirs.remove(name)
            elif name in LOCAL_DIRECTORIES or path.is_symlink():
                findings.append((str(path.relative_to(root)), "local artifact directory or symlink"))
                subdirs.remove(name)
        for name in files:
            path = current / name
            rel = str(path.relative_to(root))
            if path.is_symlink():
                findings.append((rel, "symlink requires manual review"))
                continue
            if (path.suffix.lower() in ARTIFACT_SUFFIXES or name in {".DS_Store", "Thumbs.db", ".coverage"}
                    or re.search(r"\.(?:db|sqlite3?)-(?:wal|shm|journal)$", name, re.IGNORECASE)
                    or (name.startswith(".env") and name != ".env.example")):
                findings.append((rel, "data, model, environment or generated artifact"))
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except (UnicodeError, OSError):
                findings.append((rel, "unreadable or non-text file requires manual review"))
                continue
            for label, pattern in PATTERNS.items():
                if pattern.search(content):
                    findings.append((rel, label))
    return findings


def main() -> int:
    findings = check_tree(ROOT)
    if findings:
        for path, reason in findings:
            print(f"REVIEW {path}: {reason}")
        return 1
    print("Release-folder checks passed. No common local artifacts or credential patterns found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

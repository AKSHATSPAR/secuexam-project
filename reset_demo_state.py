#!/usr/bin/env python3
"""Reset SecuExam runtime state to a clean seeded demo setup.

This removes generated local artifacts:
- SQLite database
- encrypted uploaded papers
- Selenium screenshots
- Python bytecode caches

After cleanup, the script reinitializes the database so the app starts with the
default seeded admin, setter, and receiver accounts again.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "secuexam.db"
UPLOAD_DIR = BASE_DIR / "secuexam_app" / "uploads"
SCREENSHOT_DIR = BASE_DIR / "test_screenshots"
PYCACHE_DIR = BASE_DIR / "__pycache__"


def collect_targets(include_screenshots: bool) -> list[Path]:
    targets: list[Path] = []

    if DB_PATH.exists():
        targets.append(DB_PATH)

    if UPLOAD_DIR.exists():
        targets.extend(sorted(path for path in UPLOAD_DIR.iterdir() if path.is_file()))

    if include_screenshots and SCREENSHOT_DIR.exists():
        targets.extend(sorted(path for path in SCREENSHOT_DIR.iterdir() if path.is_file()))

    if PYCACHE_DIR.exists():
        targets.extend(sorted(path for path in PYCACHE_DIR.iterdir() if path.is_file()))

    return targets


def remove_target(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description="Reset SecuExam generated local state")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without changing anything",
    )
    parser.add_argument(
        "--keep-screenshots",
        action="store_true",
        help="Preserve files in test_screenshots/",
    )
    args = parser.parse_args()

    targets = collect_targets(include_screenshots=not args.keep_screenshots)

    if not targets:
        print("No generated runtime artifacts found.")
    else:
        print("Artifacts selected for cleanup:")
        for path in targets:
            print(f"- {path.relative_to(BASE_DIR)}")

    if args.dry_run:
        print("Dry run complete. No files were changed.")
        return 0

    for path in targets:
        remove_target(path)

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    # Import after cleanup so server.py recreates the fresh seeded DB state.
    import server  # pylint: disable=import-outside-toplevel

    server.init_db()
    print("SecuExam state reset complete.")
    print("Seeded accounts restored:")
    print("- admin@secuexam.in / admin123")
    print("- setter@vit.ac.in / setter123")
    print("- receiver@vit.ac.in / receiver123")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

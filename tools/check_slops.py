"""Automated hygiene and AI slops gate."""
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Terms and patterns that must never appear in production code or schemas
FORBIDDEN_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("TODO_PLACEHOLDER", re.compile(r"\bTODO:\s*implement\b", re.IGNORECASE)),
    ("FIXME_PLACEHOLDER", re.compile(r"\bFIXME:\s*placeholder\b", re.IGNORECASE)),
    ("DEBUG_PRINT", re.compile(r"print\(\s*[\"']DEBUG:", re.IGNORECASE)),
    (
        "HARDCODED_API_KEY",
        re.compile(r"(?:api_key|token)\s*=\s*[\"'][a-zA-Z0-9_\-]{20,}[\"']"),
    ),
    (
        "PLACEHOLDER_STRING",
        re.compile(r"\b(?:lorem\s+ipsum|foo_bar_baz_test_dummy)\b", re.IGNORECASE),
    ),
)

INCLUDED_EXTENSIONS = {".py", ".json", ".md", ".yml", ".yaml"}
EXCLUDED_PATHS = {
    ".git",
    ".venv",
    "venv",
    ".ruff_cache",
    ".pytest_cache",
    ".hypothesis",
    "build",
    "dist",
    "objects",
    "__pycache__",
}


def check_file_hygiene(file_path: Path) -> list[str]:
    """Scan one file for forbidden slop patterns."""
    violations: list[str] = []
    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError, UnicodeDecodeError:
        return violations

    for name, pattern in FORBIDDEN_PATTERNS:
        matches = pattern.findall(content)
        if matches:
            rel_path = file_path.relative_to(ROOT).as_posix()
            violations.append(f"{rel_path}: flagged {name} (count={len(matches)})")

    return violations


def main() -> int:
    """Run codebase hygiene scan."""
    violations: list[str] = []
    for path in ROOT.rglob("*"):
        if any(part in EXCLUDED_PATHS for part in path.parts):
            continue
        if path.is_file() and path.suffix in INCLUDED_EXTENSIONS:
            if path.name == "check_slops.py":
                continue
            violations.extend(check_file_hygiene(path))

    if violations:
        print(f"FAILED: Found {len(violations)} hygiene / slop violations:")
        for v in violations:
            print(f"  - {v}")
        return 1

    print(
        "Hygiene & Slop Gate: PASSED (zero placeholders or forbidden patterns detected)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Sanitize and lint all Markdown documentation in pfm-docs for 100% ASCII compliance and table integrity."""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

SYMBOL_MAP: dict[str, str] = {
    "→": "->",
    "⇒": "->",
    "⟶": "->",
    "←": "<-",
    "↔": "<->",
    "≠": "!=",
    "≥": ">=",
    "≤": "<=",
    "≈": "~",
    "•": "-",
    "·": "-",
    "—": "--",
    "–": "--",
    "−": "-",
    "“": '"',
    "”": '"',
    "„": '"',
    "«": '"',
    "»": '"',
    "‘": "'",
    "’": "'",
    "‚": "'",
    "…": "...",
    "×": "x",
    "÷": "/",
    "±": "+/-",
    "°": " deg",
    "º": "o",
    "ª": "a",
    "§": "Sec.",
    "©": "(c)",
    "®": "(r)",
    "™": "(tm)",
    "€": "EUR ",
    "£": "GBP ",
    "✅": "[OK]",
    "✔": "[OK]",
    "✓": "[OK]",
    "❌": "[X]",
    "✗": "[X]",
    "✘": "[X]",
    "⚠": "[WARN]",
    "🛑": "[STOP]",
    "👉": "->",
    "🔥": "*",
    "💻": "",
    "⌨": "",
    "❗": "[!]",
    "\u00a0": " ",
    "\u200b": "",
    "\ufeff": "",
}

BOX_DRAWING_MAP: dict[str, str] = {
    "├": "|--",
    "└": "`--",
    "│": "|",
    "─": "-",
    "┌": "+",
    "┐": "+",
    "┘": "+",
    "┴": "+",
    "┬": "+",
    "┼": "+",
    "┤": "+",
    "▲": "^",
    "▼": "v",
    "◆": "*",
    "●": "*",
    "○": "o",
}


def to_ascii_text(text: str) -> str:
    for src, dst in SYMBOL_MAP.items():
        text = text.replace(src, dst)
    for src, dst in BOX_DRAWING_MAP.items():
        text = text.replace(src, dst)

    # Convert common LaTeX math symbols if any non-ASCII remains
    normalized = unicodedata.normalize("NFKD", text)
    out_chars: list[str] = []
    for ch in normalized:
        if unicodedata.combining(ch):
            continue
        if ord(ch) <= 127:
            out_chars.append(ch)
        else:
            # Fallback: strip any remaining non-ASCII char
            out_chars.append("")
    return "".join(out_chars)


def sanitize_markdown_content(content: str) -> str:
    content = to_ascii_text(content)
    lines = content.splitlines()
    cleaned_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        # Remove <br> or <br/> inside markdown table rows
        if stripped.startswith("|") and stripped.endswith("|"):
            line = re.sub(r"<br\s*/?>", " / ", line, flags=re.IGNORECASE)
        cleaned_lines.append(line.rstrip())
    return "\n".join(cleaned_lines) + "\n"


def check_file(path: Path) -> list[str]:
    errors: list[str] = []
    raw = path.read_text(encoding="utf-8")
    for lineno, line in enumerate(raw.splitlines(), start=1):
        for col, ch in enumerate(line, start=1):
            if ord(ch) > 127:
                errors.append(
                    f"{path}:{lineno}:{col}: non-ASCII character U+{ord(ch):04X} ({ch!r})"
                )
                break
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            if re.search(r"<br\s*/?>", line, flags=re.IGNORECASE):
                errors.append(f"{path}:{lineno}: forbidden <br> tag inside Markdown table row")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Sanitize and lint Pulse Docs Markdown files.")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically convert all files in docs/ and mkdocs.yml to pure ASCII and fix table <br> tags.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    docs_dir = repo_root / "docs"
    target_files = sorted(docs_dir.rglob("*.md"))
    for extra in [repo_root / "mkdocs.yml", repo_root / "README.md", repo_root / "CONTRIBUTING.md"]:
        if extra.is_file():
            target_files.append(extra)

    if args.fix:
        for file_path in target_files:
            original = file_path.read_text(encoding="utf-8")
            updated = sanitize_markdown_content(original)
            if updated != original:
                file_path.write_text(updated, encoding="utf-8")
                print(f"[FIXED] {file_path.relative_to(repo_root)}")

    all_errors: list[str] = []
    for file_path in target_files:
        all_errors.extend(check_file(file_path))

    if all_errors:
        print(f"ERROR: Found {len(all_errors)} editorial/ASCII violation(s):", file=sys.stderr)
        for err in all_errors[:50]:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(
        f"[OK] Validated {len(target_files)} files: 0 non-ASCII characters and 0 table formatting errors."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

---
name: pulse-docs-editorial-standard
description: Mandatory editorial, visual (MkDocs Material Design 3), and ASCII-pure standardization rules for creating or editing documentation in Sorobanerp/pfm-docs (Pulse Docs).
---

# Pulse Docs Editorial & Material Design 3 Standard

Always follow these rules whenever creating, editing, or reviewing documentation inside `Sorobanerp/pfm-docs`:

## 1. Universal ASCII-Pure Standardization (No Accents, No Non-ASCII Symbols)

All Markdown files (`docs/**/*.md`) and navigation labels in `mkdocs.yml` MUST use pure 7-bit ASCII characters (`ord(c) <= 127`):
- Allowed character set: `a-z`, `A-Z`, `0-9`, standard whitespace, and standard ASCII punctuation (`. , : ; - _ / ( ) [ ] { } = + * < > ! ? | # @ $ % " ' ~ & ^`).
- Remove all diacritics, accents, and cedillas (`c`, `a`, `e`, `i`, `o`, `u`).

### Mandatory Symbol Substitution Table

| Forbidden Symbol | Mandatory ASCII Replacement | Example |
| :--- | :--- | :--- |
| Right arrows | `->` | `develop -> main` |
| Not equal | `!=` | `Limite != Orcamento` |
| Greater or equal | `>=` | `cobertura >= 80%` |
| Less or equal | `<=` | `latencia <= 500ms` |
| Approximately | `~` | `~ USD 12/mes` |
| Bullet dot | `-` | `- Item` |
| Em/En dash | `--` | `Pulse Docs -- PFM` |
| Smart quotes | `"` and `'` | `"PFM Pulse"` |
| Multiplication / Checkmarks | `x` / `[OK]` / `[X]` | `[OK] Validated` |

## 2. Table, List, and Mermaid Integrity

1. **Markdown Tables:**
   - NEVER insert `<br>`, `<br/>`, or manual line breaks inside table cells (`| col 1 | col 2 |`).
   - Keep every table row on a single line with matching pipe (`|`) counts.
   - Leave exactly 1 blank line before and after every table.
2. **Lists, Code Blocks, and Admonitions:**
   - Leave exactly 1 blank line before and after every list, fenced code block, and Material admonition (`!!! note`, `!!! warning`, `!!! tip`).
3. **Mermaid Diagrams:**
   - Use simple ASCII labels inside Mermaid diagrams (`gitGraph`, `flowchart`, `sequenceDiagram`, `C4Context`).
   - Quote labels that contain parentheses, colons, or slashes (e.g., `A["2 AZs (us-east-2a/b)"]`).

## 3. Native MkDocs Material Design 3 Components

- Use native `.grid.cards` containers (`<div class="grid cards" markdown>`) for KPI big numbers and navigation grids.
- Do not use fragile custom float/flex hacks that break MkDocs Material responsive layout.
- Validate every change before committing:
  1. `python3 scripts/sanitize_and_lint_docs.py` (must report 0 violations)
  2. `mkdocs build --strict` (must complete with 0 warnings and 0 errors)

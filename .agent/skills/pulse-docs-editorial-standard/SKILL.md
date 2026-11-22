---
name: pulse-docs-editorial-standard
description: Mandatory editorial, visual (MkDocs Material Design 3), currency segregation (BRL vs USD), and ASCII-pure standardization rules for Sorobanerp/pfm-docs (Pulse Docs).
---

# Pulse Docs Editorial, Currency Governance & Material Design 3 Standard

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
| Approximately | `~` | `~ R$ 100,00` |
| Bullet dot | `-` | `- Item` |
| Em/En dash | `--` | `Pulse Docs -- PFM` |
| Smart quotes | `"` and `'` | `"PFM Pulse"` |
| Checkmarks / Crosses | `[OK]` / `[X]` | `[OK] Validated` |

## 2. Strict Currency Segregation Governance (BRL vs. USD)

Never mix SaaS product pricing, customer transaction examples, and cloud provider billing across views:

1. **Views 1, 2, and 3 (`01-visao-negocio/`, `02-visao-produto/`, `03-visao-usuario/`):**
   - Use **EXCLUSIVELY Brazilian Real (`R$` / `BRL`)** for all product plans (`R$ 29,90/mes`, `R$ 49,90/mes`), transactions, credit card limits, budgets, amortization simulations, and BDD Gherkin examples.
   - Zero cloud server billing or USD figures are permitted in Views 1, 2, or 3.
2. **View 4 (`04-visao-arquitetura/`):**
   - Zero scattered infrastructure/cloud billing numbers inside C4 diagrams, sequence flows, or ADRs.
   - Whenever referencing FinOps efficiency in architectural decisions, link directly to `../05-visao-operacoes/finops-e-custos-cloud.md`.
3. **View 5 (`05-visao-operacoes/finops-e-custos-cloud.md`):**
   - The **SINGLE authorized center** for cloud and SaaS infrastructure costs.
   - Every cost table MUST present **USD (`US$`)** alongside a parallel **Estimated BRL (`R$`)** column with an explicit reference exchange rate (e.g., `1 USD = R$ 5,80`).

## 3. Table, List, and Mermaid Integrity

1. **Markdown Tables:**
   - NEVER insert `<br>`, `<br/>`, or manual line breaks inside table cells (`| col 1 | col 2 |`).
   - Keep every table row on a single line with matching pipe (`|`) counts.
   - Leave exactly 1 blank line before and after every table.
2. **Lists, Code Blocks, and Admonitions:**
   - Leave exactly 1 blank line before and after every list, fenced code block, and Material admonition (`!!! note`, `!!! warning`, `!!! tip`).
3. **Mermaid Diagrams:**
   - Use simple ASCII labels inside Mermaid diagrams (`gitGraph`, `flowchart`, `sequenceDiagram`).

## 4. Native MkDocs Material Design 3 Components

- Use native `.grid.cards` containers (`<div class="grid cards" markdown>`) for KPI big numbers and navigation grids.
- Validate every change before committing:
  1. `python3 scripts/sanitize_and_lint_docs.py` (must report 0 violations)
  2. `mkdocs build --strict` (must complete with 0 warnings and 0 errors)

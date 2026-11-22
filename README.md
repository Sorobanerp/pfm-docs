# Pulse Docs -- Portal Institucional de Documentacao Viva (V3.1)

[![Gitflow](https://img.shields.io/badge/Gitflow-develop%20%7C%20main-indigo)](CONTRIBUTING.md)
[![SemVer](https://img.shields.io/badge/SemVer-2.0.0-blue)](CHANGELOG.md)
[![Docs](https://img.shields.io/badge/Pulse%20Docs-V3.1-8CBA51)](https://sorobanerp.github.io/pfm-docs/)

---

## 1. Visao Geral e Governanca Editorial

Repositorio central de **Docs-as-Code** (MkDocs Material Design 3 + Mermaid.js) contendo Visao Executiva V3, Design System IDS "PFM Pulse", ADRs (ADR-001 a ADR-010), Modelo C4, Fluxos Criticos, PRD Core Banking (`RN01--RN06`, `UC-01--UC-08`), Backlog Scrum V3 (`US-01--US-15`), BDD Gherkin, Guia de Execucao Local e Manuais SRE/FinOps.

- **Repositorio:** `Sorobanerp/pfm-docs`
- **Skill de Governanca Editorial Permanente:** [.agent/skills/pulse-docs-editorial-standard/SKILL.md](.agent/skills/pulse-docs-editorial-standard/SKILL.md)
- **Validador Automatico ASCII e Tabelas:** `python3 scripts/sanitize_and_lint_docs.py`

```mermaid
flowchart LR
    DOCS["pfm-docs (MkDocs Material 3)"] -->|"sanitize_and_lint_docs.py + mkdocs build --strict"| CI["GitHub Actions CI"]
    CI -->|"Merge main"| PAGES["GitHub Pages (Pulse Docs V3.1)"]
```

---

## 2. Como Executar e Validar Localmente

```bash
# 1. Validar padronizacao 100% ASCII e integridade de tabelas Markdown
python3 scripts/sanitize_and_lint_docs.py

# 2. Build estrito (0 warnings e 0 erros)
NO_MKDOCS_2_WARNING=1 .venv/bin/mkdocs build --clean --strict

# 3. Subir servidor local de preview
NO_MKDOCS_2_WARNING=1 .venv/bin/mkdocs serve -a 127.0.0.1:8000
```

Consulte [CONTRIBUTING.md](CONTRIBUTING.md) para regras editoriais e Gitflow, e [CHANGELOG.md](CHANGELOG.md) para historico de versoes.

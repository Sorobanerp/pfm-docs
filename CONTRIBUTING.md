# Guia de Contribuicao, Governanca Gitflow e Padrao Editorial -- `pfm-docs`

Este repositorio faz parte da plataforma **PFM Core Banking** (`Sorobanerp`) e segue estritamente as regras da **Skill de Governanca Editorial** em [.agent/skills/pulse-docs-editorial-standard/SKILL.md](.agent/skills/pulse-docs-editorial-standard/SKILL.md).

---

## 1. Padrao Editorial Obrigatorio (ASCII-Pure & Material Design 3)

Toda criacao ou edicao em `docs/**/*.md` e `mkdocs.yml` deve respeitar:

1. **Padronizacao Universal ASCII (Sem Acentos e Sem Caracteres Especiais):**
   - Utilizar apenas caracteres ASCII (`ord(c) <= 127`).
   - Substituir simbolos especiais: `->`, `!=`, `>=`, `<=`, `~`, `-`, `--`, `"` e `'`.
2. **Integridade de Tabelas e Quebras de Linha:**
   - Proibido inserir `<br>` dentro de celulas de tabelas Markdown.
   - Manter 1 linha em branco antes e depois de listas, tabelas, blocos de codigo e admonitions.
3. **Componentes Nativos MkDocs Material Design 3:**
   - Utilizar `<div class="grid cards" markdown>` para KPIs e cards de navegacao.

---

## 2. Fluxo Gitflow Obrigatorio

```text
docs/* ou feat/* --(PR + CI)--> develop --(PR)--> release/vX.Y.Z --(PR + GMUD)--> main (Tag vX.Y.Z)
```

---

## 3. Quality Gates Locais Antes do Pull Request

```bash
python3 scripts/sanitize_and_lint_docs.py
NO_MKDOCS_2_WARNING=1 .venv/bin/mkdocs build --strict
```

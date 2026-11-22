# Changelog -- `pfm-docs`

Todas as alteracoes notaveis neste repositorio sao documentadas neste arquivo seguindo o padrao [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e versionamento semantico [SemVer 2.0.0](https://semver.org/lang/pt-BR/).

---

## [3.1.0] - 2026-11-21

### Added
- Skill permanente de governanca editorial (`.agent/skills/pulse-docs-editorial-standard/SKILL.md`) e validador automatizado (`scripts/sanitize_and_lint_docs.py`) garantindo 100% de compatibilidade ASCII e integridade de tabelas Markdown.
- Documentacao oficial do Design System IDS "PFM Pulse" (`docs/design/ids-pfm-pulse.md`) e Guia Completo de Execucao e Debug Local (`docs/operations/local-development-guide.md`).

### Changed
- Reconstrucao completa da experiencia visual com Google Material Design 3 nativo (`mkdocs.yml`, `docs/stylesheets/pulse-material.css` e `docs/index.md` com `.grid.cards` e `gitGraph` Atlassian).
- Sanitizacao integral de `docs/**/*.md` para ASCII puro (0 acentos, 0 caracteres especiais quebrados e 0 `<br>` em tabelas).

---

## [0.2.0] - 2026-11-20

### Added
- Evolucao completa para Versao 3.0 com ADRs 008, 009 e 010, C4 V3, Fluxos OTel/Lambda, FinOps 3 estagios e BDD Feature 08.

### Changed
- Alinhamento com a arquitetura PFM Core Banking V3.0 (Production-Ready FinOps & Multi-Cloud).

---

## [0.1.0] - 2026-11-15

### Added
- Estrutura inicial do repositorio `pfm-docs`, pipelines GitHub Actions e integracao ao ecossistema Gitflow `Sorobanerp`.

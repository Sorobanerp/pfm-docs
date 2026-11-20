# Changelog — `pfm-docs`

Todas as alterações notáveis neste repositório são documentadas neste arquivo seguindo o padrão [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e versionamento semântico [SemVer 2.0.0](https://semver.org/lang/pt-BR/).

---

## [Unreleased]

### Added
- Padronização de governança DevEx (`README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`) e workflow de validação de **Conventional Commits** em Pull Requests para `develop` e `main`.

---

## [0.2.0] - 2026-11-20

### Added
- Evolução completa para **Versão 3.0** com ADRs 008, 009 e 010, C4 V3, Fluxos OTel/Lambda, FinOps 3 estágios e BDD Feature 08.

### Changed
- Alinhamento com a arquitetura **PFM Core Banking V3.0 (Production-Ready FinOps & Multi-Cloud)**.

### Security
- Aplicação estrita de políticas Zero-Trust (OIDC sem chaves estáticas, Trivy/Semgrep/Gitleaks gates e isolamento por tenant).

### Infrastructure
- Publicação automatizada via `.github/workflows/github-pages-deploy.yml` com `mkdocs build --clean --strict`.

---

## [0.1.0] - 2026-11-15

### Added
- Estrutura inicial do repositório `pfm-docs`, pipelines GitHub Actions e integração ao ecossistema Gitflow `Sorobanerp`.

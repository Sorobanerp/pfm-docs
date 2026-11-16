# `pfm-docs` — Portal de Arquitetura, Produto & SRE (PFM Core Banking)

[![Deploy MkDocs Material to GitHub Pages](https://github.com/Sorobanerp/pfm-docs/actions/workflows/deploy-pages.yml/badge.svg)](https://github.com/Sorobanerp/pfm-docs/actions/workflows/deploy-pages.yml)

Repositório oficial de **Docs-as-Code** da plataforma **PFM Core Banking** (Repositório #14 da topologia Multi-Repo), construído com **[MkDocs Material](https://squidfunk.github.io/mkdocs-material/)**, suporte nativo a diagramas **Mermaid.js**, alternância de tema claro/escuro e busca indexada em português (`pt-BR`).

---

## 1. Estrutura da Documentação

```text
pfm-docs/
├── .github/
│   └── workflows/
│       └── deploy-pages.yml          # CI/CD automático para o GitHub Pages (branch main)
├── docs/
│   ├── index.md                      # Visão Executiva (Stacks, Hexagonal, Multi-Repo, Multicloud)
│   ├── architecture/
│   │   ├── adrs.md                   # ADRs V2 (ADR-001 a ADR-007)
│   │   ├── c4-model.md               # Diagramas Mermaid C4 (Níveis 1, 2 e 3) + 14 Repositórios
│   │   └── flows.md                  # Sequência: PDF em RAM, Pipeline IA 3 Camadas e NFC-e Offline
│   ├── product/
│   │   ├── prd-core-banking.md       # Regras de Negócio RN01 a RN06 + Taxonomia de 2 Níveis
│   │   └── backlog-bdd.md            # Contratos DoR/DoD V2, Backlog US-01 a US-11 e Gherkin BDD
│   └── operations/
│       └── sre-finops.md             # SLOs/SLIs, OpenTelemetry, DR (RPO < 5m, RTO < 30m) e FinOps
├── Makefile                          # Targets de automação (make serve, make build, make clean)
├── mkdocs.yml                        # Configuração do MkDocs Material + Mermaid + Search PT
└── requirements.txt                  # Dependências Python fixadas
```

---

## 2. Como Visualizar Localmente

Você pode executar o portal localmente usando **Python `venv`** (automático via `Makefile`) ou via **Docker**.

### Opção A — Usando `make serve` (Recomendado)

O comando `make serve` cria automaticamente o ambiente virtual `.venv` (caso não exista), instala o `mkdocs-material` e inicia o servidor com *live-reload* na porta **8000** (ou automaticamente na porta **8001** caso a porta `8000` já esteja em uso na máquina, por exemplo pelo Portainer):

```bash
make serve
# Para forçar uma porta específica:
make serve PORT=8080
```

Acesse no navegador: **[http://localhost:8000/pfm-docs/](http://localhost:8000/pfm-docs/)** (ou **[http://localhost:8001/pfm-docs/](http://localhost:8001/pfm-docs/)** se a porta 8000 estiver ocupada).

### Opção B — Usando Docker diretamente

Caso prefira rodar sem instalar pacotes Python locais:

```bash
make serve-docker
# Ou diretamente:
docker run --rm -it -p 8000:8000 -v $(pwd):/docs squidfunk/mkdocs-material:latest
```

---

## 3. Como Validar o Build Estático

Para compilar o portal estático na pasta `./site` com verificação estrita de links e sintaxe (`--strict`):

```bash
make build
```

---

## 4. Como Publicar no GitHub Pages

O repositório já possui o workflow `.github/workflows/deploy-pages.yml` configurado para publicação automática via GitHub Actions:

1. No repositório do GitHub, acesse **Settings → Pages**.
2. Em **Build and deployment → Source**, selecione **GitHub Actions**.
3. Faça push para a branch `main`:
   ```bash
   git push -u origin main
   ```
4. A action `Deploy MkDocs Material to GitHub Pages` executará `mkdocs build --clean --strict` e publicará automaticamente o artefato na URL oficial do GitHub Pages.

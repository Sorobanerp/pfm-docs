# Artefato 07 -- Ciclo de Vida SRE, DevSecOps & Esteira OpenTofu Multi-Ambiente (V2)

Referencia canonica sincronizada com [5.2. Governanca Gitflow Atlassian & CI/CD OpenTofu](gitflow-cicd-e-qualidade.md) e [ADR-009](../02-arquitetura-adrs/ADR-009-ambientes-dev-prod-e-estrutura-modular-opentofu.md).

## 1. Padrao Modular Terraform Docs & Ambientes `dev` / `prod` (`FEAT-01B`)
- **Modulos Reutilizaveis (`terraform/modules/*`):** Padronizados com `versions.tf`, `variables.tf`, `main.tf`, `outputs.tf` e `README.md`, sem blocos `provider` ou `backend` embutidos.
- **Promocao GitOps:**
  - `develop` -> valida `dev` + `prod` e aplica automaticamente no ambiente **`dev`** (`<repo>/dev/terraform.tfstate`);
  - `main` -> aplica no ambiente **`prod`** (`<repo>/prod/terraform.tfstate`) sob aprovacao manual no GitHub Environment `production`.
- **Ordem Oficial de Execucao do Backlog:**
  1. `FEAT-01A` (Infraestrutura 1:1 Revisada & Automacao FinOps) -- **`CONCLUIDA`**
  2. `FEAT-01B` (Padronizacao Modular Terraform Docs, Ambientes `dev`/`prod` e Scale-to-Zero Bootstrap `0/0/0`) -- **`EM_EXECUCAO` / Prioridade Atual**
  3. `FEAT-02` (Build OCI Distroless Arm64, Push ECR & Contratos Backend) -- **`PENDENTE` (Pos-FEAT-01B)**
  4. `FEAT-03` (Rollout Aplicacoes `1/1/1` em `dev` e `1/1/3` em `prod` & Smoke Tests E2E) -- **`PENDENTE` (Pos-FEAT-02)**

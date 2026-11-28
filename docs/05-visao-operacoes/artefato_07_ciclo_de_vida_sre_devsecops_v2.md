# Artefato 07 — Ciclo de Vida SRE, DevSecOps & Esteira OpenTofu Multi-Ambiente (V2)

Referência canônica sincronizada com [5.2. Governança Gitflow Atlassian & CI/CD OpenTofu](gitflow-cicd-e-qualidade.md) e [ADR-009](../02-arquitetura-adrs/ADR-009-ambientes-dev-prod-e-estrutura-modular-opentofu.md).

## 1. Padrão Modular Terraform Docs & Ambientes `dev` / `prod` (`FEAT-01B`)
- **Módulos Reutilizáveis (`terraform/modules/*`):** Padronizados com `versions.tf`, `variables.tf`, `main.tf`, `outputs.tf` e `README.md`, sem blocos `provider` ou `backend` embutidos.
- **Promoção GitOps:**
  - `develop` -> valida `dev` + `prod` e aplica automaticamente no ambiente **`dev`** (`<repo>/dev/terraform.tfstate`);
  - `main` -> aplica no ambiente **`prod`** (`<repo>/prod/terraform.tfstate`) sob aprovação manual no GitHub Environment `production`.
- **Ordem Oficial de Execução do Backlog:**
  1. `FEAT-01A` (Infraestrutura 1:1 Revisada & Automação FinOps) — **`CONCLUÍDA`**
  2. `FEAT-01B` (Padronização Modular Terraform Docs, Ambientes `dev`/`prod` e Scale-to-Zero Bootstrap `0/0/0`) — **`EM_EXECUCAO` / Prioridade Atual**
  3. `FEAT-02` (Build OCI Distroless Arm64, Push ECR & Contratos Backend) — **`PENDENTE` (Pós-FEAT-01B)**
  4. `FEAT-03` (Rollout Aplicações `1/1/1` em `dev` e `1/1/3` em `prod` & Smoke Tests E2E) — **`PENDENTE` (Pós-FEAT-02)**

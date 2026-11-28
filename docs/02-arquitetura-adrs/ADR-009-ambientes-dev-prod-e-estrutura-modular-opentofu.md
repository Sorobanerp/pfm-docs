# ADR-009 -- Ambientes `dev` / `prod`, Estrutura Modular Canonica OpenTofu e Scale-to-Zero Bootstrap

<span class="badge-green">Status: Aprovado</span>
<span class="badge-glow">Escopo: 7 Repositorios *-infra (OpenTofu >= 1.8.0)</span>
<span class="badge-peach">FinOps: desired=0, min=0, max=0 no Bootstrap</span>

---

## 1. Contexto

A plataforma **PFM Core Banking (Pulse V3)** opera com topologia Multi-Repo 1:1 (`ADR-002`) onde cada microsservico possui seu repositorio de infraestrutura dedicado (`pfm-core-ledger-infra`, `pfm-ingestion-bff-infra`, `pfm-forecast-engine-infra`, `pfm-ai-worker-infra`, `pfm-web-infra`), alem da Landing Zone compartilhada (`pfm-shared-infra`) e do guardiao de custos (`pfm-finops-manager-infra`).

Durante o provisionamento inicial de infraestrutura (*Bootstrap* na `FEAT-01`), surgem tres desafios arquiteturais e operacionais criticos:
1. **Segregacao de Ciclo de Vida (`dev` vs. `prod`):** Necessidade de validar alteracoes de IaC continuamente na branch `develop` (ambiente `dev` -- Piloto Minimo) sem impactar o state ou os recursos da base produtiva (`main` -> ambiente `prod`).
2. **Prevencao de `CannotPullContainerError` e Cobrancas Ociosas antes do Build de Aplicacoes (`FEAT-02`/`FEAT-03`):** Se o OpenTofu provisionar servicos Amazon ECS Fargate com `desired_count >= 1` antes que as imagens OCI Distroless Arm64 das aplicacoes sejam construidas e publicadas no Amazon ECR, o ECS entra em loop de falha de pull e gera consumo desnecessario de compute.
3. **Padronizacao Modular Terraform Docs & Abstracao Multi-Cloud (`ADR-007`):** Necessidade de eliminar duplicacao de codigo HCL entre ambientes atraves de modulos reutilizaveis puros (sem blocos `provider` ou `backend` embutidos), documentados com contratos estritos de `versions.tf`, `variables.tf`, `main.tf`, `outputs.tf` e `README.md`.

---

## 2. Decisao Arquitetural

### 2.1. Separacao Oficial em 2 Ambientes (`dev` e `prod`) com States Remotos Isolados
Todos os 7 repositorios de infraestrutura adotam a separacao canonica em dois ambientes sob `terraform/environments/`:
- **`terraform/environments/dev/` (Piloto Minimo -- Branch `develop`):**
  - State remoto isolado no S3: `pfm-shared/dev/terraform.tfstate` (e `<repo-name>/dev/terraform.tfstate` nos demais repositorios `*-infra`).
  - Destinado a validacao continua de infraestrutura, integracao de contratos e testes de fumaca a custo minimo.
- **`terraform/environments/prod/` (Base Produtiva Enxuta -- Branch `main`):**
  - State remoto isolado no S3: `pfm-shared/prod/terraform.tfstate` (e `<repo-name>/prod/terraform.tfstate` nos demais repositorios `*-infra`).
  - Protegido por aprovacao manual (GMUD) no *GitHub Environment* `production`.
- **Leitura Dinamica de Remote State (`data.terraform_remote_state.shared`):**
  - Cada repositorio `*-infra` referencia dinamicamente o state de `pfm-shared-infra` do seu respectivo ambiente:
    ```hcl
    key = "pfm-shared/${var.environment}/terraform.tfstate"
    ```

### 2.2. Estrutura Modular Canonica (Padrao Terraform Docs)
Todo modulo sob `terraform/modules/<module-name>/` deve conter obrigatoriamente:
1. `versions.tf`: Declaracao exclusiva de `required_version = ">= 1.8.0"` e `required_providers` (proibido declarar blocos `provider` ou `backend` dentro de modulos reutilizaveis).
2. `variables.tf`: Todos os inputs declarados com `description` e `type` explicitos (e `sensitive = true` para segredos).
3. `main.tf`: Recursos de infraestrutura mantendo `lifecycle { create_before_destroy = true }` em Security Groups e `enable_cloudwatch_logs = false` por padrao (`ADR-010`).
4. `outputs.tf`: Todos os outputs documentados com `description` e `sensitive = true` quando aplicavel.
5. `README.md`: Documentacao canonica do modulo contendo finalidade e tabelas de Inputs e Outputs.

### 2.3. Estrategia Scale-to-Zero Bootstrap (`desired_count = 0, min_capacity = 0, max_capacity = 0`)
- No bootstrap de infraestrutura (`FEAT-01B`), todos os `terraform.tfvars` de `dev` e `prod` configuram:
  ```hcl
  desired_count = 0 # Target post-ECR image push (FEAT-02/03): 1 (dev) | 1 (prod)
  min_capacity  = 0 # Target post-ECR image push (FEAT-02/03): 1 (dev) | 1 (prod)
  max_capacity  = 0 # Target post-ECR image push (FEAT-02/03): 1 (dev) | 3 (prod)
  ```
- O OpenTofu provisiona 100% da topologia (Cluster ECS, Task Definitions Arm64, ECS Services, Cloud Map Service Connect, Application Auto Scaling Target, IAM Roles Least-Privilege, SQS DLQ e KMS) com **0 tasks ativas**.
- Para evitar rejeicao da API do AWS Application Auto Scaling quando `max_capacity = 0`, os recursos `aws_appautoscaling_target` e `aws_appautoscaling_policy` utilizam a guarda condicional:
  ```hcl
  count = var.compute_engine == "ecs_fargate_spot" && var.max_capacity > 0 ? 1 : 0
  ```

### 2.4. Fluxo GitOps CI/CD (`develop -> dev` | `main -> prod`)
- **Pull Requests (`develop`, `release/**`, `main`):** Executam `tofu fmt -check -recursive`, `tofu validate` e `trivy config` validando **ambos** os ambientes (`dev` e `prod`).
- **Push/Merge na `develop`:** Dispara automaticamente `tofu apply` no ambiente **`dev`** (`terraform/environments/dev`).
- **Push/Merge na `main`:** Dispara `tofu apply` no ambiente **`prod`** (`terraform/environments/prod`) mediante aprovacao no *GitHub Environment* `production`.

---

## 3. Consequencias

- **Positivas:**
  - Zero risco de `CannotPullContainerError` durante o provisionamento de infraestrutura antes do rollout de imagens das aplicacoes (`FEAT-02` e `FEAT-03`).
  - Run-rate de compute de **US$ 0,00/hora** no bootstrap tanto em `dev` quanto em `prod`.
  - Modulos 100% aderentes as boas praticas Terraform Docs e prontos para evolucao multi-cloud (`AWS`, `Azure`, `GCP`).
- **Trade-offs & Mitigacao:**
  - A role IAM OIDC do GitHub Actions na AWS (`PFM-GitHubActions-OIDC-Role`) precisa autorizar o subject `repo:Sorobanerp/pfm-*:ref:refs/heads/develop` (alem de `refs/heads/main` e `environment:production`) para permitir o `tofu apply` automatico do ambiente `dev`.

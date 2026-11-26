# Framework Secure by Design & Auditoria de Seguranca AWS (GitHub Actions OIDC + OpenTofu)

<span class="pulse-badge">Shift-Left DevSecOps -- Zero-Trust -- Least Privilege -- LGPD & BACEN 4.893</span>

Este documento consolida o framework **Secure by Design** da plataforma **PFM Pulse (Soroban Core Banking)** e registra o checklist oficial de auditoria nos 7 dominios criticos de seguranca em nuvem (**GitHub Actions OIDC, IAM Blast Radius, OpenTofu Remote State, Rede ALB/ECS Fargate, RDS PostgreSQL 16, Gestao de Segredos e Observabilidade/Auditoria**).

!!! tip "Governanca de Custos e FinOps"
    Para consultar o detalhamento financeiro da arquitetura cloud e a politica Zero-CloudWatch, acesse o centro unico autorizado em [FinOps & Custos Cloud](../05-visao-operacoes/finops-e-custos-cloud.md).

---

## 1. Os 5 Pilares de Secure by Design Aplicados ao PFM Pulse

<div class="grid cards" markdown>

-   **1. Threat Modeling STRIDE por Fronteira**

    ---

    Mapeamento sistematico de ameacas (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege) em cada fronteira: Edge/ALB, BFF Go, Mesh East-West (gRPC/Service Connect), Eventos Kafka/Lambda e Persistencia RDS/KMS.

-   **2. Secure Defaults (Padroes Seguros de Fabrica)**

    ---

    Todo modulo OpenTofu nasce fechado por padrao: `publicly_accessible = false` no RDS, `block_public_acls = true` em todos os buckets S3, `drop_invalid_header_fields = true` no ALB, `enable_key_rotation = true` no KMS, `enable_cloudwatch_logs = false` e bloqueio de tokens `dev-*` fora de `APP_ENV=local`.

-   **3. Least Privilege (Menor Privilegio & Blast Radius)**

    ---

    Separacao estrita entre `execution_role_arn` (infra ECS) e `task_role_arn` (runtime da aplicacao), politicas IAM sem `Resource = "*"` irrestrito em segredos e Security Groups encadeados (`ALB SG -> ECS Tasks SG -> RDS/Valkey SG`).

-   **4. Paved Roads CI/CD (Esteiras Blindadas Shift-Left)**

    ---

    Todo Pull Request para `develop` ou `main` executa bloqueios automaticos: Gitflow Branch Guard, Conventional Commits, Gitleaks (zero segredos), Semgrep SAST, Trivy Config (IaC), Gate de Politica Secure by Design (`publicly_accessible = true`), cobertura de testes `>= 95%` e assinatura Cosign Keyless.

-   **5. Privacy by Design & Zero-Trust LGPD**

    ---

    Extracao de faturas PDF 100% em memoria RAM com limpeza criptografica (`ZeroBytes()`), Envelope Encryption (`AES-256-GCM` com DEK por familia cifrada pela CMK no AWS KMS), Row-Level Security (RLS) no PostgreSQL 16, bloqueio de leitura de PII por `PLATFORM_ADMIN` e Crypto-Shredding (Art. 18 LGPD).

</div>

---

### Matriz STRIDE por Fronteira de Confianca

| Fronteira | Ameaca STRIDE Principal | Controle Secure by Design Implementado | Evidencia Tecnica |
| :--- | :--- | :--- | :--- |
| **F1: Internet -> ALB Publico** | Spoofing / Tampering / DoS | ALB expoe apenas TCP `80` (redirect `HTTP_301` fixo para `443`) e TCP `443` com `drop_invalid_header_fields = true` e access logs em S3 criptografado. | `pfm-shared-infra/terraform/modules/aws-ecs-pilot/main.tf` |
| **F2: ALB -> Ingestion BFF Go** | Elevation of Privilege / Bypass | Security Group das tasks ECS aceita trafego North-South exclusivamente do Security Group do ALB (`security_groups = [aws_security_group.alb.id]`) e bloqueia tokens `dev-*` fora de `APP_ENV=local`. | `pfm-shared-infra/terraform/modules/aws-ecs-pilot/main.tf` e `pfm-ingestion-bff-go/internal/adapter/in/http/auth.go` |
| **F3: East-West (BFF -> Java / Go)** | Information Disclosure / Spoofing | Descoberta privada via AWS Cloud Map Service Connect (`pfm.internal`) e ingress East-West restrito a `self = true` no Security Group das tasks ECS (`18080-18200`). | `pfm-shared-infra/terraform/modules/aws-ecs-pilot/main.tf` |
| **F4: Tasks ECS -> RDS PostgreSQL 16** | Information Disclosure / Tampering | RDS em subnets privadas (`publicly_accessible = false`), SG aceitando `5432` exclusivamente do SG das tasks ECS, IAM DB Auth (`rds-db:connect`), KMS storage encryption e PostgreSQL RLS (`app.current_tenant_id`). | `pfm-shared-infra/terraform/modules/aws-database-per-service/main.tf` |
| **F5: GitHub Actions -> AWS Account** | Spoofing / Elevation of Privilege | Federacao OIDC sem chaves estaticas, trust policy restrita a `repo:Sorobanerp/pfm-*` (`refs/heads/main` e `environment:production`) e `tofu apply` bloqueado em `pull_request`. | `pfm-shared-infra/terraform/modules/aws-security-kms/main.tf` e `.github/workflows/infra-opentofu-ci-cd.yml` |

---

## 2. Checklist de Auditoria: GitHub Actions OIDC + OpenTofu + AWS (7 Dominios)

Legenda de classificacao:

- **[PASS]**: Controle ja estava implementado e validado em conformidade total.
- **[FIXED]**: Controle endurecido e validado no codigo/IaC/CI nesta auditoria.
- **[MANUAL-AWS-CONSOLE]**: Controle codificado no repositorio que requer conferencia final no Console AWS / GitHub Settings antes do primeiro deploy em producao (`main`).

### Dominio 1 -- Pipeline e Identidade (GitHub Actions OIDC)

| Item de Auditoria | Status | Evidencia nos Repositorios (`develop`) |
| :--- | :--- | :--- |
| **1.1** Trust policy OIDC na AWS aceita apenas `repo:Sorobanerp/pfm-*` (sem wildcard `*` aberto) e restringe `sub` por `ref:refs/heads/main` e `environment:production`. | **[FIXED]** / **[MANUAL-AWS-CONSOLE]** | Codificado em `pfm-shared-infra/terraform/modules/aws-security-kms/main.tf` (`data.aws_iam_policy_document.github_actions_oidc_trust` com lista explicita `local.allowed_github_oidc_subjects`). Conferir na role bootstrap da conta AWS. |
| **1.2** `tofu apply` e deploy de containers nunca rodam em `pull_request`, apenas em `refs/heads/main` com `environment: production` configurado para aprovacao manual (GMUD). | **[PASS]** / **[MANUAL-AWS-CONSOLE]** | Todos os 7 `infra-opentofu-ci-cd.yml` possuem `if: (github.event_name == 'push' || github.event_name == 'workflow_dispatch') && github.ref == 'refs/heads/main'` e `environment: production`. Todos os `cd-aws-deploy.yml` disparam apenas em `push: branches: [main]` com `environment: production`. |
| **1.3** Pinagem de GitHub Actions sem referencias soltas `@main` ou `@master`. | **[PASS]** | Varredura completa em `*/.github/workflows/*.yml` confirmou `0` ocorrencias de `@main` ou `@master` (todas as actions usam tags de versao estaveis `@v1` a `@v6` e Gitleaks pinado em `v8.21.2`). |

### Dominio 2 -- Permissoes IAM (Blast Radius)

| Item de Auditoria | Status | Evidencia nos Repositorios (`develop`) |
| :--- | :--- | :--- |
| **2.1** Policies IAM sem `Action: "*"` ou `Resource: "*"` irrestritos nas roles de runtime e servicos. | **[FIXED]** | Removido `Resource = ["*"]` de `secretsmanager:GetSecretValue` em `pfm-ingestion-bff-infra`, `pfm-core-ledger-infra` e `pfm-forecast-engine-infra`, restringindo para `arn:aws:secretsmanager:${var.aws_region}:*:secret:pfm/upstash/*`. |
| **2.2** Separacao estrita entre `task_role_arn` (runtime da aplicacao) e `execution_role_arn` (ECR pull, bootstrap do container). | **[PASS]** | Todas as task definitions ECS (`pfm-ingestion-bff-infra`, `pfm-core-ledger-infra`, `pfm-forecast-engine-infra`, `pfm-web-infra`) separam `aws_iam_role.ecs_execution_role` e `aws_iam_role.ecs_task_role`. |
| **2.3** `task_role` sem permissoes administrativas e restrita apenas as chaves KMS, buckets S3, banco RDS IAM e segredos necessarios ao microsservico. | **[FIXED]** | `pfm-ingestion-bff-infra` acessa apenas bucket S3 de faturas, CMK KMS e segredo Upstash; `pfm-core-ledger-infra` acessa apenas `rds-db:connect` (`pfm_app_user`), CMK KMS e segredo Upstash; `pfm-web-infra` possui `ecs_task_role` sem nenhuma permissao de infraestrutura. |

### Dominio 3 -- OpenTofu e State Remoto (S3 + DynamoDB Lock)

| Item de Auditoria | Status | Evidencia nos Repositorios (`develop`) |
| :--- | :--- | :--- |
| **3.1** Buckets S3 com `server_side_encryption_configuration` (`aws:kms`), `versioning` (`Enabled`), `block_public_acls = true` e bucket policy negando `s3:DeleteBucket` e transporte sem TLS (`aws:SecureTransport = false`). | **[FIXED]** | Implementado em `pfm-shared-infra/terraform/environments/aws/main.tf` (`aws_s3_bucket_policy.statements_guardrail`) e `pfm-shared-infra/terraform/modules/aws-security-kms/main.tf` (`data.aws_iam_policy_document.tfstate_bucket_guardrail` e `aws_s3_bucket_policy.cloudtrail_audit`). |
| **3.2** Acesso ao bucket de state (`sorobanerp-pfm-tfstate-*`) e tabela DynamoDB lock (`pfm-tfstate-locks`) restrito a role OIDC do pipeline com `-backend-config="encrypt=true"`. | **[PASS]** / **[MANUAL-AWS-CONSOLE]** | Todos os workflows `infra-opentofu-ci-cd.yml` inicializam o backend S3 com `encrypt=true` e lock DynamoDB `pfm-tfstate-locks` via OIDC (`secrets.AWS_ROLE_TO_ASSUME`). |

### Dominio 4 -- Rede e Entrada (ALB & ECS Fargate)

| Item de Auditoria | Status | Evidencia nos Repositorios (`develop`) |
| :--- | :--- | :--- |
| **4.1** ALB publico expoe apenas portas TCP `80` (com redirect `HTTP_301` obrigatorio para `HTTPS:443`) e TCP `443`, com `drop_invalid_header_fields = true`. | **[FIXED]** | Implementado em `pfm-shared-infra/terraform/modules/aws-ecs-pilot/main.tf` (`aws_security_group.alb`, `aws_lb.public` e `aws_lb_listener.http_80_redirect`). |
| **4.2** Security Group das tasks ECS (`pfm-ecs-tasks-sg`) permite ingress North-South exclusivamente do `security_group_id` do ALB (`3000-18080`) e East-West apenas entre as proprias tasks (`self = true`, `18080-18200`), com zero `0.0.0.0/0` de entrada. | **[FIXED]** | Substituida a regra antiga `cidr_blocks = [var.vpc_cidr]` (`0-65535`) em `pfm-shared-infra/terraform/modules/aws-ecs-pilot/main.tf` por `security_groups = [aws_security_group.alb.id]` e `self = true`. |

### Dominio 5 -- Banco de Dados (Aurora / RDS PostgreSQL 16 & Valkey)

| Item de Auditoria | Status | Evidencia nos Repositorios (`develop`) |
| :--- | :--- | :--- |
| **5.1** RDS PostgreSQL 16 em subnets privadas (`aws_db_subnet_group`), `publicly_accessible = false`, `storage_encrypted = true` com CMK KMS, `iam_database_authentication_enabled = true`, `manage_master_user_password = true` e `backup_retention_period = 7`. | **[PASS]** | Definido em `pfm-shared-infra/terraform/modules/aws-database-per-service/main.tf` (`aws_db_instance.core_ledger`). |
| **5.2** Security Group do RDS PostgreSQL 16 (`5432`) e do ElastiCache Valkey (`6379`) aceita conexoes exclusivamente do Security Group das tasks ECS (`security_groups = [var.ecs_tasks_security_group_id]`). | **[FIXED]** | Endurecido em `pfm-shared-infra/terraform/modules/aws-database-per-service/main.tf` e conectado em `pfm-shared-infra/terraform/environments/aws/main.tf` (`ecs_tasks_security_group_id = module.ecs_pilot.ecs_tasks_security_group_id`). |

### Dominio 6 -- Segredos e Configuracao (Zero Hardcoded Secrets)

| Item de Auditoria | Status | Evidencia nos Repositorios (`develop`) |
| :--- | :--- | :--- |
| **6.1** Credenciais gerenciadas via AWS Secrets Manager criptografado com KMS (`aws_secretsmanager_secret` + `manage_master_user_password = true`), variaveis sensiveis sem defaults de senha hardcoded e outputs sensiveis marcados com `sensitive = true`. | **[FIXED]** | Adicionado `sensitive = true` nos outputs de segredos em `pfm-shared-infra/terraform/environments/aws/main.tf` e removidos defaults placeholder em `pfm-ai-worker-infra/terraform/aws/main.tf`. |
| **6.2** Varredura completa (`gitleaks` em todos os 16 repositorios) com `0` vazamentos e bloqueio estrito de tokens `dev-*` e endpoint `/api/v1/auth/dev-token` fora de `APP_ENV=local`. | **[PASS]** | Validado via `gitleaks detect` nos 16 repositorios (`no leaks found`) e confirmado em `pfm-ingestion-bff-go/internal/adapter/in/http/auth.go` (`isLocalDevEnvironment()`) e `swagger_and_local_endpoints.go` (`HTTP 403 Forbidden` fora de `local`). |

### Dominio 7 -- Observabilidade, Auditoria & FinOps (Zero-CloudWatch)

| Item de Auditoria | Status | Evidencia nos Repositorios (`develop`) |
| :--- | :--- | :--- |
| **7.1** AWS CloudTrail multi-regiao habilitado no modulo de seguranca com validacao de integridade de log (`enable_log_file_validation = true`), criptografia KMS e bucket S3 com lifecycle de 90 dias. | **[FIXED]** | Implementado em `pfm-shared-infra/terraform/modules/aws-security-kms/main.tf` (`aws_cloudtrail.pfm_governance` e `aws_s3_bucket.cloudtrail_audit`). |
| **7.2** Logs de acesso do ALB publico habilitados em bucket S3 dedicado (`pfm-alb-access-logs-*`) com criptografia, bloqueio de acesso publico e expiracao automatica em 30 dias (`aws_s3_bucket_lifecycle_configuration`). | **[FIXED]** | Implementado em `pfm-shared-infra/terraform/modules/aws-ecs-pilot/main.tf` (`aws_s3_bucket.alb_access_logs` e bloco `access_logs` em `aws_lb.public`). |
| **7.3** Logs das aplicacoes em JSON estruturado roteados para Datadog com `enable_cloudwatch_logs = false` por padrao em todos os modulos de servico (custo zero no CloudWatch Logs). | **[FIXED]** | Confirmado `enable_cloudwatch_logs = false` em `pfm-ingestion-bff-infra`, `pfm-core-ledger-infra`, `pfm-forecast-engine-infra`, `pfm-ai-worker-infra`, `pfm-web-infra` e padronizado tambem em `pfm-finops-manager-infra/terraform/aws/main.tf`. |

---

## 3. Guia de Verificacao Manual Final no Console AWS (Pre-Flight antes do Deploy na `main`)

Antes de aprovar a primeira GMUD de producao (`merge` para `main` e aprovacao manual do `environment: production`), o Arquiteto de Seguranca / DevSecOps deve conferir os 5 itens abaixo diretamente no Console AWS e no GitHub Organization Settings:

1. **IAM -> Identity Providers & Roles (OIDC Bootstrap):**
   - Confirmar que o provedor `token.actions.githubusercontent.com` existe na conta AWS (`366476833548`) com Audience `sts.amazonaws.com`.
   - Conferir a aba **Trust relationships** da role referenciada em `secrets.AWS_ROLE_TO_ASSUME` e garantir que a politica corresponde ao output `github_actions_oidc_trust_policy_json` gerado pelo modulo `aws-security-kms` (aceitando apenas `repo:Sorobanerp/pfm-*` sem wildcard global `*`).
2. **S3 -> Bucket de State Bootstrap (`sorobanerp-pfm-tfstate-us-east-2-366476833548`):**
   - Confirmar no console S3 que o bucket bootstrap de state possui **Bucket Versioning = Enabled**, **Default Encryption = SSE-KMS**, **Block all public access = On** e **Bucket Policy** correspondente ao output `tfstate_bucket_guardrail_policy_json` (negando `s3:DeleteBucket` e `aws:SecureTransport = false`).
3. **DynamoDB -> Tabela de Lock (`pfm-tfstate-locks`):**
   - Confirmar que a tabela `pfm-tfstate-locks` em `us-east-2` esta com `PAY_PER_REQUEST` (On-Demand), criptografia KMS habilitada e Point-in-Time Recovery (PITR) conforme politica de governanca.
4. **GitHub Settings -> Environments (`production`):**
   - Em cada repositorio `Sorobanerp/pfm-*`, acessar **Settings -> Environments -> production** e confirmar que **Required reviewers** esta ativo e restrito ao time de Arquitetura/GMUD, e que **Deployment branches** permite apenas a branch `main`.
5. **AWS Billing & Cost Management -> Budgets:**
   - Confirmar que o AWS Budget mensal de alerta da conta piloto (`us-east-2`) esta ativo com notificacoes em `50%`, `80%` e `100%` do teto planejado em [FinOps & Custos Cloud](../05-visao-operacoes/finops-e-custos-cloud.md).

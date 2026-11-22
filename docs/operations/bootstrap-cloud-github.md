# Plano de Bootstrap Cloud, Observabilidade e Governanca GitHub (Zero-Trust & FinOps)

Este documento estabelece o plano diretor e arquitetural para o **Bootstrap Multicloud**, a governanca da organizacao GitHub [`Sorobanerp`](https://github.com/Sorobanerp), o pipeline de qualidade com **SonarCloud (Gate $\ge$ 95%)**, a observabilidade enxuta com **Datadog Free Tier ($\le$ 5 hosts)** e os pipelines de entrega continua com **GMUD Automatizada** e **Zero-Trust OIDC**.

---

## 1. Diagrama de Dependencias de Bootstrap (Zero-Trust)

A implantacao segue uma esteira de pre-requisitos rigida e auditavel, garantindo que nenhum recurso de infraestrutura ou aplicacao seja provisionado sem que as camadas de identidade federada, governanca orcamentaria e gates de seguranca estejam ativas:

```mermaid
flowchart TD
    A["1. Nuvens (AWS Default -> Azure -> GCP)<br/>Identity Provider OIDC + IAM Roles + Buckets State Remoto + Budgets"] --> B["2. Qualidade & Observabilidade Free Tier<br/>SonarCloud (Gate >= 95%) + Datadog Free (<= 5 hosts, OTLP)"]
    B --> C["3. GitHub Organization & Repositorios<br/>Org Secrets/Variables + Environments + Branch Protection (main/develop)"]
    C --> D["4. Primeiro Deploy Infra Compartilhada<br/>Pipeline pfm-shared-infra via GMUD (VPC, K8s/ECS, RDS, KMS)"]
    D --> E["5. Deploy Infra Dedicada 1:1 (*-infra)<br/>IAM Roles individuais + Helm Values + Alertas SRE"]
    E --> F["6. Deploy Continuo das Aplicacoes<br/>Java 25 LTS, Golang, Python, Next.js (SAST + Sonar 95% + GMUD)"]
```

---

## 2. Isolamento Multicloud, OIDC & FinOps Guardrails

Para garantir **Zero-Trust**, **nenhuma chave de acesso estatica** (`AWS_ACCESS_KEY_ID`, `ARM_CLIENT_SECRET`, service account JSON) e persistida no GitHub. Toda a autenticacao entre os runners do GitHub Actions e os provedores de nuvem ocorre via **OpenID Connect (OIDC)** com assercoes criptograficas de curta duracao (tokens temporarios validos apenas durante a execucao do Job).

### 2.1. Arquitetura de Federacao de Identidade OIDC

| Provedor de Nuvem | Provedor OIDC Configurado | Subject Claim Validado (`sub`) | Mecanismo de Assume Role |
| :--- | :--- | :--- | :--- |
| **AWS (Default)** | `https://token.actions.githubusercontent.com` / (Audience: `sts.amazonaws.com`) | `repo:Sorobanerp/*:environment:pilot` / `repo:Sorobanerp/*:environment:production` | `sts:AssumeRoleWithWebIdentity` restrito a role `arn:aws:iam::<ACCOUNT_ID>:role/github-actions-pfm-deployer` |
| **Microsoft Azure** | `https://token.actions.githubusercontent.com` / (Audience: `api://AzureADTokenExchange`) | `repo:Sorobanerp/*:ref:refs/heads/main` / `repo:Sorobanerp/*:environment:production` | Azure AD App Registration + Federated Identity Credentials associada a Role `Contributor` no Resource Group |
| **Google Cloud (GCP)**| `https://token.actions.githubusercontent.com` | `attribute.repository_owner/Sorobanerp` | Workload Identity Pool (`github-actions-pool`) + Service Account Impersonation |

### 2.2. Politica de Tags Obrigatorias & Alocacao de Custos

Nenhum recurso de computacao, rede ou armazenamento pode ser criado sem as seguintes tags aplicadas em nivel de provider OpenTofu/Terraform:

```hcl
default_tags {
  tags = {
    Project     = "pfm-core-banking"
    Environment = var.environment # "pilot" ou "production"
    Owner       = "finops@soroban.com"
    CostCenter  = "1040-fintech-core"
    ManagedBy   = "opentofu"
    Repository  = "Sorobanerp/${var.repo_name}"
    Compliance  = "LGPD-PCI-DSS-Ready"
  }
}
```

### 2.3. FinOps Guardrails & Dimensionamento de Custos Minimos

A estrategia prioriza custos extremamente enxutos durante o Piloto Familiar (5 usuarios), mantendo alta fidelidade tecnica com a arquitetura de producao:

#### 1. AWS (Regiao Primaria / Default -- `us-east-2`): US\$ 12 a US\$ 24 / mes (Piloto V3 / ADR-008)
- **Storage de Estado Remoto:** S3 Bucket criptografado com SSE-KMS + DynamoDB Table para *State Locking* (US\$ 0,50/mes).
- **PostgreSQL Core Ledger & Audit Log:** Amazon RDS PostgreSQL 16 `db.t4g.micro` Single-AZ com 20 GB gp3 e parada noturna automatizada via `pfm-finops-manager` (US\$ 7,50--12,00/mes).
- **Computacao (BFF, Ledger, Forecast, Web):** AWS ECS Fargate Spot (`linux/arm64` Graviton, `0.25 vCPU / 0.5 GB RAM`) com plano de controle gratuito e Service Connect `pfm.internal` (US\$ 3,50--8,00/mes).
- **Worker IA Serverless (`pfm-ai-worker-python`):** AWS Lambda Arm64 orientada a eventos Kafka/gRPC -- **US\$ 0,00 ocioso** (ADR-009).
- **Event Streaming & Cache:** **Upstash Kafka & Redis Serverless** com TLS/SASL (Free Tier ate 10.000 msgs/cmds dia -- US\$ 0,00--3,50/mes).
- **FinOps Budget Alert:** Alerta preventivo em **US\$ 20,00/mes** e *Circuit-Breaker* automatico em **US\$ 30,00/mes** via `pfm-finops-manager`.

#### 2. Microsoft Azure (Regiao Secundaria DR -- `brazilsouth` / `eastus`): Warm Standby
- **Backend de Estado:** Azure Storage Account (Blob Storage com Imutabilidade e Encriptacao gerenciada) para `terraform.tfstate`.
- **Database:** Azure Database for PostgreSQL Flexible Server Burstable `B1ms` (`1 vCPU, 2 GB RAM`) com armazenamento de 32 GB.
- **Compute:** Azure Container Apps (ACA) com consumo *Serverless* configurado para escala a zero (*Scale-to-Zero*) quando o trafego nao estiver ativo no ambiente de Disaster Recovery.

#### 3. Google Cloud (Regiao Terciaria -- `southamerica-east1` / `us-central1`): ~US\$ 8 / mes liquidos
- **Backend de Estado:** Google Cloud Storage (GCS) Multi-Regional com Object Versioning.
- **Compute:** Cloud Run de 2a Geracao com cobranca estritamente orientada a eventos (CPU alocada apenas durante o processamento da requisicao HTTP/gRPC).
- **Credito & Free Tier:** Uso do Free Tier mensal (primeiros 2 milhoes de requisicoes Cloud Run gratuitas e 1 GB de rede de saida).

---

## 3. Politica de Governanca Datadog Free Tier ($\le$ 5 Hosts)

A plataforma PFM Core Banking adota o plano **Datadog Free Tier**, que disponibiliza monitoramento completo de infraestrutura sem custo para ate **5 hosts fisicos ou nos virtuais**:

```mermaid
flowchart LR
    subgraph Microservices["Microsservicos PFM (Host / K8s / ECS)"]
        LEDGER["pfm-core-ledger-java"]
        BFF["pfm-ingestion-bff-go"]
        FORECAST["pfm-forecast-engine-go"]
        AI["pfm-ai-worker-python"]
        WEB["pfm-web-nextjs"]
    end

    subgraph OTelCollector["OpenTelemetry Collector Daemon / Sidecar"]
        REDACT["Redaction Processor<br/>(Anonimizacao CPF/PII)"]
        FILTER["Filter Processor<br/>(Exclui /health, /healthz, /actuator)"]
        EXPORT["Datadog Exporter<br/>(OTLP Datadog Intake)"]
    end

    subgraph Datadog["Datadog Free Tier (<= 5 Hosts)"]
        DASH["Dashboards RED & USE"]
        SLO["Monitors de Latencia & Erro"]
    end

    Microservices -->|"OTLP gRPC (Porta 4317)"| REDACT
    REDACT --> FILTER
    FILTER --> EXPORT
    EXPORT -->|"HTTPS (API Key)"| Datadog
```

### Regras Inegociaveis de Governanca Datadog:
1. **Limite Estrito de Hosts ($\le$ 5):** O agente ou OTel collector exporta metricas agregadas por no/host fisico, impedindo que tarefas efemeras gerem *host overages*.
2. **Filtro de Ruido & Healthchecks:** O processador OTel descarta 100% dos traces e logs com destino aos endpoints de sonda (`/health`, `/healthz`, `/actuator/health`, `GET /`), preservando a cota mensal de ingestao apenas para fluxos de negocio reais (UC-01 a UC-06).
3. **Higienizacao LGPD / Zero PII:** O `redaction processor` do OpenTelemetry Collector substitui expressoes regulares de CPF (`\d{3}\.\d{3}\.\d{3}-\d{2}`), numeros de cartao (`\b(?:\d{4}[ -]?){3}\d{4}\b`), e-mails e chaves de sessao pelo marcador `[REDACTED_PII]` antes de enviar qualquer dado para o backend Datadog.

---

## 4. Gitflow Fintech & Quality Gate Estrito (95% Cobertura)

### 4.1. Modelo de Branching & Ciclo de Mudanca

```text
feature/PFM-xxx --> PR com CI/SAST --> develop --> release/vX.Y.Z --> PR com GMUD --> main (vX.Y.Z Tag)
                                                                             |
                                                                             `----> Deploy Pilot / Prod
```

1. **`feature/*`:** Branch criada a partir de `develop` para desenvolvimento local.
2. **`develop`:** Branch de integracao continua. Protegida contra push direto. Exige 1 aprovacao de Code Review e passagem de todos os testes unitarios.
3. **`release/vX.Y.Z`:** Branch de homologacao, congelamento de codigo e execucao de testes de carga (k6) e E2E Playwright.
4. **`main`:** Branch de producao estrita. **Nenhum commit direto e permitido**. O merge so ocorre a partir de uma `release/*` via Pull Request contendo o formulario oficial de **GMUD (Gestao de Mudanca)** preenchido e aprovado pelo Tech Lead / SRE.

### 4.2. Formulario Obrigatorio de GMUD no Pull Request (`main`)

Todo PR para `main` deve conter o checklist de governanca preenchido no corpo da Issue/PR:

```markdown
###  Formulario de Gestao de Mudanca (GMUD) -- Release Oficial

- **Identificador da Release:** vX.Y.Z
- **Resumo Executivo da Mudanca:** (Descricao objetiva do impacto aos titulares)
- **Plano de Rollback:**
  - [ ] Migracao de banco e retrocompativel (Expand & Contract, sem DROP COLUMN imediato)
  - [ ] Imagem anterior do container documentada para reversao imediata via Helm/ECS
- **Evidencias do Quality Gate:**
  - [ ] Semgrep SAST: 0 vulnerabilidades (CWE Top 25 e OWASP API)
  - [ ] Gitleaks: 0 segredos detectados
  - [ ] Trivy: 0 CVEs Criticas/Altas na imagem Distroless
  - [ ] SonarCloud: Cobertura de Testes >= 95.0% comprovada
- **Aprovadores:** @fcd007 (Lead Architect) & SRE On-call
```

### 4.3. Quality Gate Automatizado (CI Pipeline)

| Ferramenta | Etapa de Execucao | Regra de Bloqueio (Quality Gate) |
| :--- | :--- | :--- |
| **Gitleaks** | Pre-commit & CI PR | Bloqueio imediato caso detecte chaves privadas, tokens AWS/GCP, senhas ou JWTs. |
| **Semgrep** | CI PR (`develop` & `main`) | Bloqueio em caso de vulnerabilidades OWASP Top 10 ou injecao SQL/XXE. |
| **Trivy** | Build de Imagem Docker | Falha o build se encontrar vulnerabilidades `CRITICAL` ou `HIGH` na imagem base Distroless. |
| **SonarCloud** | Analise Estatica & Cobertura | **Gate $\ge$ 95% de Cobertura de Codigo Novo**, Duplicacao de Codigo $< 3\%$, 0 *Bugs*, 0 *Security Hotspots* abertos. |

### 4.4. Versionamento SemVer 2.0.0, Conventional Commits & `CHANGELOG.md` Governado

Todos os repositorios da organizacao `Sorobanerp` seguem obrigatoriamente a especificacao **Semantic Versioning 2.0.0 (`MAJOR.MINOR.PATCH`)** combinada ao padrao **Conventional Commits**:

- **`feat:`** $\rightarrow$ Incrementa `MINOR` (`0.x.0`), indicando nova funcionalidade retrocompativel.
- **`fix:` / `perf:` / `security:`** $\rightarrow$ Incrementa `PATCH` (`0.0.x`), indicando correcao de bug ou melhoria sem quebra de contrato.
- **`BREAKING CHANGE:` / `feat!:`** $\rightarrow$ Incrementa `MAJOR` (`x.0.0`), exigindo nova versao major de contrato no `pfm-contracts`.
- **`docs:` / `chore:` / `ci:` / `refactor:`** $\rightarrow$ Governanca interna e documentacao sem impacto de API publica.

**Geracao Automatica de `CHANGELOG.md`:**
1. Ao abrir PR de `develop` para `release/vX.Y.Z`, o pipeline de release gera/atualiza o `CHANGELOG.md` agrupando automaticamente *Features*, *Bug Fixes* e *Security/FinOps* a partir dos Conventional Commits.
2. O merge da `release/vX.Y.Z` na `main` cria a Git Tag anotada `vX.Y.Z` e publica os artefatos auditaveis.

---

## 5. Backlog Estrategico de Bootstrap (`BOOT-01` a `BOOT-07`)

A tabela abaixo estabelece o roteiro de execucao sequencial para levar a governanca e o deploy multicloud ao ar:

| ID | Epico / Historia | Provedor / Ferramenta | Descricao Tecnica & Escopo | Criterios de Pronto (Definition of Done - DoD) |
| :-: | :--- | :--- | :--- | :--- |
| **`BOOT-01`** | **Provedores OIDC & IAM Roles** | AWS, Azure, GCP | Criar os provedores OIDC para `token.actions.githubusercontent.com` e as IAM Roles de deploy com politicas de menor privilegio. | `gh workflow` assume credenciais efemeras em AWS STS, Azure AD e GCP Workload Identity sem armazenar segredos estaticos no GitHub. |
| **`BOOT-02`** | **Buckets de Estado Remoto & Locking** | S3, Azure Blob, GCS | Provisionar buckets S3 (com versionamento e criptografia KMS) + DynamoDB para state locking nas 3 nuvens via OpenTofu. | Arquivo `terraform.tfstate` criptografado e bloqueio de concorrencia testado com sucesso ao rodar `tofu init`. |
| **`BOOT-03`** | **Governanca GitHub Org `Sorobanerp`** | GitHub CLI / API | Configurar Secrets e Variables da organizacao, criar os Environments `pilot` e `production`, e ativar Branch Protection Rules nas branches `main` e `develop`. | Branches `main` e `develop` rejeitam commits diretos e forcam aprovacao de PR e status checks do CI (`SonarCloud`, `Trivy`). |
| **`BOOT-04`** | **SonarCloud Quality Gate (95%)** | SonarCloud | Vincular os repositorios da organizacao [`Sorobanerp`](https://github.com/Sorobanerp) ao SonarCloud e instituir o Quality Gate rigido de **95% de cobertura**. | PRs com cobertura inferior a 95% em novas linhas de codigo sao bloqueados automaticamente com status `FAILED`. |
| **`BOOT-05`** | **Datadog Free Tier & OTLP Collector** | Datadog / OTel | Configurar a organizacao Datadog no plano Free Tier ($\le$ 5 hosts), com filtros de descarte para `/health` e sanitizacao LGPD/PII. | Metricas RED (Rate, Errors, Duration) e latencias P95/P99 visualizadas no dashboard Datadog sem ultrapassar o limite de 5 nos. |
| **`BOOT-06`** | **Deploy Pipeline `pfm-shared-infra`** | GitHub Actions / OpenTofu | Criar o workflow de CI/CD para deploy da Landing Zone compartilhada (VPC, PostgreSQL 16 RLS, Valkey, Kafka e KMS) disparado via PR com GMUD. | Execucao de `tofu plan` no PR e `tofu apply` apos merge na `main` no ambiente `production`, com logs auditaveis. |
| **`BOOT-07`** | **Pipelines 1:1 dos Repositorios da Plataforma** | GitHub Actions / Docker | Configurar os workflows de CI/CD para os 5 microsservicos e seus respectivos 5 repositorios `-infra`, com compilacao multi-stage Distroless. | Todos os 10 repositorios com pipelines verdes no GitHub Actions gerando imagens versionadas no GitHub Packages / ECR. |

---

## 6. Procedimento de Validacao e Execucao

Para iniciar o provisionamento do backlog `BOOT-01` a `BOOT-07`, utilize o script de bootstrap OIDC disponivel em `pfm-shared-infra/terraform/modules/security-kms/` ou os manifests de automacao correspondentes via GitHub CLI (`gh`).

# 4.4. Registro de Decisoes Arquiteturais (ADR-001 a ADR-010)

<span class="badge-green">Artefato 02 - ADRs 001 a 010</span>
<span class="badge-glow">Multi-Cloud &amp; Hexagonal</span>

Este documento consolida as **10 Decisoes Arquiteturais (`ADR-001` a `ADR-010`)** que governam a engenharia da plataforma **PFM Core Banking (V3)**.

!!! note "Segregacao de Custos FinOps"
    Os valores financeiros de infraestrutura cloud e o comparativo entre o estagio piloto enxuto e a hiperescala Kubernetes estao centralizados exclusivamente em [5.3. FinOps & Custos Cloud](../05-visao-operacoes/finops-e-custos-cloud.md).

---

## Sumario Executivo de ADRs

| ID | Titulo da Decisao | Status | Escopo Principal |
| :---: | :--- | :---: | :--- |
| **ADR-001** | Poliglotismo Restrito e Arquitetura Hexagonal | Aprovado | Java 25, Go 1.27, Python 3.12, Next.js 15, Kotlin Android |
| **ADR-002** | Topologia Multi-Repo, Mapeamento 1:1 IaC e Ambientes `dev`/`prod` | Aprovado | 15 repositorios independentes na org `Sorobanerp` com estrutura modular Terraform Docs |
| **ADR-003** | Comunicacao Hibrida REST HTTP/3 (Edge) e gRPC (East-West) | Aprovado | OpenAPI 3.1 na borda + Protobuf v1 via Service Connect |
| **ADR-004** | Padroes de Resiliencia Distribuida e Degradacao Graciosa | Aprovado | Circuit Breaker, Retry com Jitter, Timeout, Bulkhead e Idempotencia |
| **ADR-005** | Eventos Assincronos com Kafka e Transactional Outbox | Aprovado | Eliminacao de Dual Write e consumidores idempotentes |
| **ADR-006** | Isolamento Multitenant PostgreSQL 16 RLS e KMS Envelope Encryption | Aprovado | `FORCE ROW LEVEL SECURITY`, AES-256-GCM e Zero-Disk PDF |
| **ADR-007** | Arquitetura Multicloud Well-Architected e Modulos Reutilizaveis | Aprovado | Containers OCI Distroless Arm64, protocolos abertos e modulos OpenTofu puros |
| **ADR-008** | Compute Enxuto, Scale-to-Zero Bootstrap (`0/0/0`) e Trilha Kubernetes | Aprovado | ECS Fargate Spot Arm64 (`desired=0,min=0,max=0` bootstrap) + Cloud Map -> K8s |
| **ADR-009** | Ambientes `dev`/`prod`, Modularizacao OpenTofu e Worker IA Serverless | Aprovado | Separacao `environments/dev` e `prod`, Scale-to-Zero Bootstrap e Lambda Arm64 |
| **ADR-010** | Observabilidade Multi-Cloud Unificada e Auditoria Imutavel | Aprovado | OTel Tail-Based Sampling -> Datadog (`us3.datadoghq.com`) + `audit_log` |

---

## Detalhamento das Decisoes Arquiteturais

### ADR-001 -- Poliglotismo Restrito e Arquitetura Hexagonal
- **Contexto:** Escrituracao contabil ACID, parsing de PDFs em RAM, scraping de NFC-e e inferencia de IA possuem perfis computacionais distintos.
- **Decisao:** Adotar 5 stacks homologadas (**Java 25 LTS** com Virtual Threads no Core Ledger, **Go 1.27** no Ingestion BFF e Forecast Engine, **Python 3.12** no AI Worker, **Next.js 15** na Web e **Kotlin Jetpack Compose** no Android) estruturadas sob **Arquitetura Hexagonal (Ports & Adapters)** com dominio 100% livre de frameworks.

### ADR-002 -- Topologia Multi-Repo, Mapeamento 1:1 IaC e Ambientes `dev`/`prod`
- **Contexto:** Necessidade de isolamento de blast radius, states OpenTofu segregados por servico e por ambiente (`dev` e `prod`), e permissoes IAM Least Privilege.
- **Decisao:** Manter 15 repositorios independentes na organizacao `Sorobanerp`, pareando cada microsservico com seu repositorio `*-infra` dedicado (`pfm-core-ledger-infra`, `pfm-ingestion-bff-infra`, `pfm-forecast-engine-infra`, `pfm-ai-worker-infra`, `pfm-web-infra`), alem de `pfm-shared-infra`, `pfm-finops-manager-infra`, `pfm-contracts` e `pfm-docs`. Cada repositorio `*-infra` organiza seu codigo OpenTofu em `terraform/modules/` (puro, padrao Terraform Docs) e `terraform/environments/{dev,prod}/` com remote state dinamico (`pfm-shared/${var.environment}/terraform.tfstate`).

### ADR-003 -- Comunicacao Hibrida REST HTTP/3 e gRPC
- **Decisao:** Trafego Norte-Sul (Web/Mobile -> BFF) utiliza **REST sobre HTTP/2 e HTTP/3** documentado em **OpenAPI 3.1** com compressao Brotli/Gzip e ETag; trafego Leste-Oeste (BFF -> Core Ledger `:9090` e Forecast Engine `:9091`) utiliza **gRPC com Protobuf v1** e Server Reflection habilitado em ambiente local.

### ADR-004 -- Padroes de Resiliencia Distribuida
- **Decisao:** Toda chamada externa (SEFAZ, LLM) ou Leste-Oeste aplica **Timeout estrito (3s)**, **Circuit Breaker** (`gobreaker` / `Resilience4j`), **Retry com Exponential Backoff**, **Rate Limiting por Tenant** e chave `Idempotency-Key`.

### ADR-005 -- Eventos Assincronos com Kafka e Transactional Outbox
- **Decisao:** O Core Ledger grava a transacao contabil e o evento na tabela `outbox_events` na mesma transacao ACID do PostgreSQL 16, publicando de forma assincrona nos topicos `statement.raw.extracted`, `tx.categorized`, `ledger.entry.committed` e `tx.dlq`.

### ADR-006 -- Isolamento Multitenant PostgreSQL 16 RLS e KMS Envelope Encryption
- **Decisao:** Habilitar `FORCE ROW LEVEL SECURITY` em 100% das tabelas multi-tenant, criptografar dados sensiveis com chaves DEK por tenant via AWS KMS (`alias/pfm-master-key`) e processar faturas PDF exclusivamente em memoria RAM.

### ADR-007 -- Arquitetura Multicloud Well-Architected e Modulos OpenTofu Reutilizaveis (AWS / Azure / GCP)
- **Decisao:** Empacotar todos os servicos em imagens OCI Distroless (`linux/arm64`), utilizar apenas protocolos abertos (PostgreSQL Wire Protocol, Kafka Protocol, Redis RESP3, S3 API e OpenTelemetry OTLP) e estruturar todos os modulos OpenTofu segundo o padrao canônico Terraform Docs (`versions.tf`, `variables.tf`, `main.tf`, `outputs.tf`, `README.md`, sem `provider` ou `backend` hardcoded nos modulos), permitindo portabilidade direta entre **AWS**, **Microsoft Azure** e **Google Cloud Platform**.

### ADR-008 -- Compute Enxuto, Scale-to-Zero Bootstrap (`0/0/0`) e Trilha de Escala Kubernetes
- **Decisao:** Operar a fase inicial em **Amazon ECS Fargate Spot (`linux/arm64`)** no cluster `pfm-ecs-pilot` com descoberta interna via **AWS Cloud Map (`pfm.internal`)**, 2 AZs (`us-east-2a/b`) sem NAT Gateway e RDS PostgreSQL 16 `db.t4g.micro`. Todo bootstrap de infraestrutura (`dev` e `prod`) nasce com `desired_count = 0`, `min_capacity = 0` e `max_capacity = 0` (evitando `CannotPullContainerError` antes do build das imagens na `FEAT-02`/`FEAT-03` e garantindo custo zero de compute ocioso), escalando para `1/1/1` (`dev`) e `1/1/3` (`prod`) apos o push das imagens no ECR. Consulte o detalhamento financeiro em [FinOps & Custos Cloud](../05-visao-operacoes/finops-e-custos-cloud.md).

### ADR-009 -- Ambientes `dev`/`prod`, Estrutura Modular OpenTofu e Worker IA Serverless Event-Driven
- **Decisao:** Formalizar os ambientes `terraform/environments/dev` (implantado via merge na `develop`) e `terraform/environments/prod` (implantado via merge na `main` com aprovacao manual), com Scale-to-Zero Bootstrap (`0/0/0`) e execucao do `pfm-ai-worker-python` como funcao **AWS Lambda Arm64 (`pfm-ai-worker-python-${var.environment}`)** orientada a eventos e isolada do PostgreSQL. Veja o documento dedicado em [ADR-009 Detalhado](../02-arquitetura-adrs/ADR-009-ambientes-dev-prod-e-estrutura-modular-opentofu.md).

### ADR-010 -- Observabilidade Multi-Cloud Unificada e Auditoria Imutavel
- **Decisao:** Padronizar telemetria via **OpenTelemetry Collector** com **Tail-Based Sampling** (retendo 100% dos traces com `ERROR` ou latencia `> 500ms` e 10% dos traces `OK`), mascara automatica de PII (`Redaction Processor`), exportacao OTLP para o **Datadog (`us3.datadoghq.com`)** e auditoria imutavel na tabela `audit_log`.

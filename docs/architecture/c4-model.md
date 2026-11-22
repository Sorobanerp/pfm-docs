# Modelo C4 & Topologia Oficial Multi-Repo (V3)

Esta secao apresenta a arquitetura da plataforma **PFM Core Banking (Versao 3.0 -- Production-Ready FinOps & Multi-Cloud)** atraves do **Modelo C4 (Context, Containers, Components)**, a topologia oficial dos repositorios do ecossistema e a trilha evolutiva de computacao **Serverless/Containers Enxutos $\rightarrow$ Hiperescala Kubernetes**.

---

## 1. C4 Nivel 1 -- Diagrama de Contexto do Sistema

O diagrama de contexto ilustra como titulares, membros familiares e administradores SaaS interagem com a plataforma PFM Core Banking e como o sistema se integra de forma resiliente aos provedores externos (SEFAZ Estaduais, Provedores de IA/LLM, Emissores Bancarios, Datadog e SonarCloud).

```mermaid
flowchart TB
    USER[" Titular & Familia (OWNER / MEMBER / VIEWER)<br/>[Person]<br/>Gerencia financas, cartoes, orcamentos,<br/>faturas PDF, notas NFC-e e perfil LGPD."]
    ADMIN[" Administrador SaaS (PLATFORM_ADMIN)<br/>[Person]<br/>Gere planos, assinaturas, quotas e metricas<br/>globais sem acesso a dados financeiros privados."]

    subgraph Enterprise["Boundary: Ecossistema PFM Core Banking (V3)"]
        PFM[" Plataforma PFM Core Banking<br/>[Software System]<br/>Core contabil multitenant (RLS + KMS),<br/>ingestao PDF em RAM, NFC-e offline-first,<br/>Worker IA Serverless (Lambda Arm64) e Audit Log imutavel."]
    end

    SEFAZ[" Portais SEFAZ Estaduais<br/>[External System]<br/>Consulta publica de cupons fiscais<br/>eletronicos (NFC-e / SAT) via Chave/QR Code."]
    LLM[" Provedor Cloud LLM (Bedrock / Vertex / OpenAI)<br/>[External System]<br/>Inferencia semantica de fallback (Camada 3)<br/>para descricoes financeiras anonimizadas."]
    OPENFIN[" Instituicoes Financeiras / OFX & PDF<br/>[External System]<br/>Emissores de cartoes e extratos bancarios."]
    OBS[" Datadog Unified & SonarCloud Portfolio<br/>[External Systems]<br/>APM/Logs/Metricas via OTel Tail Sampling<br/>e Quality Gate SAST/Cobertura >= 95%."]

    USER -->|"HTTPS / HTTP/3<br/>Upload PDF, Scan QR NFC-e,<br/>Orcamento, Conciliacao & LGPD"| PFM
    ADMIN -->|"HTTPS / OIDC<br/>Gestao SaaS Admin (Zero-PII)"| PFM
    PFM -->|"HTTPS Scraping Resiliente<br/>(Circuit Breaker + Retries)"| SEFAZ
    PFM -->|"HTTPS Anonimizado<br/>(Zero PII)"| LLM
    USER -.->|"Obtem Fatura PDF / Extrato"| OPENFIN
    PFM -->|"OTLP Tail-Sampled & SAST Reports"| OBS
```

---

## 2. C4 Nivel 2 -- Diagrama de Conteineres (Topologia V3 FinOps & Serverless)

O Nivel 2 detalha os conteineres e funcoes serverless da arquitetura V3, destacando o uso de **AWS ECS Fargate Spot (Arm64)** com **Service Connect (`pfm.internal`)**, o worker de IA como **AWS Lambda Arm64 Event-Driven (ADR-009)** sem conexao direta ao PostgreSQL, mensageria/cache em **Upstash Serverless** e coleta unificada via **OpenTelemetry Collector (ADR-010)**.

```mermaid
flowchart TB
    subgraph Clients["Canais de Entrada (Frontends)"]
        WEB[" pfm-web-nextjs<br/>[Container: Next.js 15 / TypeScript]<br/>Portal Executivo, SaaS Admin (US-12)<br/>e Central Perfil/Familia (US-13)."]
        MOB[" pfm-mobile-android<br/>[App: Kotlin / Jetpack Compose]<br/>App Offline-First, scanner QR NFC-e<br/>e banco local SQLCipher."]
    end

    subgraph EdgeLayer["Borda, Identidade & Roteamento"]
        GW[" Edge ALB / Envoy Gateway<br/>[Container / Managed L7]<br/>Terminacao TLS 1.3 / HTTP/3, Rate Limiting,<br/>Validacao JWT OIDC e Roteamento."]
    end

    subgraph EcsPilot["Compute Enxuto (ECS Fargate Spot Arm64 / ACA / Cloud Run) + Service Connect (pfm.internal)"]
        BFF[" pfm-ingestion-bff-go<br/>[Container: Golang 1.24]<br/>BFF REST/gRPC, PDF Parser 100% em RAM<br/>(Zero-Disk) e Scraper SEFAZ NFC-e."]
        LEDGER[" pfm-core-ledger-java<br/>[Container: Java 25 LTS / Spring Boot 3.4]<br/>Partidas dobradas, Competencia/Caixa (RN01),<br/>Cartoes/Estornos, Conciliacao e Audit Log."]
        FORECAST[" pfm-forecast-engine-go<br/>[Container: Golang 1.24]<br/>Motor de Projecao Preditiva (30/60/90d)<br/>e Alertas de Limiar de Orcamento."]
    end

    subgraph ServerlessAI["Compute IA Event-Driven (ADR-009 -- Custo $0 Ocioso)"]
        AI[" pfm-ai-worker-python<br/>[AWS Lambda Arm64 / Python 3.12]<br/>Pipeline IA 3 Camadas (L1/L2 ONNX/L3 LLM)<br/>ISOLADO: Sem conexao direta ao PostgreSQL."]
    end

    subgraph DataAndMessaging["Persistencia Isolada & Backbone Serverless (Upstash + RDS)"]
        PG[(" Amazon RDS PostgreSQL 16 (RLS + KMS)<br/>[Database: db.t4g.micro -> Aurora HA]<br/>Isolamento Row-Level Security por tenant_id,<br/>Outbox e tabela audit_log append-only.")]
        REDIS[(" Upstash Redis / Valkey Serverless<br/>[In-Memory Serverless Cache]<br/>Chaves Idempotencia (72h),<br/>Cache L1 Categorizacao e Rate Limit.")]
        KAFKA[[" Upstash Kafka Serverless<br/>[Event Streaming Backbone]<br/>Topicos particionados por tenant_id<br/>+ Dead Letter Queues (DLQ Cifradas KMS)."]]
    end

    subgraph Observability["Observabilidade Unificada (ADR-010)"]
        OTEL[" OpenTelemetry Collector<br/>[Redaction + Tail-Based Sampling]<br/>100% Erros & Latencia > 500ms | 5-10% Sucessos"]
        DD[" Datadog Unified Dashboard<br/>[Multi-Cloud APM & Jornadas UC-01..08]"]
    end

    WEB -->|"REST HTTP/3 (JSON)"| GW
    MOB -->|"REST HTTP/3 (JSON)"| GW
    GW -->|"HTTP/gRPC"| BFF
    GW -->|"HTTP/SSR"| WEB

    BFF -->|"gRPC Service Connect (pfm.internal)"| LEDGER
    BFF -->|"gRPC Service Connect (pfm.internal)"| FORECAST
    LEDGER -->|"gRPC Service Connect (pfm.internal)"| FORECAST

    LEDGER -->|"ACID + RLS + audit_log"| PG
    BFF <-->|"RESP3"| REDIS
    LEDGER <-->|"RESP3"| REDIS

    PG -.->|"Outbox Relay"| KAFKA
    BFF -->|"Produce Events"| KAFKA
    KAFKA -->|"Trigger Event-Driven"| AI
    AI <-->|"RESP3 (L1 Cache)"| REDIS
    AI -->|"Produce CategorizedEvent / gRPC"| KAFKA
    KAFKA -->|"Consume Events"| LEDGER
    KAFKA -->|"Consume Events"| FORECAST

    BFF -.->|"OTLP/gRPC"| OTEL
    LEDGER -.->|"OTLP/gRPC"| OTEL
    FORECAST -.->|"OTLP/gRPC"| OTEL
    AI -.->|"OTLP/gRPC"| OTEL
    OTEL -->|"Sanitized OTLP"| DD
```

---

## 3. C4 Nivel 3 -- Diagrama de Componentes Hexagonais (`pfm-core-ledger-java`)

O Nivel 3 demonstra a estrutura interna padronizada utilizando **Arquitetura Hexagonal (Ports & Adapters)**, garantindo que o dominio contabil permaneca 100% livre de frameworks e SDKs de nuvem, enquanto os *Outbound Adapters* aplicam RLS, Envelope Encryption KMS e gravacao imutavel no `audit_log`.

```mermaid
flowchart TB
    subgraph InboundAdapters["Adapters Layer -- Inbound (Driving Adapters)"]
        GRPC_IN["LedgerGrpcController<br/>[gRPC Inbound Adapter]<br/>Recebe comandos Protobuf v3 via Service Connect."]
        KAFKA_IN["TransactionEventConsumer<br/>[Kafka Inbound Adapter]<br/>Consome eventos de PDF/NFC-e e CategorizedEvent (Lambda IA)."]
    end

    subgraph ApplicationLayer["Application Layer -- Use Cases & Ports"]
        IN_PORT["&lt;&lt;Interface&gt;&gt;<br/>RecordTransactionUseCase<br/>[Inbound Port]"]
        UC_IMPL["LedgerApplicationService<br/>[Use Case Orchestrator]<br/>Orquestra transacao, idempotencia e trilha de auditoria."]
        OUT_REPO["&lt;&lt;Interface&gt;&gt;<br/>LedgerRepositoryPort<br/>[Outbound Port]"]
        OUT_AUDIT["&lt;&lt;Interface&gt;&gt;<br/>ImmutableAuditLogPort<br/>[Outbound Port]"]
        OUT_OUTBOX["&lt;&lt;Interface&gt;&gt;<br/>OutboxEventPublisherPort<br/>[Outbound Port]"]
        OUT_IDEMP["&lt;&lt;Interface&gt;&gt;<br/>IdempotencyStorePort<br/>[Outbound Port]"]
    end

    subgraph DomainCore["Domain Core -- 100% Pure Java 25 (Zero Framework Dependencies)"]
        AGG["LedgerEntryAggregate<br/>[Domain Aggregate]<br/>Invariantes contabeis, Competencia vs. Caixa (RN01)."]
        VO_MONEY["MoneyValueObject<br/>[Value Object]<br/>BigDecimal NUMERIC(19,4) + ROUND_HALF_EVEN (RN06)."]
        POL_REFUND["RefundAdjustmentPolicy<br/>[Domain Policy]<br/>Estorno parcial/total e vinculo original (RN03)."]
        TAXONOMY["TwoLevelCategoryValidator<br/>[Domain Specification]<br/>Valida Taxonomia Oficial Nivel 1 + Nivel 2."]
    end

    subgraph OutboundAdapters["Adapters Layer -- Outbound (Driven Adapters)"]
        PG_ADAPTER["PostgresRlsLedgerAdapter<br/>[PostgreSQL Outbound Adapter]<br/>SET LOCAL app.current_tenant_id, persiste Ledger + Outbox + audit_log."]
        REDIS_ADAPTER["RedisIdempotencyAdapter<br/>[Upstash Redis Adapter]<br/>Lock distribuido e cache de resposta idempotente."]
    end

    GRPC_IN --> IN_PORT
    KAFKA_IN --> IN_PORT
    IN_PORT --> UC_IMPL

    UC_IMPL --> AGG
    AGG --> VO_MONEY
    AGG --> POL_REFUND
    AGG --> TAXONOMY

    UC_IMPL --> OUT_IDEMP
    UC_IMPL --> OUT_REPO
    UC_IMPL --> OUT_AUDIT
    UC_IMPL --> OUT_OUTBOX

    OUT_IDEMP --> REDIS_ADAPTER
    OUT_REPO --> PG_ADAPTER
    OUT_AUDIT --> PG_ADAPTER
    OUT_OUTBOX --> PG_ADAPTER
```

---

## 4. Tabela Oficial dos Repositorios da Plataforma

A governanca de codigo da plataforma **PFM Core Banking** opera sob topologia Multi-Repo na organizacao GitHub [`Sorobanerp`](https://github.com/Sorobanerp), com mapeamento 1:1 entre servicos de aplicacao e modulos dedicados de infraestrutura (`*-infra`):

| # | Repositorio | Categoria | Stack / Tecnologia Principal | Responsabilidade Arquitetural & Escopo |
| :-: | :--- | :--- | :--- | :--- |
| **01** | `pfm-contracts` | Contratos & Schemas | OpenAPI 3.1, Protobuf v3, JSON Schema / Avro | Fonte unica da verdade (*Single Source of Truth*) para APIs REST, gRPC (`TenantAdminService`, `UserProfileService`, `LedgerService`) e eventos Kafka. |
| **02** | `pfm-core-ledger-java` | Core Banking | Java 25 LTS, Spring Boot 3.4, PostgreSQL RLS | Escrituracao contabil ACID, Competencia vs. Caixa (**RN01**), Parcelas/Estornos (**RN02/RN03/RN06**), Conciliacao (**RN04**), SaaS Admin, LGPD e `audit_log` append-only. |
| **03** | `pfm-ingestion-bff-go` | Ingestao & BFF | Golang 1.24+, HTTP/3, gRPC, `bytes.Reader` | API BFF, parsing de faturas PDF **100% em memoria RAM** (**ADR-006**) e Scraper SEFAZ NFC-e resiliente. |
| **04** | `pfm-forecast-engine-go` | Projecao & Alertas | Golang 1.24+, gRPC, Kafka | Motor preditivo de fluxo de caixa (30/60/90 dias), calculo de *burn rate* de orcamento e disparo de alertas (80% / 100%). |
| **05** | `pfm-ai-worker-python` | IA Serverless | Python 3.12+, AWS Lambda Arm64, ONNX, LLM | Pipeline de categorizacao em 3 camadas (L1 Redis $\rightarrow$ L2 ONNX $\rightarrow$ L3 LLM Anonimizado), **sem acesso direto ao PostgreSQL (ADR-009)**. |
| **06** | `pfm-web-nextjs` | Frontend Web | Next.js 15, React 19, TypeScript, TailwindCSS | Portal Web "Organic Financial Pulse", dashboards Competencia vs. Caixa, Painel SaaS Admin (`UC-07`) e Central Perfil/Familia (`UC-08`). |
| **07** | `pfm-mobile-android` | Frontend Mobile | Kotlin, Jetpack Compose, Room/SQLCipher, CameraX | App nativo **Offline-First** com leitor QR Code NFC-e instantaneo, cofre local cifrado e sincronizacao via WorkManager. |
| **08** | `pfm-shared-infra` | Infra Compartilhada | OpenTofu, AWS ECS Fargate Spot, Service Connect, RDS, KMS | Landing Zone VPC, Cluster ECS `pfm-pilot-prod`, Cloud Map `pfm.internal`, RDS PostgreSQL, KMS, S3 criptografado, Secrets Upstash e trilha EKS condicional. |
| **09** | `pfm-core-ledger-infra` | Infra Dedicada 1:1 | OpenTofu, ECS Service / Helm, Auto Scaling | Task Definition Arm64, Service Connect (`pfm-core-ledger-java.pfm.internal:18200`), IAM Least Privilege e Auto-Rollback S3. |
| **10** | `pfm-ingestion-bff-infra` | Infra Dedicada 1:1 | OpenTofu, ECS Service / Helm, Auto Scaling | Task Definition Arm64, Service Connect (`pfm-ingestion-bff-go.pfm.internal:18080`), IAM KMS/S3 e Auto-Rollback S3. |
| **11** | `pfm-forecast-engine-infra` | Infra Dedicada 1:1 | OpenTofu, ECS Service / Helm, Auto Scaling | Task Definition Arm64, Service Connect (`pfm-forecast-engine-go.pfm.internal:18110`) e Auto-Rollback S3. |
| **12** | `pfm-ai-worker-infra` | Infra Dedicada 1:1 | OpenTofu, AWS Lambda Arm64 / ECS (`desired=0`) | Provisionamento Serverless Event-Driven (custo $0 ocioso) e triggers Kafka/SQS + DLQ cifrada. |
| **13** | `pfm-web-infra` | Infra Dedicada 1:1 | OpenTofu, ECS Service / Helm, Auto Scaling | Task Definition Arm64, Service Connect (`pfm-web-nextjs.pfm.internal:3000`) e Auto-Rollback S3. |
| **14** | `pfm-finops-manager-infra` | Governanca FinOps | Python 3.12, AWS Lambda Arm64, EventBridge | Orquestracao automatica de `stop` (20h30 BRT), `start` (06h00 BRT), `audit` (run-rate USD) e *circuit-breaker* de orcamento. |
| **15** | `pfm-docs` | Governanca & Docs | MkDocs Material, Mermaid.js, GitHub Actions | Portal de **Docs-as-Code** V3 (Visao Executiva, ADRs V3, Modelo C4, Fluxos, PRD, Backlog BDD e SRE/FinOps). |

---

## 5. Topologia de Portas: Ambiente Local (Host) vs. Cloud

A plataforma adota o principio **12-Factor App (Port Binding via Environment Variables)** para evitar colisoes locais (ex.: Portainer na porta `8000`) e padronizar o roteamento em producao:

| Componente / Servico | Host Local | Cloud (`pfm.internal` / K8s) | Protocolo | Variavel de Ambiente (12-Factor) |
| :--- | :---: | :---: | :---: | :--- |
| **`pfm-docs`** (MkDocs) | `18000` | `8000` | HTTP | `PORT=18000` (`Makefile`) |
| **`pfm-web-nextjs`** | `18300` | `3000` | HTTP | `PORT=18300`, `NEXT_PUBLIC_API_URL` |
| **`pfm-envoy-gateway`** | `18080` | `8080` | HTTP/2, HTTP/3 | Mapeamento Docker `18080:8080` |
| **`pfm-ingestion-bff-go`** | `18100` | `18080` / `8080` | HTTP / gRPC | `SERVER_PORT=18100` |
| **`pfm-forecast-engine-go`** | `18110` | `18110` / `9090` | gRPC / HTTP | `GRPC_PORT=18110` |
| **`pfm-core-ledger-java` (HTTP)** | `18200` | `18200` / `8080` | HTTP | `SERVER_PORT=18200` |
| **`pfm-core-ledger-java` (gRPC)** | `18210` | `9090` | gRPC | `GRPC_SERVER_PORT=18210` |
| **`pfm-ai-worker-python`** | `18400` | `18090` / Lambda | Event / HTTP | `WORKER_PORT=18400` |
| **`postgres-core-ledger`** | `15432` | `5432` | TCP/SQL | `DB_URL` |
| **`pfm-redis`** (Valkey / Upstash) | `16379` | `6379` (TLS) | RESP3 | `REDIS_ADDR` |
| **`pfm-kafka`** (KRaft / Upstash) | `19092` | `9092` (SASL/TLS) | TCP | `KAFKA_BROKERS` |
| **`pfm-localstack`** | `14566` | AWS Endpoints | HTTP/HTTPS | `AWS_ENDPOINT_URL` |

---

## 6. Trilha Evolutiva Multi-Cloud: Producao Inicial $\rightarrow$ Hiperescala Kubernetes (ADR-008)

Gracas ao empacotamento em imagens **OCI Distroless (`linux/arm64`)** e protocolos abertos, a plataforma evolui sem reescrita de codigo em 3 estagios financeiros:

```mermaid
flowchart LR
    subgraph Stage1["Estagio 1: Piloto / Producao Inicial (US$ 12--24/mes)"]
        direction TB
        C1["AWS: ECS Fargate Spot (Arm64)<br/>Azure: Container Apps | GCP: Cloud Run"]
        AI1["AI Worker: AWS Lambda Arm64 ($0 ocioso)"]
        MSG1["Upstash Kafka & Redis Serverless"]
        DB1["RDS PostgreSQL db.t4g.micro (Park Noturno)"]
    end

    subgraph Stage2["Estagio 2: Escala 100 Tenants (~US$ 115/mes)"]
        direction TB
        C2["ECS Fargate Spot / ACA / Cloud Run (24x7 Ativo)"]
        AI2["Lambda Arm64 Concorrencia Reservada"]
        MSG2["Upstash Pro / Serverless Dedicated"]
        DB2["RDS Aurora Serverless v2 / Multi-AZ"]
    end

    subgraph Stage3["Estagio 3: Hiperescala 500+ Tenants (~US$ 420/mes)"]
        direction TB
        C3["Kubernetes: EKS / AKS / GKE<br/>+ Karpenter Spot + KEDA Autoscaling"]
        AI3["Lambda / Knative / KEDA Event Workers"]
        MSG3["Amazon MSK / Confluent / Strimzi Multi-AZ"]
        DB3["Aurora PostgreSQL Multi-AZ + Read Replicas"]
    end

    Stage1 -->|"OpenTofu Toggle<br/>Zero Mudanca de Codigo"| Stage2
    Stage2 -->|"compute_engine = 'eks'<br/>Helm Charts Ja Versionados"| Stage3
```

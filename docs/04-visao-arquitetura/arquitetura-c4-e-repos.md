# 4.1. Arquitetura C4 (Niveis 1 a 3) e Catalogo dos 15 Repositorios

<span class="badge-green">Artefato 03 - Modelo C4 &amp; Topologia Multi-Repo</span>
<span class="badge-glow">Hexagonal Ports &amp; Adapters</span>

Este documento apresenta a arquitetura de software da plataforma **PFM Core Banking (V3)** atraves do **Modelo C4 (Contexto, Conteineres e Componentes)** e o catalogo oficial dos **15 repositorios** na organizacao GitHub `Sorobanerp`.

!!! note "Governanca FinOps Centralizada"
    Todas as estimativas financeiras de infraestrutura cloud e comparativos de estagios operacionais estao consolidados exclusivamente em [5.3. FinOps & Custos Cloud](../05-visao-operacoes/finops-e-custos-cloud.md).

---

## 1. C4 Nivel 1 -- Diagrama de Contexto do Sistema

```mermaid
flowchart TB
    USER["Titular & Familia (OWNER / MEMBER / VIEWER)<br/>[Person]<br/>Gerencia financas, cartoes, orcamentos,<br/>faturas PDF, notas NFC-e e perfil LGPD."]
    ADMIN["Administrador SaaS (PLATFORM_ADMIN)<br/>[Person]<br/>Gere planos, assinaturas e quotas<br/>sem acesso a dados financeiros privados."]

    subgraph Enterprise["Boundary: Ecossistema PFM Core Banking (V3)"]
        PFM["Plataforma PFM Core Banking<br/>[Software System]<br/>Core contabil multitenant (RLS + KMS),<br/>ingestao PDF em RAM, NFC-e offline-first,<br/>Worker IA Serverless e Audit Log imutavel."]
    end

    SEFAZ["Portais SEFAZ Estaduais<br/>[External System]<br/>Consulta publica de cupons fiscais<br/>eletronicos (NFC-e) via Chave/QR Code."]
    LLM["Provedor Cloud LLM (Gemini / Bedrock)<br/>[External System]<br/>Inferencia semantica de fallback (Camada 3)<br/>para descricoes financeiras anonimizadas."]
    OBS["Datadog Unified & SonarCloud Portfolio<br/>[External Systems]<br/>APM/Logs/Metricas via OTel Tail Sampling<br/>e Quality Gate SAST/Cobertura."]

    USER -->|"HTTPS / HTTP/3 (OpenAPI 3.1)"| PFM
    ADMIN -->|"HTTPS / OIDC (Zero-PII)"| PFM
    PFM -->|"HTTPS Scraping Resiliente"| SEFAZ
    PFM -->|"HTTPS Anonimizado (Zero PII)"| LLM
    PFM -->|"OTLP Tail-Sampled & SAST"| OBS
```

---

## 2. C4 Nivel 2 -- Diagrama de Conteineres (ECS Fargate Spot + Service Connect + Lambda IA)

```mermaid
flowchart TB
    subgraph Clients["Canais de Entrada (Frontends)"]
        WEB["pfm-web-nextjs<br/>[Container: Next.js 15 / TypeScript]<br/>Portal Executivo, SaaS Admin (US-12)<br/>e Central Perfil/Familia (US-13)."]
        MOB["pfm-mobile-android<br/>[App: Kotlin / Jetpack Compose]<br/>App Offline-First, scanner QR NFC-e<br/>e banco local SQLCipher."]
    end

    subgraph EcsPilot["Cluster ECS Fargate Spot Arm64 (pfm-ecs-pilot) + AWS Cloud Map (pfm.internal)"]
        BFF["pfm-ingestion-bff-go<br/>[Container: Go 1.27]<br/>BFF REST/gRPC, Swagger UI OpenAPI 3.1,<br/>PDF Parser 100% em RAM e Scraper NFC-e."]
        LEDGER["pfm-core-ledger-java<br/>[Container: Java 25 LTS / Spring Boot 3.5]<br/>Partidas dobradas, Competencia/Caixa (RN01),<br/>Parcelas/Estornos, RLS e Audit Log."]
        FORECAST["pfm-forecast-engine-go<br/>[Container: Go 1.27]<br/>Motor de Projecao Preditiva (30/60/90d)<br/>e Simulador SAC/Price/Consorcio."]
    end

    subgraph ServerlessAI["Compute IA Event-Driven (ADR-009)"]
        AI["pfm-ai-worker-python<br/>[AWS Lambda Arm64 / Python 3.12]<br/>Pipeline IA 3 Camadas (L1/L2/L3)<br/>ISOLADO: Sem conexao direta ao PostgreSQL."]
    end

    subgraph DataAndMessaging["Persistencia Isolada & Backbone de Eventos"]
        PG[("Amazon RDS PostgreSQL 16 (RLS + KMS)<br/>[Database: db.t4g.micro]<br/>Isolamento FORCE ROW LEVEL SECURITY,<br/>Outbox e tabela audit_log append-only.")]
        REDIS[("Redis / Valkey Serverless<br/>[In-Memory Cache]<br/>Chaves de Idempotencia (72h),<br/>Cache L1 e Rate Limit.")]
        KAFKA[["Kafka Event Backbone<br/>[Event Streaming]<br/>Topicos particionados por tenant_id<br/>+ Dead Letter Queues cifradas via KMS."]]
    end

    WEB -->|"REST HTTP/2 & HTTP/3"| BFF
    MOB -->|"REST HTTP/2 & HTTP/3"| BFF

    BFF -->|"gRPC Service Connect (:9090)"| LEDGER
    BFF -->|"gRPC Service Connect (:9091)"| FORECAST

    LEDGER -->|"ACID + FORCE RLS + audit_log"| PG
    BFF <-->|"RESP3"| REDIS
    FORECAST <-->|"RESP3"| REDIS

    BFF -->|"statement.raw.extracted"| KAFKA
    KAFKA -->|"Event Trigger"| AI
    AI -->|"tx.categorized"| KAFKA
    KAFKA -->|"Consume Events"| LEDGER
    LEDGER -->|"ledger.entry.committed"| KAFKA
    KAFKA -->|"Consume Events"| FORECAST
```

---

## 3. C4 Nivel 3 -- Diagrama de Componentes Hexagonais (`pfm-core-ledger-java`)

```mermaid
flowchart TB
    subgraph InboundAdapters["Inbound Adapters (Driving)"]
        GRPC_IN["CoreLedgerGrpcServerAdapter (:9090)<br/>UserProfileGrpcServerAdapter<br/>TenantAdminGrpcServerAdapter"]
        KAFKA_IN["CategorizedTransactionKafkaConsumer<br/>(Topico: tx.categorized)"]
    end

    subgraph ApplicationLayer["Application Layer (Use Cases & Ports)"]
        IN_PORT["RecordLedgerEntryUseCase<br/>GetTenantFinancialSummaryUseCase<br/>UserProfileUseCase / TenantAdminUseCase"]
        OUT_PORT["LedgerEntryRepositoryPort<br/>AuditLogRepositoryPort<br/>EnvelopeEncryptionKmsPort"]
    end

    subgraph DomainCore["Domain Core (100% Pure Java 25 -- Zero Framework Dependencies)"]
        DOM["DoubleEntryLedgerService<br/>InstallmentSplitter (RN06)<br/>RefundHandler (RN03)<br/>Money (BigDecimal NUMERIC 19,4)"]
    end

    subgraph OutboundAdapters["Outbound Adapters (Driven)"]
        PG_OUT["PostgresRlsLedgerRepositoryAdapter<br/>PostgresRlsAuditLogAdapter<br/>(SET LOCAL app.current_tenant_id)"]
        KMS_OUT["AesGcmEnvelopeEncryptionKmsAdapter<br/>(AWS KMS alias/pfm-master-key)"]
    end

    GRPC_IN --> IN_PORT
    KAFKA_IN --> IN_PORT
    IN_PORT --> DOM
    IN_PORT --> OUT_PORT
    OUT_PORT --> PG_OUT
    OUT_PORT --> KMS_OUT
```

---

## 4. Catalogo Oficial dos 15 Repositorios (`Sorobanerp`)

| # | Repositorio | Categoria | Stack Principal | Responsabilidade Arquitetural |
| :-: | :--- | :--- | :--- | :--- |
| **01** | `pfm-docs` | Governanca & Docs | MkDocs Material 3, Python | Portal Institucional Pulse Docs (5 Visoes Executivas, Linter ASCII e GitHub Pages). |
| **02** | `pfm-contracts` | Contratos & Schemas | Protobuf v1, OpenAPI 3.1 | Fonte unica da verdade para contratos gRPC e especificacao `openapi/openapi.yaml`. |
| **03** | `pfm-shared-infra` | Infra Compartilhada | OpenTofu, Docker Compose | VPC 2 AZs (`us-east-2a/b`, 0 NAT), Cluster ECS `pfm-ecs-pilot`, Cloud Map `pfm.internal`, RDS, KMS e S3. |
| **04** | `pfm-finops-manager-infra` | Automacao FinOps | Python 3.12 Arm64, OpenTofu | Lambda `pfm-finops-manager` (`stop`, `start`, `audit` e `cost_guardrails`) + EventBridge Schedules. |
| **05** | `pfm-core-ledger-java` | Core Banking | Java 25 LTS, Spring Boot 3.5 | Partidas dobradas, Competencia vs. Caixa (`RN01`), Parcelas/Estornos (`RN06`), RLS e gRPC `:9090`. |
| **06** | `pfm-core-ledger-infra` | Infra Dedicada 1:1 | OpenTofu (ECS Fargate Spot) | Task Definition Arm64, Service Connect, Auto Scaling e IAM Least Privilege do Core Ledger. |
| **07** | `pfm-ingestion-bff-go` | Ingestao & BFF | Go 1.27, HTTP/2, Swagger UI | Upload PDF em RAM (`Zero-Disk`), Scraper SEFAZ NFC-e, Bridge gRPC e Swagger `:8080`. |
| **08** | `pfm-ingestion-bff-infra` | Infra Dedicada 1:1 | OpenTofu (ECS Fargate Spot) | Task Definition Arm64, Service Connect e IAM de acesso ao bucket S3 compartilhado e KMS. |
| **09** | `pfm-forecast-engine-go` | Projecao & Contratos | Go 1.27, `shopspring/decimal` | Projecao Run-Rate (30/60/90d) e Simulador SAC/Price/Consorcio com gRPC Reflection `:9091`. |
| **10** | `pfm-forecast-engine-infra` | Infra Dedicada 1:1 | OpenTofu (ECS Fargate Spot) | Task Definition Arm64, Service Connect e IAM Least Privilege do Forecast Engine. |
| **11** | `pfm-ai-worker-python` | IA Serverless | Python 3.12, Pydantic v2 | Funil de categorizacao em 3 camadas sem conexao direta ao PostgreSQL (`ADR-009`). |
| **12** | `pfm-ai-worker-infra` | Infra Dedicada 1:1 | OpenTofu (AWS Lambda Arm64) | Funcao Serverless `pfm-ai-worker-python-prod`, fila SQS DLQ cifrada e Secrets Manager. |
| **13** | `pfm-web-nextjs` | Frontend Web | Next.js 15, React 19, Tailwind | Experiencia Web Full-Viewport com as 6 jornadas do IDS "PFM Pulse". |
| **14** | `pfm-web-infra` | Infra Dedicada 1:1 | OpenTofu (ECS Fargate Spot) | Task Definition Arm64 e infraestrutura dedicada do Portal Web. |
| **15** | `pfm-mobile-android` | Frontend Mobile | Kotlin 2.1, Jetpack Compose | Aplicativo Android Material 3 Offline-First com Scanner NFC-e e SQLCipher. |

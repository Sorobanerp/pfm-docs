# Modelo C4 & Topologia Oficial Multi-Repo (14 Repositórios)

Esta seção apresenta a arquitetura da plataforma **PFM Core Banking** através do **Modelo C4 (Context, Containers, Components)** e a tabela oficial dos **14 repositórios** que compõem o ecossistema.

---

## 1. C4 Nível 1 — Diagrama de Contexto do Sistema

O diagrama de contexto ilustra como o titular da conta interage com a plataforma PFM Core Banking e como o sistema se integra de forma resiliente aos provedores externos (SEFAZ Estaduais, Provedores de IA/LLM, Emissores Bancários/Open Finance e Serviços de Mensageria Push/Email).

```mermaid
flowchart TB
    USER["👤 Titular da Conta (PFM User)<br/>[Person]<br/>Gerencia finanças pessoais, cartões,<br/>orçamentos, faturas PDF e notas NFC-e."]

    subgraph Enterprise["Boundary: Ecossistema PFM Core Banking"]
        PFM["🏦 Plataforma PFM Core Banking<br/>[Software System]<br/>Core contábil multitenant (Regime de Competência vs. Caixa),<br/>ingestão PDF em RAM, captura NFC-e offline-first,<br/>categorização IA em 3 camadas e conciliação."]
    end

    SEFAZ["🏛️ Portais SEFAZ Estaduais<br/>[External System]<br/>Consulta pública de cupons fiscais<br/>eletrônicos (NFC-e / SAT) via Chave/QR Code."]
    LLM["🧠 Provedor Cloud LLM (Vertex AI / Bedrock / OpenAI)<br/>[External System]<br/>Inferência semântica de fallback (Camada 3)<br/>para descrições financeiras ambíguas."]
    OPENFIN["💳 Instituições Financeiras / OFX & PDF<br/>[External System]<br/>Emissores de cartões e extratos bancários<br/>importados para conciliação."]
    PUSH["📨 Provedor Push / Email (FCM / APNs / SES)<br/>[External System]<br/>Entrega de alertas de orçamento,<br/>fechamento de fatura e anomalias."]

    USER -->|"HTTPS / HTTP/3<br/>Upload de Fatura PDF, Scan QR NFC-e,<br/>Gestão de Orçamento e Extrato"| PFM
    PFM -->|"HTTPS Scraping Resiliente<br/>(Circuit Breaker + Retries)"| SEFAZ
    PFM -->|"HTTPS / gRPC Anonimizado<br/>(Zero PII)"| LLM
    USER -.->|"Obtém Fatura PDF / Extrato"| OPENFIN
    PFM -->|"HTTPS / SMTP<br/>Notificações Transacionais"| PUSH
```

---

## 2. C4 Nível 2 — Diagrama de Contêineres (Topologia Multi-Repo)

O Nível 2 detalha os contêineres de execução mapeados diretamente para os repositórios da arquitetura Multi-Repo, destacando os protocolos de comunicação (`REST HTTP/3`, `gRPC mTLS` e `Apache Kafka`).

```mermaid
flowchart TB
    subgraph Clients["Canais de Entrada (Frontends)"]
        WEB["💻 pfm-web-portal<br/>[Container: Next.js 15 / TypeScript]<br/>Dashboard executivo SSR, análise de<br/>Competência vs. Caixa e Conciliação."]
        MOB["📱 pfm-mobile-android<br/>[Container: Kotlin / Jetpack Compose]<br/>App Offline-First, scanner QR NFC-e<br/>e banco local SQLCipher."]
    end

    subgraph EdgeLayer["Camada de Borda & Identidade"]
        GW["🛡️ pfm-api-gateway<br/>[Container: Envoy / Kong + OAuth2/OIDC]<br/>Terminação HTTP/3, Rate Limiting por Tenant,<br/>Validação JWT e Roteamento gRPC."]
    end

    subgraph CoreServices["Domínio Core Banking (Java 25 LTS + Virtual Threads)"]
        LEDGER["📒 pfm-ledger-service<br/>[Container: Java 25 / Spring Boot 3.4]<br/>Partidas dobradas, Regime Competência/Caixa,<br/>NUMERIC(19,4) e Idempotência."]
        CARDS["💳 pfm-cards-service<br/>[Container: Java 25 / Spring Boot 3.4]<br/>Ciclo de vida de faturas, limite total,<br/>parcelamentos e estornos (RN03)."]
        BUDGET["🎯 pfm-budget-service<br/>[Container: Java 25 / Spring Boot 3.4]<br/>Teto de gastos por categoria (RN02),<br/>projeções e alertas de consumo."]
        RECON["🔄 pfm-reconcile-service<br/>[Container: Java 25 / Spring Boot 3.4]<br/>Motor de conciliação automática e manual<br/>entre NFC-e, faturas PDF e extrato (RN04)."]
        NOTIF["🔔 pfm-notification-service<br/>[Container: Java 25 / Spring Boot 3.4]<br/>Despacho de alertas multicanal<br/>(Push, Email, Webhook)."]
    end

    subgraph IngestionAndAI["Ingestão de Alta Vazão (Golang) & Inteligência (Python)"]
        PDF["📄 pfm-ingestion-pdf-service<br/>[Container: Golang 1.24]<br/>Stream parser de faturas PDF 100% em RAM<br/>(Zero-Disk Persistence)."]
        NFCE["🧾 pfm-nfce-scraper-service<br/>[Container: Golang 1.24]<br/>Worker concorrente de extração de itens<br/>fiscais nos portais SEFAZ."]
        AI["🧠 pfm-ai-categorizer-service<br/>[Container: Python 3.12 / FastAPI]<br/>Pipeline IA 3 Camadas:<br/>L1 Regex/Exact -> L2 ONNX ML -> L3 LLM."]
    end

    subgraph DataAndMessaging["Persistência Isolada & Backbone de Eventos"]
        PG[("🐘 PostgreSQL 16 (Multi-Schema + RLS)<br/>[Container: Aurora / Cloud SQL / Flexible]<br/>Isolamento Row-Level Security por tenant_id,<br/>NUMERIC(19,4) e Transactional Outbox.")]
        REDIS[("⚡ Redis / Valkey Cluster<br/>[Container: In-Memory Cache]<br/>Chaves de Idempotência (72h),<br/>Cache L1 Categorização e Rate Limit.")]
        KAFKA[["📨 Apache Kafka + Debezium CDC<br/>[Container: Event Streaming]<br/>Tópicos particionados por tenant_id<br/>+ Dead Letter Queues (DLQ)."]]
    end

    WEB -->|"REST HTTP/3 (JSON)"| GW
    MOB -->|"REST HTTP/3 (JSON)"| GW

    GW -->|"gRPC / mTLS"| LEDGER
    GW -->|"gRPC / mTLS"| CARDS
    GW -->|"gRPC / mTLS"| BUDGET
    GW -->|"gRPC / mTLS"| RECON
    GW -->|"gRPC / mTLS (Stream)"| PDF
    GW -->|"gRPC / mTLS"| NFCE

    LEDGER <-->|"gRPC / mTLS"| AI
    PDF -->|"gRPC / mTLS"| AI
    NFCE -->|"gRPC / mTLS"| AI

    LEDGER -->|"ACID + RLS"| PG
    CARDS -->|"ACID + RLS"| PG
    BUDGET -->|"ACID + RLS"| PG
    RECON -->|"ACID + RLS"| PG

    LEDGER <-->|"RESP3"| REDIS
    GW <-->|"RESP3"| REDIS
    AI <-->|"RESP3"| REDIS

    PG -.->|"WAL CDC (Outbox)"| KAFKA
    PDF -->|"Produce Events"| KAFKA
    NFCE -->|"Produce Events"| KAFKA
    KAFKA -->|"Consume Events"| LEDGER
    KAFKA -->|"Consume Events"| CARDS
    KAFKA -->|"Consume Events"| BUDGET
    KAFKA -->|"Consume Events"| RECON
    KAFKA -->|"Consume Events"| NOTIF
```

---

## 3. C4 Nível 3 — Diagrama de Componentes Hexagonais (`pfm-ledger-service`)

O Nível 3 demonstra a estrutura interna padronizada de um microsserviço da plataforma utilizando **Arquitetura Hexagonal (Ports & Adapters)**, exemplificada pelo `pfm-ledger-service`.

```mermaid
flowchart TB
    subgraph InboundAdapters["Adapters Layer — Inbound (Driving Adapters)"]
        GRPC_IN["LedgerGrpcController<br/>[gRPC Inbound Adapter]<br/>Recebe comandos Protobuf v3 do API Gateway."]
        KAFKA_IN["TransactionEventConsumer<br/>[Kafka Inbound Adapter]<br/>Consome eventos de PDF/NFC-e e Conciliação com deduplicação."]
    end

    subgraph ApplicationLayer["Application Layer — Use Cases & Ports"]
        IN_PORT["<<Interface>><br/>RecordTransactionUseCase<br/>[Inbound Port]"]
        UC_IMPL["LedgerApplicationService<br/>[Use Case Orchestrator]<br/>Gerencia transação, idempotência e orquestra portas."]
        OUT_REPO["<<Interface>><br/>LedgerRepositoryPort<br/>[Outbound Port]"]
        OUT_OUTBOX["<<Interface>><br/>OutboxEventPublisherPort<br/>[Outbound Port]"]
        OUT_CAT["<<Interface>><br/>CategoryResolutionPort<br/>[Outbound Port]"]
        OUT_IDEMP["<<Interface>><br/>IdempotencyStorePort<br/>[Outbound Port]"]
    end

    subgraph DomainCore["Domain Core — 100% Pure Java 25 (Zero Framework Dependencies)"]
        AGG["LedgerEntryAggregate<br/>[Domain Aggregate]<br/>Garante invariantes contábeis, Competência vs. Caixa (RN01)."]
        VO_MONEY["MoneyValueObject<br/>[Value Object]<br/>BigDecimal NUMERIC(19,4) + ROUND_HALF_EVEN (RN06)."]
        POL_REFUND["RefundAdjustmentPolicy<br/>[Domain Policy]<br/>Regras de estorno parcial/total e vínculo original (RN03)."]
        TAXONOMY["TwoLevelCategoryValidator<br/>[Domain Specification]<br/>Valida Taxonomia Oficial Nível 1 + Nível 2."]
    end

    subgraph OutboundAdapters["Adapters Layer — Outbound (Driven Adapters)"]
        PG_ADAPTER["PostgresRlsLedgerAdapter<br/>[PostgreSQL Outbound Adapter]<br/>Executa SET LOCAL app.current_tenant_id e persiste lançamento + Outbox."]
        REDIS_ADAPTER["RedisIdempotencyAdapter<br/>[Redis Outbound Adapter]<br/>Lock distribuído e cache de resposta idempotente."]
        AI_ADAPTER["GrpcCategorizerClientAdapter<br/>[gRPC Outbound Adapter]<br/>Cliente com Circuit Breaker e Fallback para o Categorizer IA."]
    end

    GRPC_IN --> IN_PORT
    KAFKA_IN --> IN_PORT
    IN_PORT --> UC_IMPL

    UC_IMPL --> AGG
    AGG --> VO_MONEY
    AGG --> POL_REFUND
    AGG --> TAXONOMY

    UC_IMPL --> OUT_IDEMP
    UC_IMPL --> OUT_CAT
    UC_IMPL --> OUT_REPO
    UC_IMPL --> OUT_OUTBOX

    OUT_IDEMP --> REDIS_ADAPTER
    OUT_CAT --> AI_ADAPTER
    OUT_REPO --> PG_ADAPTER
    OUT_OUTBOX --> PG_ADAPTER
```

---

## 4. Tabela Oficial dos 14 Repositórios da Plataforma

A governança de código da plataforma **PFM Core Banking** é dividida exatamente nos **14 repositórios** abaixo, sob o namespace local `/home/dantas/workspace/pfm-platform/` e organização GitHub [`Sorobanerp`](https://github.com/Sorobanerp):

| # | Repositório | Categoria | Stack / Tecnologia Principal | Responsabilidade Arquitetural & Escopo |
| :-: | :--- | :--- | :--- | :--- |
| **01** | `pfm-contracts` | Contratos & Schemas | OpenAPI 3.1, Protobuf v3, JSON Schema / Avro | Fonte única da verdade (*Single Source of Truth*) para contratos REST, definições gRPC e esquemas de eventos Kafka com verificação de compatibilidade (*Buf / Schema Registry*). |
| **02** | `pfm-api-gateway` | Edge & Segurança | Envoy / Kong, Lua/Go Plugins, OAuth2/OIDC | Terminação TLS 1.3 / HTTP/3 (QUIC), validação de JWT, injeção segura de `X-Tenant-ID`, *Rate Limiting* e transcodificação REST-to-gRPC. |
| **03** | `pfm-ledger-service` | Core Banking | Java 25 LTS, Spring Boot 3.4, PostgreSQL RLS | Escrituração contábil imutável, gestão de Regime de Competência vs. Regime de Caixa (**RN01**), precisão `NUMERIC(19,4)` (**RN06**) e publicação via Transactional Outbox. |
| **04** | `pfm-cards-service` | Core Banking | Java 25 LTS, Spring Boot 3.4, PostgreSQL RLS | Gestão de cartões de crédito, controle de Limite Total vs. Limite Disponível (**RN02**), ciclos de fechamento/vencimento de fatura, desdobramento de parcelas e estornos (**RN03**). |
| **05** | `pfm-budget-service` | Core Banking | Java 25 LTS, Spring Boot 3.4, PostgreSQL RLS | Motor de orçamento mensal por categoria de 2 níveis (**RN02**), acompanhamento de *burn rate* por competência e disparo de eventos de limiar (80% / 100%). |
| **06** | `pfm-reconcile-service` | Core Banking | Java 25 LTS, Spring Boot 3.4, PostgreSQL RLS | Motor de conciliação determinística e nebulosa (*fuzzy matching* de data, valor e CNPJ/Estabelecimento) entre faturas PDF, notas NFC-e e lançamentos manuais (**RN04**). |
| **07** | `pfm-ingestion-pdf-service` | Ingestão High-Perf | Golang 1.24+, PDF Stream Parser, `tmpfs` (RAM) | Recebimento e parsing de faturas de cartão em PDF **100% em memória RAM** (Zero-Disk Persistence - **ADR-006**), extração de linhas transacionais e envio ao pipeline. |
| **08** | `pfm-nfce-scraper-service` | Ingestão High-Perf | Golang 1.24+, Goroutines, HTML/XML Parser | Extração resiliente de cupons fiscais eletrônicos (NFC-e) nos portais da SEFAZ a partir da chave de acesso de 44 dígitos ou URL de QR Code capturado offline. |
| **09** | `pfm-ai-categorizer-service` | Inteligência Artificial | Python 3.12+, FastAPI, ONNX Runtime, LLM SDK | Pipeline de categorização em 3 camadas (L1 Regras Exatas/CNPJ, L2 Modelo ML Local ONNX $<10\text{ms}$, L3 LLM Cloud Anonimizado) mapeado para a Taxonomia de 2 Níveis. |
| **10** | `pfm-notification-service` | Engajamento & Alertas | Java 25 LTS, Spring Boot 3.4, Kafka Consumer | Consumo de eventos de domínio para envio idempotente de notificações Push (FCM/APNs), e-mail transacional e alertas de segurança/orçamento. |
| **11** | `pfm-web-portal` | Frontend Web | Next.js 15, React 19, TypeScript, TailwindCSS | Portal Web executivo com visões comparativas de Competência vs. Caixa, painel de conciliação assistida, upload seguro de PDF e gráficos de orçamento. |
| **12** | `pfm-mobile-android` | Frontend Mobile | Kotlin, Jetpack Compose, Room/SQLCipher, CameraX | Aplicativo nativo **Offline-First** com leitor de QR Code NFC-e instantâneo, fila criptografada local e sincronização resiliente via WorkManager. |
| **13** | `pfm-infra-iac` | Infraestrutura & SRE | Terraform / OpenTofu, Helm, ArgoCD, OTel | Módulos IaC 1:1 multicloud (**AWS / Azure / GCP**), manifestos GitOps Kubernetes, configurações do OpenTelemetry Collector, Prometheus/Grafana e políticas KMS/RLS. |
| **14** | `pfm-docs` | Governança & Docs | MkDocs Material, Mermaid.js, GitHub Actions | Este repositório de **Docs-as-Code** contendo Visão Executiva, ADRs V2, Modelo C4, Fluxos de Sequência, PRD, Backlog BDD e Manual SRE/FinOps. |

---

## 5. Topologia de Portas: Ambiente Local (Host) vs. Cloud (Kubernetes)

Para garantir execução 100% livre de colisões com serviços pré-instalados na máquina do desenvolvedor (notadamente **Portainer** nas portas `8000`, `9000` e `9443`, além de instâncias locais de PostgreSQL `5432`, Redis `6379`, Kafka `9092` ou Envoy `8080`), a plataforma adota o princípio **12-Factor App (Port Binding via Environment Variables)**:

- **No Host Local:** Todos os serviços expostos e ferramentas utilizam a faixa canônica `1xxxx` (aplicações e gateways) e `14xxx`/`15xxx`/`16xxx`/`19xxx` (infraestrutura e bancos).
- **Nos Contêineres & Kubernetes (Cloud):** Os serviços escutam em suas portas canônicas internas padrão (`8080`, `9090`, `3000`, `5432`, `6379`, `9092`, `4566`).

| Componente / Serviço | Host Local | Container / K8s Cloud | Protocolo | Responsabilidade / Roteamento | Variável de Ambiente (Configuração 12-Factor) |
| :--- | :---: | :---: | :---: | :--- | :--- |
| **`pfm-docs`** (MkDocs) | `18000` | `8000` | HTTP | Servidor de documentação viva (preserva Portainer na `8000`) | `PORT=18000` (`Makefile`) |
| **`pfm-web-nextjs`** | `18300` | `3000` | HTTP | Portal Web Executivo (SSR/Next.js) | `PORT=18300`, `NEXT_PUBLIC_API_URL=http://localhost:18080` |
| **`pfm-envoy-gateway`** | `18080` | `8080` | HTTP/2, HTTP/3 | Edge API Gateway / Reverse Proxy | Mapeamento Docker `18080:8080` (Upstream -> `host.docker.internal:18100`) |
| **`pfm-ingestion-bff-go`** | `18100` | `8080` | HTTP | Ingestion BFF & Transações | `SERVER_PORT=18100` |
| **`pfm-forecast-engine-go`** | `18110` | `9090` | gRPC / HTTP | Motor de Projeção & Fluxo de Caixa | `GRPC_PORT=18110` (Health HTTP & gRPC) |
| **`pfm-core-ledger-java` (HTTP)** | `18200` | `8080` | HTTP | Actuator Health, Metrics & REST | `SERVER_PORT=18200` |
| **`pfm-core-ledger-java` (gRPC)** | `18210` | `9090` | gRPC | Core Ledger Engine (Double-entry) | `GRPC_SERVER_PORT=18210` |
| **`pfm-ai-worker-python`** | `18400` | `8080` | HTTP | Worker de Categorização & Healthcheck | `WORKER_PORT=18400` |
| **`postgres-core-ledger`** | `15432` | `5432` | TCP/SQL | Banco de Dados Core Ledger (RLS + Partidas) | `DB_URL=jdbc:postgresql://localhost:15432/pfm_core_ledger` |
| **`postgres-ai-rules`** | `15433` | `5432` | TCP/SQL | Banco de Regras e Taxonomia IA | `PFM_AI_RULES_DSN=postgresql://...:15433/pfm_ai_rules` |
| **`pfm-redis`** (Valkey) | `16379` | `6379` | RESP3 | Cache L1, Idempotência (72h) & Lock | `REDIS_ADDR=localhost:16379` |
| **`pfm-kafka`** (KRaft) | `19092` | `9092` | TCP | Event Streaming Backbone | `KAFKA_BROKERS=localhost:19092` / `KAFKA_BOOTSTRAP_SERVERS` |
| **`pfm-kafka-ui`** | `18085` | `8080` | HTTP | Console Web para inspeção de tópicos Kafka | Mapeamento Docker `18085:8080` |
| **`pfm-localstack`** | `14566` | `4566` | HTTP | Mock AWS S3, KMS & SecretsManager | `AWS_ENDPOINT_URL=http://localhost:14566` |
| **`pfm-mobile-android`** | `18080` | — | HTTP | App Android no emulador -> Envoy Gateway | `BuildConfig.API_BASE_URL="http://10.0.2.2:18080/"` |

---

## 6. Topologias de Implantação Cloud: Piloto 3 Meses vs. Enterprise Scale (ADR-007 / ADR-008)

A plataforma possui uma arquitetura desacoplada de container (100% OCI Distroless Arm64) que suporta duas topologias de implantação em nuvem sem alteração de código-fonte:

```mermaid
flowchart LR
    subgraph Pilot["Topologia A: Piloto 3 Meses (~US$ 11,50 a 24,00/mês)"]
        direction TB
        ALB_P["Single ALB / API GW<br/>Path-Routing"] --> ECS_P["AWS ECS Fargate Spot<br/>(Arm64 Graviton)<br/>0.25 vCPU / 0.5 GB"]
        ECS_P --> RDS_P[("Amazon RDS PostgreSQL<br/>db.t4g.micro (Single-AZ)<br/>Parada Noturna 20h30-06h00")]
        ECS_P --> UP_K["Upstash Kafka Serverless<br/>(Free Tier / Pay-per-msg)"]
        ECS_P --> UP_R["Upstash Redis Serverless<br/>(Free Tier / Pay-per-cmd)"]
        LAMBDA_P["⚡ pfm-finops-manager Lambda<br/>EventBridge 20h30/06h00 BRT"] -.->|Stop/Start| RDS_P
    end

    subgraph Enterprise["Topologia B: Enterprise Scale (>100 Tenants, ~US$ 140 a 350+/mês)"]
        direction TB
        ALB_E["Multi-ALB + AWS WAF<br/>AWS Load Balancer Controller"] --> EKS_E["Amazon EKS Cluster<br/>(Graviton t4g.medium Multi-AZ)<br/>Autoscale KEDA + Karpenter"]
        EKS_E --> AURORA_E[("Amazon Aurora PostgreSQL<br/>Multi-AZ + Read Replicas<br/>KMS DEK por Tenant")]
        EKS_E --> MSK_E["Amazon MSK / Strimzi Kafka<br/>Dedicated 3-Broker Cluster"]
        EKS_E --> VALKEY_E["Amazon ElastiCache Valkey<br/>Multi-AZ Cluster com Failover"]
    end
```

### Matriz Comparativa de Infraestrutura e Custos Mensais

| Dimensão Arquitetural | Topologia A — Piloto Enxuto 3 Meses (ADR-008) | Topologia B — Produção Enterprise (ADR-007) |
| :--- | :--- | :--- |
| **Público-Alvo / Escopo** | Piloto Familiar (5 a 20 usuários / 1 a 3 tenants) | Operação Comercial Multi-Tenant B2C (> 100 tenants) |
| **Orquestrador de Containers** | **AWS ECS Fargate Spot (Arm64)** | **Amazon EKS (Kubernetes 1.30+)** |
| **Custo do Control Plane** | **US$ 0,00 / mês** (Gerenciado AWS ECS) | **US$ 73,00 / mês** (Taxa fixa EKS $0,10/h) |
| **Nós / Computação** | Fargate Spot sob demanda (~US$ 3,50 a US$ 8,00/mês) | Node Group Graviton Spot/On-Demand (~US$ 35,00 a US$ 80,00/mês) |
| **Backbone Mensageria** | **Upstash Kafka Serverless** (~US$ 0,00 a US$ 2,00/mês) | **Amazon MSK ou Strimzi in-cluster** (~US$ 30,00 a US$ 90,00/mês) |
| **Cache & Idempotência** | **Upstash Redis Serverless** (~US$ 0,00 a US$ 1,50/mês) | **Amazon ElastiCache Valkey Multi-AZ** (~US$ 15,00 a US$ 35,00/mês) |
| **Banco Relacional (RLS)** | **RDS PostgreSQL `db.t4g.micro`** com Parada Noturna (~US$ 7,50 a US$ 12,00/mês) | **Amazon Aurora PostgreSQL Multi-AZ** (~US$ 45,00 a US$ 120,00/mês) |
| **Load Balancer & Borda** | Single ALB compartilhado ou HTTP API (~US$ 1,50 a US$ 3,50/mês) | Ingress NGINX + ALB Multi-AZ + AWS WAF (~US$ 25,00 a US$ 50,00/mês) |
| **Governança de Custos** | Lambda `pfm-finops-manager` (Park às 20h30 / Unpark às 06h00 BRT) | Karpenter + KEDA + Savings Plans 1-Year |
| **Custo Total Estimado** | **~US$ 11,50 a US$ 24,00 / mês** | **~US$ 140,00 a US$ 350,00+ / mês** |
| **Impacto no Código da Aplicação** | **Zero**. Mesmas imagens OCI Distroless `linux/arm64`. | **Zero**. Mesmas imagens OCI Distroless `linux/arm64`. |


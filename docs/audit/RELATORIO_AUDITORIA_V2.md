# Relatório de Auditoria Técnica Completa — Arquitetura V2 (14 Repositórios)

**Data da Auditoria:** 16 de Novembro de 2026  
**Escopo:** `/home/dantas/workspace/pfm-platform/`  
**Auditores:** Principal Backend Architect & Staff SRE Auditor  
**Referencial Normativo:** ADRs V2 (ADR-001 a ADR-010), Artefato 01 V2 (PRD & Regras RN01–RN06), Artefato 07 V2 (SRE/FinOps) e Artefato 09 V2 (Backlog BDD).

---

## 1. Tabela Executiva de Status por Repositório (14 Repositórios V2)

| # | Repositório | Papel Arquitetural | Build & Testes | Status Geral | Resumo da Auditoria |
|---|---|---|---|---|---|
| 01 | `pfm-docs` | Documentação Executiva (MkDocs Material + Mermaid + GitHub Pages) | `mkdocs build` OK | **CONFORME** | `mkdocs.yml` completo, diagramas C4/Mermaid, ADRs V2, PRD RN01–RN06, BDD, SRE/FinOps e workflow `.github/workflows/deploy-pages.yml`. |
| 02 | `pfm-contracts` | Contratos Protobuf v3, OpenAPI 3.1 e AsyncAPI/Kafka | `buf generate` OK | **CONFORME** | Contratos `ledger_events.proto`, `core_ledger_service.proto`, `forecast_service.proto`, `buf.yaml`, `buf.gen.yaml` e stubs gerados em `gen/go`, `gen/java` e `gen/python`. |
| 03 | `pfm-shared-infra` | Emulador Cloud Local (`docker-compose.yml`) & Módulos Terraform Base | Sintaxe YAML/HCL OK | **PARCIAL** | Possui LocalStack (`:4566`), `postgres-core-ledger` (`:5432`), `postgres-ai-rules` (`:5433`), Kafka KRaft (`:9092`), Valkey (`:6379`) e Envoy (`:8080`). **Gaps:** (1) `envoy.yaml` aponta para a porta `8090` enquanto o `pfm-ingestion-bff-go` escuta na `8081`; (2) `init-pgvector.sql` não cria a role `pfm_ai_user` nem a tabela `learned_merchant_rules` com RLS no banco `pfm_ai_rules`. |
| 04 | `pfm-core-ledger-java` | Core Banking Ledger (Java 25 LTS, Virtual Threads, ScopedValue, RLS) | `./mvnw test` **10/10 PASS** | **CONFORME** | Domínio 100% puro (`DoubleEntryLedgerService`, `InstallmentSplitter`, `RefundHandler`, `ReceiptReconciliationEngine`), precisão `BigDecimal(19,4)` `HALF_EVEN`, Flyway V1 com PostgreSQL 16 RLS, Outbox Relay em Virtual Threads e Resilience4j (Timeout 3s, CB, Bulkhead). |
| 05 | `pfm-core-ledger-infra` | IaC 1:1 do Core Ledger (OpenTofu AWS/Azure/GCP, Helm, NetworkPolicy, SLOs) | YAML/HCL Validados | **CONFORME** | Políticas IRSA/Workload Identity de menor privilégio, Deployment com ZGC Generational + Virtual Threads, `PodDisruptionBudget`, `NetworkPolicy` Zero-Trust, alertas Prometheus Multi-Window Burn Rate (`< 99,95%`, `p99 > 150ms`, `outbox > 100`) e workflow `infra-validate.yml`. |
| 06 | `pfm-ingestion-bff-go` | Edge BFF & Ingestão PDF em RAM + Scraper SEFAZ NFC-e (Golang) | `go test -v -race ./...` **PASS** | **PARCIAL** | Arquitetura Hexagonal, `shopspring/decimal`, desbloqueio PDF exclusivamente em RAM com wipe via `defer`, Checksum exato, scraper SEFAZ NFC-e com Circuit Breaker e Producer Kafka. **Gaps:** (1) Falta middleware de **Rate Limiting** por `X-Tenant-ID` (ADR-008); (2) Falta cliente gRPC para `pfm-forecast-engine-go` (`:9091`) expondo `POST /api/v1/contracts/simulate` e `GET /api/v1/dashboard` para o frontend Next.js. |
| 07 | `pfm-ingestion-bff-infra` | IaC 1:1 do Ingestion BFF (OpenTofu, Helm, DevSecOps CI/CD) | YAML/HCL Validados | **PARCIAL** | Possui `terraform/aws|azure|gcp`, `helm/Chart.yaml`, `values-local.yaml`, `values-prod.yaml` e `.github/workflows/ci-cd.yml`. **Gap:** Faltam os templates Kubernetes em `helm/templates/` (`deployment.yaml`, `service.yaml`, `hpa.yaml`, `networkpolicy.yaml`). |
| 08 | `pfm-forecast-engine-go` | Motor de Projeção Run-rate (`< 25ms`) & Simulador SAC/Price/Consórcio | `go test -v -bench=. ./...` **PASS** (`1.31ms/op`) | **CONFORME** | `RunRateForecaster` e `ContractAmortizationSimulator` (SAC, Price, Consórcio) com `shopspring/decimal` (`RoundBank`), Consumer Kafka `ledger.entry.committed`, Servidor gRPC e adaptador Redis com Timeout (500ms) + Circuit Breaker. |
| 09 | `pfm-forecast-engine-infra` | IaC 1:1 do Forecast Engine (OpenTofu, Helm, NetworkPolicy, Alertas `< 25ms`) | YAML/HCL Validados | **PARCIAL** | Possui `terraform/aws|azure|gcp`, `helm/Chart.yaml`, `values-local.yaml`, `values-prod.yaml`, `helm/templates/networkpolicy.yaml` e `monitoring/prometheus-alerts.yaml`. **Gaps:** Faltam `helm/templates/deployment.yaml`, `helm/templates/service.yaml` e workflow `.github/workflows/ci-cd.yml`. |
| 10 | `pfm-ai-worker-python` | Worker IA em 3 Camadas (Regras Tenant + Regex Adquirentes/Cidade + Gemini) | `pytest -v` **11/11 PASS** + `ruff` **0 erros** | **PARCIAL** | Arquitetura Hexagonal, remoção de `JIM.COM*`/`MP *`/`BMB*`/`HNA*`/`PG *`/`EC *`/`PAG*`, extração de cidade (`POSTO FREI DAMIAOACUBRA` -> `Acu`), correção `CHURRASCARIA GAUCHA`, Circuit Breaker Gemini (8s) e aprendizado retroativo. **Gap de Integração:** Mapear os códigos da taxonomia do Python (`VAR_FOOD_RESTAURANT`, etc.) para os códigos N1/N2 do seed SQL do Core Ledger Java (`ALIMENTACAO` / `RESTAURANTES_GASTRONOMIA`) ao publicar em `tx.categorized`, além de incluir script SQL de migração para a tabela `learned_merchant_rules`. |
| 11 | `pfm-ai-worker-infra` | IaC 1:1 do AI Worker (OpenTofu, Helm, KEDA Scale-to-Zero, CI/CD) | YAML/HCL Validados | **CONFORME** | OpenTofu AWS/Azure/GCP, manifesto `helm/keda-kafka-scaler.yaml` (`minReplicaCount: 0` escalando por consumer lag de `statement.raw.extracted`) e `.github/workflows/ci-cd.yml` com Ruff, Pytest, Gitleaks e Trivy. |
| 12 | `pfm-web-nextjs` | Portal Executivo Next.js 15 App Router + TypeScript + Tailwind CSS | `npm run lint` & `npm run build` **PASS** | **CONFORME** | Camada HTTP isolada em `src/adapters/api/pfmHttpClient.ts` (`ETag`/`If-None-Match`, `X-Tenant-ID` e fallback demo) e os 4 Módulos Executivos (`/`, `/cards`, `/inbox`, `/contracts`) com build standalone Distroless-ready. |
| 13 | `pfm-web-infra` | IaC 1:1 do Portal Web Next.js (OpenTofu, Helm, CI/CD) | YAML/HCL Validados | **PARCIAL** | Possui `terraform/aws|azure|gcp`, `helm/Chart.yaml`, `values-local.yaml`, `values-prod.yaml` e `.github/workflows/ci-cd.yml`. **Gap:** Faltam os templates Kubernetes em `helm/templates/` (`deployment.yaml`, `service.yaml`, `networkpolicy.yaml`). |
| 14 | `pfm-mobile-android` | App Android Offline-First (Kotlin 2.0, Compose, Room `< 100ms`, WorkManager) | Estrutura & Testes Unitários OK | **CONFORME** | Clean Architecture (`domain`, `data/local/room`, `data/sync`, `ui`), `BigDecimal` escala 4, persistência offline `< 100ms` via `ReceiptDao`, `ReceiptSyncWorker` com `BackoffPolicy.EXPONENTIAL`, telas `QrScannerScreen` e `PendingQueueScreen` e `ReceiptSyncWorkerTest.kt`. |

---

## 2. Análise de Integração Entre Serviços (Portas, Tópicos Kafka, gRPC e Schemas)

### 2.1. Topologia de Portas Locais (`pfm-shared-infra` vs. Microsserviços)

| Componente | Porta Definida no Serviço | Porta Esperada pelos Clientes / Gateway | Status de Alinhamento |
|---|---|---|---|
| **Envoy Edge Gateway** | `8080` (`docker-compose.yml`) | `http://localhost:8080` (`pfm-web-nextjs`) | **ALINHADO** |
| **Upstream Envoy -> `pfm-ingestion-bff-go`** | `8081` (`cmd/server/main.go`) | `8090` (`envoy/envoy.yaml` linha 81) | **DIVERGÊNCIA DETECTADA** (Ajustar `envoy.yaml` para `8081` ou `main.go` para `8090`) |
| **PostgreSQL Core Ledger (`pfm_core_ledger`)** | `5432` (`docker-compose.yml`) | `5432` (`pfm-core-ledger-java/application.yml`) | **ALINHADO** |
| **PostgreSQL AI Rules (`pfm_ai_rules`)** | `5433` (`docker-compose.yml`) | `5433` (`pfm-ai-worker-python`) | **ALINHADO** (Requer DDL inicial da tabela `learned_merchant_rules` com RLS) |
| **Apache Kafka KRaft** | `9092` (`EXTERNAL`) / `29092` (`INTERNAL`) | `localhost:9092` (Go, Python, Java) | **ALINHADO** |
| **Valkey / Redis 8.0** | `6379` (`docker-compose.yml`) | `localhost:6379` (`pfm-forecast-engine-go`) | **ALINHADO** |
| **Core Ledger gRPC Server** | `9090` / `8080` HTTP/2 | `localhost:9090` (`pfm-ingestion-bff-go`) | **ALINHADO** |
| **Forecast Engine gRPC Server** | `9091` (`cmd/server/main.go`) | `localhost:9091` (`pfm-ingestion-bff-go`) | **ALINHADO** |

### 2.2. Contratos de Tópicos Apache Kafka (Particionamento por `tenant_id`)

1. **`statement.raw.extracted`**:
   - **Producer:** `pfm-ingestion-bff-go` (`internal/adapter/out/kafka/statement_producer.go`) — Chave de partição = `tenant_id`.
   - **Consumer:** `pfm-ai-worker-python` (`src/adapter/in/kafka/statement_consumer.py`) — Suporta tanto evento individual quanto lote de faturas.
   - **KEDA Autoscaler:** `pfm-ai-worker-infra/helm/keda-kafka-scaler.yaml` monitora `statement.raw.extracted` no consumer group `pfm-ai-worker-group`.
2. **`tx.categorized`**:
   - **Producer:** `pfm-ai-worker-python` (`src/adapter/out/kafka/categorized_producer.py`) — Chave de partição = `tenant_id`.
   - **Consumer:** `pfm-core-ledger-java` (`CategorizedTransactionKafkaConsumer.java`) — Executa em Virtual Threads vinculando `ScopedValue<UUID>` (`TenantContextHolder.CURRENT_TENANT`).
   - **Ponto de Atenção:** Os códigos N1/N2 emitidos pelo `pfm-ai-worker-python` devem incluir os códigos canônicos da tabela `categories` do `pfm-core-ledger-java` (ex.: `ALIMENTACAO` / `RESTAURANTES_GASTRONOMIA`) para respeitar a constraint `REFERENCES categories(level2_code)`.
3. **`ledger.entry.committed`**:
   - **Producer:** `pfm-core-ledger-java` (`OutboxRelayScheduler.java`) — Publica eventos `PENDING` da tabela `outbox_events` particionados por `tenant_id`.
   - **Consumer:** `pfm-forecast-engine-go` (`internal/adapter/in/kafka/committed_consumer.go`) — Recalcula o Run-rate mensal e atualiza o cache Valkey/Redis em `< 25ms` (`~1.31ms` medido em benchmark).

### 2.3. Diretórios Legados V1 Encontrados no Workspace
Foram identificados 11 diretórios vazios/esqueleto remanescentes da topologia V1 anterior (`pfm-ai-categorizer-service`, `pfm-api-gateway`, `pfm-budget-service`, `pfm-cards-service`, `pfm-infra-iac`, `pfm-ingestion-pdf-service`, `pfm-ledger-service`, `pfm-nfce-scraper-service`, `pfm-notification-service`, `pfm-reconcile-service`, `pfm-web-portal`). Recomenda-se sua remoção para manter exclusivamente os **14 repositórios oficiais da Arquitetura V2**.

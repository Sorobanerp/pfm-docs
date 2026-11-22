# Relatorio de Auditoria Tecnica Completa -- Arquitetura V2 (14 Repositorios)

**Data da Auditoria e Remediacao:** 16 de Novembro de 2026
**Escopo:** `/home/dantas/workspace/pfm-platform/`
**Auditores:** Principal Backend Architect & Staff SRE Auditor
**Referencial Normativo:** ADRs V2 (ADR-001 a ADR-010), Artefato 01 V2 (PRD & Regras RN01--RN06), Artefato 07 V2 (SRE/FinOps) e Artefato 09 V2 (Backlog BDD).

> [!IMPORTANT]
> **Status Consolidado Pos-Remediacao:** **14 de 14 repositorios `CONFORME` (100% de aderencia a Arquitetura V2)**. Todos os gaps tecnicos e de integracao detectados na varredura inicial foram remediados, testados e comitados.

---

## 1. Tabela Executiva de Status por Repositorio (14 Repositorios V2)

| # | Repositorio | Papel Arquitetural | Build & Testes | Status Geral | Resumo da Auditoria & Remediacao Aplicada |
|---|---|---|---|---|---|
| 01 | `pfm-docs` | Documentacao Executiva (MkDocs Material + Mermaid + GitHub Pages) | `mkdocs.yml` OK | **CONFORME** | `mkdocs.yml` completo, diagramas C4/Mermaid, ADRs V2, PRD RN01--RN06, BDD, SRE/FinOps, Relatorio de Auditoria V2 e workflow GitHub Pages. |
| 02 | `pfm-contracts` | Contratos Protobuf v3, OpenAPI 3.1 e AsyncAPI/Kafka | `buf generate` OK | **CONFORME** | Contratos `ledger_events.proto`, `core_ledger_service.proto`, `forecast_service.proto`, `buf.yaml`, `buf.gen.yaml` e stubs gerados em `gen/go`, `gen/java` e `gen/python`. |
| 03 | `pfm-shared-infra` | Emulador Cloud Local (`docker-compose.yml`) & Modulos Terraform Base | Sintaxe YAML/HCL OK | **CONFORME** | **Remediado (`2934f22`):** Porta do cluster `bff_go_cluster` em `envoy.yaml` alinhada para `8081`; DDL RLS da tabela `learned_merchant_rules` + role `pfm_ai_user` adicionados em `init-pgvector.sql`; workflow `infra-validate.yml` criado e diretorios legados V1 removidos. |
| 04 | `pfm-core-ledger-java` | Core Banking Ledger (Java 25 LTS, Virtual Threads, ScopedValue, RLS) | `./mvnw test` **10/10 PASS** | **CONFORME** | Dominio 100% puro (`DoubleEntryLedgerService`, `InstallmentSplitter`, `RefundHandler`, `ReceiptReconciliationEngine`), precisao `BigDecimal(19,4)` `HALF_EVEN`, Flyway V1 com PostgreSQL 16 RLS, Outbox Relay em Virtual Threads e Resilience4j (Timeout 3s, CB, Bulkhead). |
| 05 | `pfm-core-ledger-infra` | IaC 1:1 do Core Ledger (OpenTofu AWS/Azure/GCP, Helm, NetworkPolicy, SLOs) | YAML/HCL Validados | **CONFORME** | Politicas IRSA/Workload Identity de menor privilegio, Deployment com ZGC Generational + Virtual Threads, `PodDisruptionBudget`, `NetworkPolicy` Zero-Trust, alertas Prometheus Multi-Window Burn Rate (`< 99,95%`, `p99 > 150ms`, `outbox > 100`) e workflow `infra-validate.yml`. |
| 06 | `pfm-ingestion-bff-go` | Edge BFF & Ingestao PDF em RAM + Scraper SEFAZ NFC-e (Golang) | `go test -v -race ./...` **PASS** | **CONFORME** | **Remediado (`6800c84`):** Adicionado middleware `TenantRateLimiter` por `X-Tenant-ID` (`HTTP 429` + `Retry-After`) em `rate_limiter.go`, cliente East-West `EastWestGrpcBridgeClient` (`forecast_ledger_client.go`) com `shopspring/decimal` e rotas `GET /api/v1/dashboard` (`ETag`/`304`) e `POST /api/v1/contracts/simulate` testadas. |
| 07 | `pfm-ingestion-bff-infra` | IaC 1:1 do Ingestion BFF (OpenTofu, Helm, DevSecOps CI/CD) | YAML/HCL Validados | **CONFORME** | **Remediado:** Templates Kubernetes completos adicionados em `helm/templates/` (`deployment.yaml`, `service.yaml`, `hpa.yaml`, `networkpolicy.yaml`) + `helm/values.yaml`. |
| 08 | `pfm-forecast-engine-go` | Motor de Projecao Run-rate (`< 25ms`) & Simulador SAC/Price/Consorcio | `go test -v -bench=. ./...` **PASS** (`1.31ms/op`) | **CONFORME** | **Remediado (`bc47946`):** `RunRateForecaster` e `ContractAmortizationSimulator` (SAC, Price, Consorcio) 100% em `shopspring/decimal` (`RoundBank`, zero `float`), Consumer Kafka `ledger.entry.committed`, Servidor gRPC e adaptador Redis com Timeout (500ms) + Circuit Breaker. |
| 09 | `pfm-forecast-engine-infra` | IaC 1:1 do Forecast Engine (OpenTofu, Helm, NetworkPolicy, Alertas `< 25ms`) | YAML/HCL Validados | **CONFORME** | **Remediado:** Adicionados `helm/values.yaml`, `helm/templates/deployment.yaml`, `helm/templates/service.yaml` e workflow `.github/workflows/ci-cd.yml`. |
| 10 | `pfm-ai-worker-python` | Worker IA em 3 Camadas (Regras Tenant + Regex Adquirentes/Cidade + Gemini) | `pytest -v` **11/11 PASS** + `ruff` **0 erros** | **CONFORME** | **Remediado (`612775a`):** Adicionado mapeador canonico `to_core_ledger_taxonomy` em `src/domain/taxonomy.py`, campos `ledger_category_code` e `ledger_subcategory_code` em `CategorizedTransaction` e migracao `migrations/V1__init_ai_rules_rls.sql`. |
| 11 | `pfm-ai-worker-infra` | IaC 1:1 do AI Worker (OpenTofu, Helm, KEDA Scale-to-Zero, CI/CD) | YAML/HCL Validados | **CONFORME** | OpenTofu AWS/Azure/GCP, manifesto `helm/keda-kafka-scaler.yaml` (`minReplicaCount: 0` escalando por consumer lag de `statement.raw.extracted`) e `.github/workflows/ci-cd.yml` com Ruff, Pytest, Gitleaks e Trivy. |
| 12 | `pfm-web-nextjs` | Portal Executivo Next.js 15 App Router + TypeScript + Tailwind CSS | `npm run lint` & `npm run build` **PASS** | **CONFORME** | Camada HTTP isolada em `src/adapters/api/pfmHttpClient.ts` (`ETag`/`If-None-Match`, `X-Tenant-ID` e fallback demo) e os 4 Modulos Executivos (`/`, `/cards`, `/inbox`, `/contracts`) com build standalone Distroless-ready. |
| 13 | `pfm-web-infra` | IaC 1:1 do Portal Web Next.js (OpenTofu, Helm, CI/CD) | YAML/HCL Validados | **CONFORME** | **Remediado:** Adicionados `helm/values.yaml`, `helm/templates/deployment.yaml`, `helm/templates/service.yaml` e `helm/templates/networkpolicy.yaml`. |
| 14 | `pfm-mobile-android` | App Android Offline-First (Kotlin 2.0, Compose, Room `< 100ms`, WorkManager) | Estrutura & Testes Unitarios OK | **CONFORME** | Clean Architecture (`domain`, `data/local/room`, `data/sync`, `ui`), `BigDecimal` escala 4, persistencia offline `< 100ms` via `ReceiptDao`, `ReceiptSyncWorker` com `BackoffPolicy.EXPONENTIAL`, telas `QrScannerScreen` e `PendingQueueScreen` e `ReceiptSyncWorkerTest.kt`. |

---

## 2. Matriz de Integracao Validada (100% Alinhada)

| Integracao | Origem | Destino | Protocolo / Topico / Porta Canonica | Status |
|---|---|---|---|---|
| **North-South Edge Routing** | `pfm-web-nextjs` (`:18300`) / Mobile -> Envoy (`:18080`) | `pfm-ingestion-bff-go` (`:18100`) | HTTP/3 & HTTP/2 (`ETag`, `Brotli`, `X-Tenant-ID`, Rate Limit) | **CONFORME** |
| **Extracao de Faturas PDF (RAM)** | `pfm-ingestion-bff-go` | `pfm-ai-worker-python` | Kafka `statement.raw.extracted` (key = `tenant_id`) | **CONFORME** |
| **Classificacao IA 3 Camadas** | `pfm-ai-worker-python` (`pfm_ai_rules:15433` RLS) | `pfm-core-ledger-java` (`pfm_core_ledger:15432` RLS) | Kafka `tx.categorized` (`ledger_category_code` / `ledger_subcategory_code`) | **CONFORME** |
| **Conciliacao NFC-e Sincrona** | `pfm-ingestion-bff-go` (`SefazNfceScraper`) | `pfm-core-ledger-java` (`:18210`) | gRPC `ProcessReceipt` (`+/-3 dias` + inflacao `>10%` EAN) | **CONFORME** |
| **Transactional Outbox -> Projecao** | `pfm-core-ledger-java` (`OutboxRelayScheduler`) | `pfm-forecast-engine-go` (`Valkey:16379`) | Kafka `ledger.entry.committed` (`< 25ms`, medido `1.31ms`) | **CONFORME** |
| **Simulador SAC / Price / Consorcio** | `pfm-ingestion-bff-go` (`/api/v1/contracts/simulate`) | `pfm-forecast-engine-go` (`:18110`) | gRPC `SimulateContractAmortization` (`shopspring/decimal` Half-Even) | **CONFORME** |

> *Nota de Conformidade 12-Factor:* Todas as portas locais no host utilizam a faixa canonica `1xxxx` (infra em `14xxx`/`15xxx`/`16xxx`/`19xxx`) para isolamento total contra Portainer (`8000`, `9000`, `9443`) e servicos legados do sistema operacional. No cluster K8s, aplicam-se as portas internas padrao (`8080`, `9090`, `5432`, `6379`, `9092`).

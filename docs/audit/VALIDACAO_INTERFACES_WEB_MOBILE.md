# Relatório de Validação Full-Stack de Interfaces Web (Playwright) & Contratos Mobile (Android Offline-First)

**Data/Hora da Homologação:** `2026-11-17T06:18:37-03:00`  
**Scripts de Orquestração:** [`pfm-shared-infra/scripts/up-all-local.sh`](file:///home/dantas/workspace/pfm-platform/pfm-shared-infra/scripts/up-all-local.sh) & [`down-all-local.sh`](file:///home/dantas/workspace/pfm-platform/pfm-shared-infra/scripts/down-all-local.sh)  
**Suíte Web E2E:** [`pfm-web-nextjs/e2e/executive-portal.spec.ts`](file:///home/dantas/workspace/pfm-platform/pfm-web-nextjs/e2e/executive-portal.spec.ts) (`Playwright Headless Chrome`)  
**Resultado Consolidado:** **100% APROVADO (`4/4` Testes Playwright Web + Contrato Mobile HTTP/2-HTTP/3 -> Core Ledger gRPC)**

---

## 1. Orquestração Full-Stack Local (`up-all-local.sh`)

Todos os containers de infraestrutura (`pfm-shared-infra/local-cloud/docker-compose.yml`), os 4 microsserviços backend (com logs estruturados em `/tmp/pfm-logs/`) e o portal `pfm-web-nextjs` subiram em ordem e responderam `HTTP 200 OK` nos health checks:

| Camada | Serviço / Container | Endpoint de Saúde / Porta | Status Obtido | Log Estruturado |
|---|---|---|---|---|
| **Infra Cloud Local** | `pfm-localstack`, `postgres-core-ledger` (`:5432`), `postgres-ai-rules` (`:5433`), `pfm-kafka` (`:9092`), `pfm-redis` (`:6379`) | Containers Docker Healthcheck | `Healthy` | Docker Engine |
| **Edge API Gateway** | `pfm-envoy-gateway` | `http://localhost:8080/healthz` | **`HTTP 200 OK`** | Docker / Envoy |
| **Backend Core Ledger** | `pfm-core-ledger-java` (Java 25 LTS) | `http://localhost:9090/actuator/health` | **`HTTP 200 OK`** | `/tmp/pfm-logs/pfm-core-ledger-java.log` |
| **Backend Forecast Engine** | `pfm-forecast-engine-go` (Golang) | `http://localhost:9091/health` | **`HTTP 200 OK`** | `/tmp/pfm-logs/pfm-forecast-engine-go.log` |
| **Backend AI Worker** | `pfm-ai-worker-python` (Python 3.12) | Consumer `statement.raw.extracted` | **`ACTIVE`** | `/tmp/pfm-logs/pfm-ai-worker-python.log` |
| **Backend Ingestion BFF** | `pfm-ingestion-bff-go` (Golang) | `http://localhost:8081/health` | **`HTTP 200 OK`** | `/tmp/pfm-logs/pfm-ingestion-bff-go.log` |
| **Frontend Executivo** | `pfm-web-nextjs` (Next.js 15 Standalone) | `http://localhost:3000` | **`HTTP 200 OK`** | `/tmp/pfm-logs/pfm-web-nextjs.log` |

---

## 2. Validação E2E da Interface Web (`Playwright Headless` — `4 passed in 2.0s`)

A suíte [`e2e/executive-portal.spec.ts`](file:///home/dantas/workspace/pfm-platform/pfm-web-nextjs/e2e/executive-portal.spec.ts) foi executada em navegador Chromium/Chrome real (`headless: true`) contra `http://localhost:3000` integrado ao API Gateway Envoy (`http://localhost:8080`):

| # | Tela / Rota | Cenário Validado pelo Playwright | Tempo de Execução | Status |
|---|---|---|---|---|
| **01** | **Visão Consolidada (`/`)** | Renderização do Termômetro Run-rate (`Semáforo: RED`), banner **"Regra de Ouro (RN02): Limite disponível de cartão ≠ Orçamento"**, conexão real com o backend via Envoy (`Fonte: LIVE_API` / `ETAG_304_CACHE`) e alternância do filtro entre `Família Consolidada`, `Por Titular: Dantas` e `Por Titular: Cônjuge`. | **`443 ms`** | **PASS** |
| **02** | **Matriz Multi-Cartões (`/cards`)** | Tabela comparativa dos 4 cartões (`Itaú Uniclass Signature •••• 5285`, `•••• 1360`, `Ourocard Visa Platinum`, `Cartão Marisa Mastercard`) e upload real de fatura PDF de teste (`fatura-itau-5285-2026-11.pdf`) enviado para `POST /api/v1/statements/upload`. | **`303 ms`** | **PASS** |
| **03** | **Inbox de Revisão (`/inbox`)** | Exibição do estabelecimento normalizado (`COMERCIO SERTAO LTDA`) e município extraído (`Cidade: Acu / RN`), seleção de categoria e acionamento do botão *"Aplicar para todo o histórico deste estabelecimento"*, gerando regra aprendida na Camada 1 (`pfm_ai_rules`). | **`247 ms`** | **PASS** |
| **04** | **Simulador de Contratos (`/contracts`)** | Simulação interativa de amortização extraordinária alternando entre `Financiamento SAC`, `Financiamento Price` e `Consórcio Veicular`, comparando **Reduzir Prazo** vs. **Reduzir Valor da Parcela** e validando a economia de juros/taxas e ROI. | **`311 ms`** | **PASS** |

---

## 3. Validação de Contratos Mobile (`pfm-mobile-android` Offline-First -> Envoy -> BFF -> Core Ledger gRPC)

1. **Persistência Offline-First (`< 100ms`) & WorkManager (`ReceiptSyncWorkerTest.kt`):**
   - Persistência local via `ReceiptDao` (`PendingReceiptEntity`) validada em modo avião com chave determinística SHA-256 (`tenant_id|qr_code_url|payment_method`) e política de retry exponencial (`NetworkType.CONNECTED` + `BackoffPolicy.EXPONENTIAL`).
2. **Chamada Integrada do Contrato Mobile (`POST http://localhost:8080/api/v1/receipts/nfce`):**
   - Requisição enviada com headers `X-Tenant-ID: aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa` e payload JSON idêntico ao emitido pelo `ReceiptSyncWorker` Android.
   - **Headers de Resposta Recebidos:**
     - `HTTP/1.1 200 OK`
     - `alt-svc: h3=":8443"; ma=86400, h2=":8443"; ma=86400`
     - `etag: "f8be3e8054d29415bf335ef59bda93ed"`
     - `x-envoy-upstream-service-time: 41` (`41 ms` ponta a ponta passando por Envoy -> Go BFF SEFAZ Scraper -> gRPC `ProcessReceipt` no Java 25 Core Ledger -> PostgreSQL 16 RLS).
   - **Payload de Resposta Validado:**
     ```json
     {
       "ledgerResult": {
         "receiptId": "09dc212f-713f-41c1-a01c-df6cf1e49f11",
         "reconciliationStatus": "MATCHED_STATEMENT_LINE",
         "matchedTransactionId": "e37f40e9-17db-4fdd-a807-dde08c583728",
         "journalEntryId": "e37f40e9-17db-4fdd-a807-dde08c583728",
         "matchConfidence": "1.0000",
         "hasInflationAlerts": false,
         "inflationAlerts": []
       },
       "scrapedReceipt": {
         "tenantId": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
         "idempotencyKey": "sha256-mobile-android-nfce-001",
         "accessKey": "24261175315333000109650010000987651000987654",
         "merchantTaxId": "75315333000109",
         "merchantName": "ATACADAO S.A. - LOJA ACU",
         "totalAmount": "313.01",
         "currency": "BRL",
         "paymentMethod": "CREDIT_CARD"
       }
     }
     ```

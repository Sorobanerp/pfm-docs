# Relatorio de Validacao Full-Stack de Interfaces Web (Playwright) & Contratos Mobile (Android Offline-First)

**Data/Hora da Homologacao:** `2026-11-17T06:18:37-03:00`
**Scripts de Orquestracao:** [`pfm-shared-infra/scripts/up-all-local.sh`](file:///home/dantas/workspace/pfm-platform/pfm-shared-infra/scripts/up-all-local.sh) & [`down-all-local.sh`](file:///home/dantas/workspace/pfm-platform/pfm-shared-infra/scripts/down-all-local.sh)
**Suite Web E2E:** [`pfm-web-nextjs/e2e/executive-portal.spec.ts`](file:///home/dantas/workspace/pfm-platform/pfm-web-nextjs/e2e/executive-portal.spec.ts) (`Playwright Headless Chrome`)
**Resultado Consolidado:** **100% APROVADO (`4/4` Testes Playwright Web + Contrato Mobile HTTP/2-HTTP/3 -> Core Ledger gRPC)**

---

## 1. Orquestracao Full-Stack Local (`up-all-local.sh`)

Todos os containers de infraestrutura (`pfm-shared-infra/local-cloud/docker-compose.yml`), os 4 microsservicos backend (com logs estruturados em `/tmp/pfm-logs/`) e o portal `pfm-web-nextjs` subiram em ordem e responderam `HTTP 200 OK` nos health checks:

| Camada | Servico / Container | Endpoint de Saude / Porta Canonica Host | Status Obtido | Log Estruturado |
|---|---|---|---|---|
| **Infra Cloud Local** | `pfm-localstack` (`:14566`), `postgres-core-ledger` (`:15432`), `postgres-ai-rules` (`:15433`), `pfm-kafka` (`:19092`), `pfm-redis` (`:16379`) | Containers Docker Healthcheck | `Healthy` | Docker Engine |
| **Edge API Gateway** | `pfm-envoy-gateway` | `http://localhost:18080/healthz` | **`HTTP 200 OK`** | Docker / Envoy |
| **Backend Core Ledger** | `pfm-core-ledger-java` (Java 25 LTS) | `http://localhost:18200/actuator/health` | **`HTTP 200 OK`** | `/tmp/pfm-logs/pfm-core-ledger-java.log` |
| **Backend Forecast Engine** | `pfm-forecast-engine-go` (Golang) | `http://localhost:18110/health` | **`HTTP 200 OK`** | `/tmp/pfm-logs/pfm-forecast-engine-go.log` |
| **Backend AI Worker** | `pfm-ai-worker-python` (Python 3.12) | `http://localhost:18400/health` | **`HTTP 200 OK`** | `/tmp/pfm-logs/pfm-ai-worker-python.log` |
| **Backend Ingestion BFF** | `pfm-ingestion-bff-go` (Golang) | `http://localhost:18100/health` | **`HTTP 200 OK`** | `/tmp/pfm-logs/pfm-ingestion-bff-go.log` |
| **Frontend Executivo** | `pfm-web-nextjs` (Next.js 15 Standalone) | `http://localhost:18300` | **`HTTP 200 OK`** | `/tmp/pfm-logs/pfm-web-nextjs.log` |

> *Nota de Conformidade 12-Factor:* Todas as portas locais no host utilizam a faixa canonica `1xxxx` (infra em `14xxx`/`15xxx`/`16xxx`/`19xxx`) para isolamento total contra Portainer (`8000`, `9000`, `9443`) e servicos legados do sistema operacional.

---

## 2. Validacao E2E da Interface Web (`Playwright Headless` -- `4 passed in 2.0s`)

A suite [`e2e/executive-portal.spec.ts`](file:///home/dantas/workspace/pfm-platform/pfm-web-nextjs/e2e/executive-portal.spec.ts) foi executada em navegador Chromium/Chrome real (`headless: true`) contra `http://localhost:18300` integrado ao API Gateway Envoy (`http://localhost:18080`):

| # | Tela / Rota | Cenario Validado pelo Playwright | Tempo de Execucao | Status |
|---|---|---|---|---|
| **01** | **Visao Consolidada (`/`)** | Renderizacao do Termometro Run-rate (`Semaforo: RED`), banner **"Regra de Ouro (RN02): Limite disponivel de cartao != Orcamento"**, conexao real com o backend via Envoy (`Fonte: LIVE_API` / `ETAG_304_CACHE`) e alternancia do filtro entre `Familia Consolidada`, `Por Titular: Dantas` e `Por Titular: Conjuge`. | **`443 ms`** | **PASS** |
| **02** | **Matriz Multi-Cartoes (`/cards`)** | Tabela comparativa dos 4 cartoes (`Itau Uniclass Signature ---- 5285`, `---- 1360`, `Ourocard Visa Platinum`, `Cartao Marisa Mastercard`) e upload real de fatura PDF de teste (`fatura-itau-5285-2026-11.pdf`) enviado para `POST /api/v1/statements/upload`. | **`303 ms`** | **PASS** |
| **03** | **Inbox de Revisao (`/inbox`)** | Exibicao do estabelecimento normalizado (`COMERCIO SERTAO LTDA`) e municipio extraido (`Cidade: Acu / RN`), selecao de categoria e acionamento do botao *"Aplicar para todo o historico deste estabelecimento"*, gerando regra aprendida na Camada 1 (`pfm_ai_rules`). | **`247 ms`** | **PASS** |
| **04** | **Simulador de Contratos (`/contracts`)** | Simulacao interativa de amortizacao extraordinaria alternando entre `Financiamento SAC`, `Financiamento Price` e `Consorcio Veicular`, comparando **Reduzir Prazo** vs. **Reduzir Valor da Parcela** e validando a economia de juros/taxas e ROI. | **`311 ms`** | **PASS** |

---

## 3. Validacao de Contratos Mobile (`pfm-mobile-android` Offline-First -> Envoy -> BFF -> Core Ledger gRPC)

1. **Persistencia Offline-First (`< 100ms`) & WorkManager (`ReceiptSyncWorkerTest.kt`):**
   - Persistencia local via `ReceiptDao` (`PendingReceiptEntity`) validada em modo aviao com chave deterministica SHA-256 (`tenant_id|qr_code_url|payment_method`) e politica de retry exponencial (`NetworkType.CONNECTED` + `BackoffPolicy.EXPONENTIAL`).
2. **Chamada Integrada do Contrato Mobile (`POST http://localhost:18080/api/v1/receipts/nfce` / emulador `http://10.0.2.2:18080`):**
   - Requisicao enviada com headers `X-Tenant-ID: aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa` e payload JSON identico ao emitido pelo `ReceiptSyncWorker` Android.
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

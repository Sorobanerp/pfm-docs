# Guia Completo de Execucao, Debug em IDEs & Testes Locais (DX)

Este guia documenta o fluxo oficial de onboarding, inicializacao de infraestrutura local, debug interativo em IDEs (**IntelliJ IDEA** para Java 25 e **VS Code** para Go e Python) e validacao ponta a ponta (Swagger UI OpenAPI 3.1, gRPC Server Reflection, Kafka Console e PostgreSQL 16 Row-Level Security) da plataforma **PFM Core Banking V3.0**.

---

## 1. Inicializacao em Comando Unico (`init-local-development.sh`)

Na raiz do workspace (`/home/dantas/workspace/pfm-platform/`), execute o script idempotente de bootstrap local:

```bash
chmod +x ./init-local-development.sh
./init-local-development.sh
```

O script executa automaticamente 5 etapas sem gravar nenhum segredo real nos repositorios Git:

1. **Validacao de Pre-requisitos:** Docker Compose, OpenJDK 25 LTS, Go 1.27+, Python 3.12+ e `grpcurl`.
2. **Geracao de `.env.local` (Ignorados pelo `.gitignore`):** Cria `.env.local` em cada projeto (`pfm-shared-infra`, `pfm-core-ledger-java`, `pfm-ingestion-bff-go`, `pfm-forecast-engine-go`, `pfm-ai-worker-python`, `pfm-web-nextjs`) mantendo versionado apenas o `.env.example`.
3. **Orquestracao Docker (`pfm-shared-infra/docker-compose.local.yml`):**
   - **PostgreSQL 16 + `pgvector` + RLS:** `localhost:5432` (e `:15432`)
   - **Kafka / Redpanda Event Backbone:** `localhost:9092` (e `:19092`)
   - **Kafka / Redpanda Console Web UI:** `http://localhost:8081` (e `:18085`)
   - **Valkey / Redis 8.0:** `localhost:6379` (e `:16379`)
   - **LocalStack (AWS S3 + KMS + Secrets Manager):** `http://localhost:4566` (e `:14566`)
4. **Criacao Automatica de Topicos Kafka:** `statement.raw.extracted`, `tx.categorized`, `ledger.entry.committed`, `tx.dlq`.
5. **Provisionamento Criptografico LocalStack:** Cria a chave KMS simetrica `alias/pfm-master-key` (e `alias/pfm-tenant-master-key`) e o bucket S3 `s3://pfm-statements-encrypted-local` com SSE-KMS.

---

## 2. Mapa de Portas & Perfis Locais (`local`)

| Servico / Componente | Perfil Local | Porta Principal | Endpoints Locais |
| :--- | :--- | :---: | :--- |
| **PostgreSQL 16 (Core Ledger RLS)** | Docker | `5432` | `jdbc:postgresql://localhost:5432/pfm_core_ledger` |
| **Kafka / Redpanda Broker** | Docker | `9092` | `localhost:9092` |
| **Kafka / Redpanda Console UI** | Docker | `8081` | `http://localhost:8081` |
| **Valkey / Redis** | Docker | `6379` | `localhost:6379` |
| **LocalStack (S3 + KMS)** | Docker | `4566` | `http://localhost:4566` |
| **`pfm-core-ledger-java`** | `SPRING_PROFILES_ACTIVE=local` | `9090` (gRPC) / `8082` (HTTP) | `localhost:9090` (gRPC Reflection) / `http://localhost:8082/actuator/health` |
| **`pfm-forecast-engine-go`** | `APP_ENV=local` | `9091` (gRPC + HTTP/2 h2c) | `localhost:9091` (gRPC Reflection) / `http://localhost:9091/health` |
| **`pfm-ingestion-bff-go`** | `APP_ENV=local` | `8080` (HTTP REST + Swagger) | `http://localhost:8080/swagger/index.html` |
| **`pfm-ai-worker-python`** | `APP_ENV=local` | `18400` (Health) | `http://localhost:18400/health` |

---

## 3. Passo a Passo de Execucao e Debug nas IDEs

### 3.1. IntelliJ IDEA JetBrains -- `pfm-core-ledger-java` (Java 25 LTS)

O repositorio `pfm-core-ledger-java` ja inclui a configuracao compartilhada em `.run/CoreLedgerApplication (local).run.xml`:

1. Abra a pasta `/home/dantas/workspace/pfm-platform/pfm-core-ledger-java` no **IntelliJ IDEA**.
2. Em **File -> Project Structure -> Project SDK**, selecione **Java 25 LTS**.
3. No seletor de execucao (canto superior direito), a configuracao **`CoreLedgerApplication (local)`** aparecera automaticamente com:
   - `SPRING_PROFILES_ACTIVE=local` (`src/main/resources/application-local.yml`)
   - `SERVER_PORT=8082` (Actuator e Bridge HTTP)
   - `GRPC_SERVER_PORT=9090` com `grpc.server.reflection-service-enabled=true`
   - VM Options: `-XX:+UseZGC --enable-preview`
4. Clique em **Run** (`Shift+F10`) ou **Debug** (`Shift+F9`). O Flyway aplicara automaticamente as migrations `V1`, `V2` e `V3` (com politicas PostgreSQL 16 RLS) no banco local `:5432`.
5. **Via CLI (alternativa):**
   ```bash
   cd /home/dantas/workspace/pfm-platform/pfm-core-ledger-java
   SPRING_PROFILES_ACTIVE=local ./mvnw spring-boot:run
   ```

### 3.2. Visual Studio Code -- `pfm-ingestion-bff-go` & `pfm-forecast-engine-go` (Go)

Ambos os repositorios Go incluem `.vscode/launch.json`, `.vscode/settings.json`, `.vscode/extensions.json` e `requests-local.http`:

1. Abra `/home/dantas/workspace/pfm-platform/pfm-forecast-engine-go` ou `/home/dantas/workspace/pfm-platform/pfm-ingestion-bff-go` no **VS Code**.
2. Instale as extensoes recomendadas quando solicitado: **Go (`golang.go`)** e **REST Client (`humao.rest-client`)**.
3. Pressione **`F5`** (Run and Debug):
   - No `pfm-forecast-engine-go`: seleciona **`Run PFM Forecast Engine (APP_ENV=local :9091 gRPC)`**, carregando `.env.local` e habilitando `reflection.Register(grpcServer)`.
   - No `pfm-ingestion-bff-go`: seleciona **`Run PFM Ingestion BFF (APP_ENV=local :8080)`**, carregando `.env.local` e expondo o **Swagger UI** em `http://localhost:8080/swagger/index.html`.
4. Abra o arquivo `requests-local.http` na raiz do projeto e clique em **`Send Request`** acima de qualquer bloco para disparar chamadas HTTP/REST direto do editor.

### 3.3. Visual Studio Code -- `pfm-ai-worker-python` (Python 3.12)

1. Abra `/home/dantas/workspace/pfm-platform/pfm-ai-worker-python` no **VS Code**.
2. O interpretador `.venv/bin/python` ja esta pre-configurado em `.vscode/settings.json`.
3. Pressione **`F5`** para iniciar **`Run PFM AI Worker Python (APP_ENV=local)`**:
   - Consome `statement.raw.extracted` em `localhost:9092`;
   - Quando `GEMINI_API_KEY` esta vazia no `.env.local`, opera automaticamente em **modo deterministico local** sem falhar e publica em `tx.categorized`.

---

## 4. Swagger UI (OpenAPI 3.1) & Console Kafka

- **Swagger UI Interativo (`APP_ENV=local`):**
  Acesse `http://localhost:8080/swagger/index.html`.
  - A especificacao OpenAPI 3.1 (`pfm-contracts/openapi/openapi.yaml`) e servida em `http://localhost:8080/swagger/openapi.yaml`.
  - O Swagger UI injeta automaticamente o header de desenvolvimento `X-Tenant-ID: 11111111-1111-1111-1111-111111111111` (voce pode altera-lo no botao **Authorize** para `22222222-2222-2222-2222-222222222222` para testar isolamento multi-tenant RLS).
- **Kafka / Redpanda Web Console:**
  Acesse `http://localhost:8081` para inspecionar em tempo real as mensagens e particoes dos topicos `statement.raw.extracted`, `tx.categorized`, `ledger.entry.committed` e `tx.dlq`.

---

## 5. Colecao de Testes Locais (`curl` HTTP REST & `grpcurl` gRPC)

### 5.1. Validar Swagger UI & Healthchecks

```bash
curl -I http://localhost:8080/swagger/index.html
curl -s http://localhost:8080/health | jq .
curl -s http://localhost:8082/actuator/health | jq .
curl -s http://localhost:9091/health | jq .
```

### 5.2. Inspecionar e Invocar Servicos gRPC via `grpcurl` (Server Reflection)

```bash
# 1. Listar servicos gRPC no Core Ledger Java (:9090)
grpcurl -plaintext localhost:9090 list
grpcurl -plaintext localhost:9090 describe pfm.v1.CoreLedgerService

# 2. Listar servicos gRPC no Forecast Engine Go (:9091)
grpcurl -plaintext localhost:9091 list

# 3. Simular amortizacao SAC direto via gRPC no Forecast Engine (:9091)
grpcurl -plaintext -d '{
  "tenant_id": "11111111-1111-1111-1111-111111111111",
  "contract_id": "33333333-3333-3333-3333-333333333333",
  "amortization_system": "AMORTIZATION_SYSTEM_SAC",
  "prepayment_strategy": "PREPAYMENT_STRATEGY_REDUCE_TERM",
  "outstanding_balance": "240000.00",
  "remaining_installments": 120,
  "monthly_interest_rate": "0.0085",
  "monthly_insurance_and_fees": "65.00",
  "extra_amortization_amount": "20000.00"
}' localhost:9091 pfm.v1.ForecastService/SimulateContractAmortization
```

### 5.3. Fluxo de Transacoes, Dashboard & Comprovacao de Isolamento RLS

```bash
# 1. Criar lancamento no Tenant Alpha (11111111-1111-1111-1111-111111111111)
curl -s -X POST http://localhost:8080/api/v1/transactions \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 11111111-1111-1111-1111-111111111111" \
  -d '{
    "description": "SUPERMERCADO PAO DE ACUCAR",
    "amount": "450.75",
    "currency": "BRL",
    "category_code": "VAR_SUPERMARKET",
    "payment_method": "CREDIT_CARD",
    "competence_month": "2026-11"
  }' | jq .

# 2. Consultar Dashboard Summary do Tenant Alpha
curl -s "http://localhost:8080/api/v1/dashboard/summary?scope=FAMILY" \
  -H "X-Tenant-ID: 11111111-1111-1111-1111-111111111111" | jq .

# 3. Comprovar isolamento RLS consultando com Tenant Beta (22222222-2222-2222-2222-222222222222 -> count: 0)
curl -s http://localhost:8080/api/v1/transactions \
  -H "X-Tenant-ID: 22222222-2222-2222-2222-222222222222" | jq .

# 4. Comprovar RLS diretamente no PostgreSQL 16 (pfm_app_user NOBYPASSRLS)
docker exec -i postgres-core-ledger psql -U pfm_app_user -d pfm_core_ledger -c \
  "SELECT COUNT(*) AS rows_without_tenant_context FROM ledger_entries;"
```

### 5.4. Upload de Fatura PDF & Validacao de Checksum

```bash
# Upload de fatura com soma de itens igual ao total (200 OK)
curl -s -X POST http://localhost:8080/api/v1/statements/upload \
  -H "X-Tenant-ID: 11111111-1111-1111-1111-111111111111" \
  -H "X-Statement-Issuer: ITAU" \
  -H "X-Card-Last4: 4422" \
  -H "X-File-Name: fatura-itau-2026-11.pdf" \
  --data-binary $'ITAU PERSONNALITE\nTOTAL DA FATURA: 550.00\n10/11 SUPERMERCADO PAO DE ACUCAR 350.00\n12/11 DROGASIL FARMACIA 200.00\n' | jq .
```

---

## 6. Checklist de Troubleshooting para Novos Engenheiros

- **`401 Unauthorized: missing or invalid X-Tenant-ID UUID header`**:
  Verifique se o header `X-Tenant-ID` contem um UUID v4 valido (ex: `11111111-1111-1111-1111-111111111111`).
- **`Connection refused` em `localhost:5432`, `localhost:9092`, `localhost:6379` ou `localhost:4566`**:
  Execute `./init-local-development.sh` na raiz do workspace para garantir que todos os conteineres de `pfm-shared-infra/docker-compose.local.yml` estejam `healthy`.
- **`grpcurl` retorna `Server does not support the reflection API`**:
  Certifique-se de que o `pfm-core-ledger-java` foi iniciado com `SPRING_PROFILES_ACTIVE=local` (porta `9090`) e o `pfm-forecast-engine-go` com `APP_ENV=local` (porta `9091`).
- **PostgreSQL retorna `0 rows` ao consultar tabelas manualmente via `psql`**:
  Comportamento esperado do **Zero-Trust RLS (ADR-006)** quando conectado como `pfm_app_user` sem definir `SET LOCAL app.current_tenant_id = '<uuid>';` dentro de um bloco `BEGIN; ... COMMIT;`.

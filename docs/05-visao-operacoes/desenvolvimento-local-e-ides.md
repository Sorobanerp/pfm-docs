# 5.1. Guia Completo de Execucao Local, Debug em IDEs, Swagger UI e gRPC

<span class="badge-green">Developer Experience (DX)</span>
<span class="badge-glow">APP_ENV=local &amp; SPRING_PROFILES_ACTIVE=local</span>
<span class="badge-peach">Exemplos de Teste em BRL (R$)</span>

Este documento orienta o onboarding de engenheiros, a inicializacao local em comando unico (`./init-local-development.sh`), o debug interativo no **IntelliJ IDEA** (Java 25 LTS) e **VS Code** (Go e Python) e a colecao de testes locais via **Swagger UI (OpenAPI 3.1)**, `curl`, `grpcurl` e **PostgreSQL 16 RLS**.

---

## 1. Inicializacao em Comando Unico (`init-local-development.sh`)

Na raiz do workspace (`/home/dantas/workspace/pfm-platform/`), execute:

```bash
chmod +x ./init-local-development.sh
./init-local-development.sh
```

O script executa automaticamente 5 etapas sem gravar nenhum segredo real nos repositorios Git:

1. **Validacao de Pre-requisitos:** Docker Compose, OpenJDK 25 LTS, Go 1.27+, Python 3.12+ e `grpcurl`.
2. **Geracao de `.env.local` (Ignorados pelo `.gitignore`):** Cria `.env.local` em cada projeto mantendo versionado apenas o `.env.example` com placeholders seguros.
3. **Orquestracao Docker (`pfm-shared-infra/docker-compose.local.yml`):**
   - **PostgreSQL 16 + `pgvector` + RLS:** `localhost:5432`
   - **Kafka / Redpanda Event Backbone:** `localhost:9092`
   - **Kafka / Redpanda Console Web UI:** `http://localhost:8081`
   - **Valkey / Redis 8.0:** `localhost:6379`
   - **LocalStack (AWS S3 + KMS + Secrets Manager):** `http://localhost:4566`
4. **Criacao Automatica de Topicos Kafka:** `statement.raw.extracted`, `tx.categorized`, `ledger.entry.committed`, `tx.dlq`.
5. **Provisionamento LocalStack:** Chave KMS `alias/pfm-master-key` e bucket `s3://pfm-statements-encrypted-local`.

---

## 2. Mapa de Portas e Perfis Locais (`local`)

| Servico / Componente | Perfil Local | Porta Local | Endpoint de Verificacao |
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

1. Abra `/home/dantas/workspace/pfm-platform/pfm-core-ledger-java` no **IntelliJ IDEA**.
2. Em **File -> Project Structure -> Project SDK**, confirme **Java 25 LTS**.
3. Selecione a configuracao compartilhada **`CoreLedgerApplication (local)`** (`.run/CoreLedgerApplication (local).run.xml`) que carrega `SPRING_PROFILES_ACTIVE=local` (`application-local.yml`), Flyway ativo (`V1`, `V2`, `V3` + RLS), Actuator `:8082` e gRPC Server Reflection `:9090`.
4. Clique em **Run** (`Shift+F10`) ou **Debug** (`Shift+F9`).

### 3.2. Visual Studio Code -- `pfm-ingestion-bff-go` e `pfm-forecast-engine-go` (Go)

1. Abra `pfm-ingestion-bff-go` ou `pfm-forecast-engine-go` no **VS Code**.
2. Pressione **`F5`** (`.vscode/launch.json` com `APP_ENV=local` e `envFile: "${workspaceFolder}/.env.local"`).
3. Utilize o arquivo `requests-local.http` com a extensao **REST Client (`humao.rest-client`)** ou acesse o **Swagger UI** em `http://localhost:8080/swagger/index.html`.

### 3.3. Visual Studio Code -- `pfm-ai-worker-python` (Python 3.12)

1. Abra `pfm-ai-worker-python` no **VS Code** (interpretador `.venv/bin/python` pre-configurado em `.vscode/settings.json`).
2. Pressione **`F5`** para iniciar **`Run PFM AI Worker Python (APP_ENV=local)`** (opera em modo deterministico local quando `GEMINI_API_KEY` estiver vazia).

---

## 4. Colecao de Comandos `curl` (HTTP REST) e `grpcurl` (gRPC) em BRL (`R$`)

```bash
# 1. Validar Swagger UI (HTTP/1.1 200 OK)
curl -I http://localhost:8080/swagger/index.html

# 2. Listar servicos gRPC via Server Reflection (:9090 e :9091)
grpcurl -plaintext localhost:9090 list
grpcurl -plaintext localhost:9091 list

# 3. Registrar transacao de R$ 450,75 no Tenant Alpha
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

# 4. Consultar resumo executivo do Tenant Alpha
curl -s "http://localhost:8080/api/v1/dashboard/summary?scope=FAMILY" \
  -H "X-Tenant-ID: 11111111-1111-1111-1111-111111111111" | jq .

# 5. Comprovar isolamento RLS consultando como Tenant Beta (retorna count: 0)
curl -s http://localhost:8080/api/v1/transactions \
  -H "X-Tenant-ID: 22222222-2222-2222-2222-222222222222" | jq .

# 6. Comprovar Fail-Closed RLS diretamente no PostgreSQL 16 (pfm_app_user)
docker exec -i postgres-core-ledger psql -U pfm_app_user -d pfm_core_ledger -c \
  "SELECT COUNT(*) AS visible_rows_without_tenant_context FROM ledger_entries;"
```

---

## 5. Suite Oficial de Homologacao Local E2E (`validation-suite/`)

Para validar **100% das 8 Jornadas do Produto (Happy Path + Sad Path)** contra os 4 servicos locais antes de qualquer deploy em nuvem, o repositorio `pfm-ingestion-bff-go` disponibiliza a pasta `validation-suite/`:

- **`pfm-ingestion-bff-go/validation-suite/journey-complete.http`**: Colecao interativa REST Client (VS Code / IntelliJ HTTP Client / Insomnia / Postman) com variaveis encadeadas (`@baseUrl`, `@tenantA`, `@tenantB`, `@ownerA`, `@viewerA`, `@platformAdmin`).
- **`pfm-ingestion-bff-go/validation-suite/run-local-e2e-validation.sh`**: Suite automatizada executavel (`chmod +x`) que valida 43 assercoes HTTP REST, gRPC (`:9090` e `:9091`) e PostgreSQL 16 RLS (`:5432`) em menos de 3 segundos.

### 5.1. Como Executar a Homologacao Local E2E

```bash
cd /home/dantas/workspace/pfm-platform/pfm-ingestion-bff-go
./validation-suite/run-local-e2e-validation.sh
```

### 5.2. Matriz das 8 Jornadas Homologadas (Happy Path + Sad Path)

| Jornada | Escopo Funcional (100% BRL `R$`) | Cenarios Happy Path | Cenarios Sad Path (Seguranca & Dominio) |
| :--- | :--- | :--- | :--- |
| **Jornada 1** | Autenticacao JWT Local, Onboarding de Tenant e Isolamento RLS | Emissao de JWT para `OWNER` (Tenants A e B), `VIEWER` e `PLATFORM_ADMIN` (`200 OK`) | Sem `X-Tenant-ID`/JWT (`401`), UUID malformado (`401`), Cross-Tenant Read (`404` / `0 rows` no PostgreSQL 16 RLS) |
| **Jornada 2** | Gestao de Cartoes de Credito e Lancamentos (CRUD + `RN02` / `RN03`) | Cartao final `5285` (`R$ 15.000,00`), compra a vista (`R$ 245,90`), parcelado `10x` (`R$ 4.500,00` `01/10..10/10`), `PATCH` categoria e estorno `RN03` (`201 Created`) | Valor negativo `-10.00` (`400`), valor zero `0.00` (`400`), data invalida (`400`), parcelas `0` (`400`), `VIEWER` tentando deletar (`403 Forbidden`) |
| **Jornada 3** | Ingestao de Fatura PDF em RAM (Zero-Persistence) e Checksum (`RN04`) | Upload PDF em RAM com soma exata `R$ 750,90` e `checksum_diff: 0.00` (`200 OK`) | Divergencia de soma `R$ 700,00 != R$ 750,90` (`409 Conflict`), arquivo `.exe` / `MZ` (`415 Unsupported Media Type`), PDF vazio (`400 Bad Request`) |
| **Jornada 4** | Ingestao de Cupom Fiscal SEFAZ (NFC-e) e Inflacao Pessoal por SKU | Ingestao de 2 notas fiscais com SKU `EAN 7891234567890` (`R$ 39,90` -> `R$ 47,90`) detectando `+20.05%` de inflacao pessoal (`200 OK`) | Reenvio da mesma chave de acesso NFC-e de 44 digitos (`409 Conflict` idempotente) |
| **Jornada 5** | Pipeline Kafka, Categorizacao IA (3 Camadas) e Inbox Zero (`< 5%`) | Consulta da fila Inbox Zero (`2.40% < 5.00%`) e confirmacao com `learn_rule: true` (`200 OK`) | Evento malformado roteado para `tx.dlq` (`202 Accepted`) mantendo `pfm-ai-worker-python` `UP` |
| **Jornada 6** | Motor de Previsibilidade ("Livre para Gastar") e Simulador SAC/PRICE | "Livre para Gastar" (`TODAY`/`WEEK`/`MONTH`) e amortizacao SAC (`R$ 320.000,00`, extra `R$ 50.000,00`) via HTTP e gRPC `:9091` (`200 OK` / `gRPC OK`) | Amortizacao extra `R$ 400.000,00 > R$ 320.000,00` (`400 Bad Request` / `InvalidArgument`) e prazo `0` (`400 Bad Request`) |
| **Jornada 7** | Governanca Familiar, Teto de Gastos e Portabilidade LGPD | Teto mensal `R$ 1.500,00` (alerta `80%`), convite `MEMBER` (`201 Created`), exportacao LGPD (`202 Accepted`) e gRPC Core Ledger `:9090` (`gRPC OK`) | Bloqueio de mutacao para perfil `VIEWER` (`403 Forbidden`) |
| **Jornada 8** | SaaS Admin Backoffice e Zero-Trust Privacy (Blindagem LGPD) | `PLATFORM_ADMIN` lista metadados comerciais de tenants (`200 OK`) | `PLATFORM_ADMIN` bloqueado ao tentar ler transacoes financeiras (`403 Forbidden`) ou perfil familiar privado (`403 Forbidden`) |


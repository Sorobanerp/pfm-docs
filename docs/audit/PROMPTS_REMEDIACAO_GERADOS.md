# Prompts Mestres Autonomos de Remediacao -- Arquitetura V2

Este documento contem os **Prompts Mestres Autonomos prontos para execucao** gerados pela Auditoria Tecnica V2 para elevar todos os repositorios com status **`PARCIAL`** (`pfm-shared-infra`, `pfm-ingestion-bff-go`, `pfm-ai-worker-python`, `pfm-ingestion-bff-infra`, `pfm-forecast-engine-infra` e `pfm-web-infra`) ao status **`100% CONFORME`**, alem de limpar diretorios legados V1.

---

## Prompt de Remediacao 01 -- `pfm-shared-infra` (Alinhamento Envoy `:8081` & DDL RLS `pfm_ai_rules`)

```text
MODO DE EXECUCAO AUTONOMA: Execute todas as edicoes de arquivos, validacoes e commits Git locais de forma 100% autonoma ate concluir. So peca autorizacao caso precise executar comandos em APIs externas, GitHub remoto, AWS ou servicos de terceiros.

Atue como Staff Cloud Architect & Database Reliability Engineer no repositorio `/home/dantas/workspace/pfm-platform/pfm-shared-infra`:

1. Alinhe a porta do cluster `bff_go_cluster` em `local-cloud/envoy/envoy.yaml` de `8090` para `8081` (porta oficial do `pfm-ingestion-bff-go`).
2. Atualize `local-cloud/init-db/init-pgvector.sql` para criar de forma idempotente:
   - A role restrita `pfm_ai_user` (`WITH LOGIN PASSWORD 'pfm_ai_pass' NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS`).
   - A funcao `current_app_tenant_id()` lendo `current_setting('app.current_tenant_id', true)`.
   - A tabela `learned_merchant_rules` (`tenant_id VARCHAR(64)`, `merchant_pattern VARCHAR(255)`, `category_code VARCHAR(64)`, `category_group VARCHAR(64)`, `confidence NUMERIC(19,4)`, `updated_at TIMESTAMPTZ`, `PRIMARY KEY (tenant_id, merchant_pattern)`) com Row-Level Security (`ENABLE ROW LEVEL SECURITY` e `FORCE ROW LEVEL SECURITY`) isolada por `tenant_id = current_setting('app.current_tenant_id', true)`.
3. Crie `.github/workflows/infra-validate.yml` validando a sintaxe do `docker-compose.yml`, `envoy.yaml` e modulos OpenTofu (`terraform/`).
4. Remova do diretorio `/home/dantas/workspace/pfm-platform/` as pastas vazias/legadas da V1 (`pfm-ai-categorizer-service`, `pfm-api-gateway`, `pfm-budget-service`, `pfm-cards-service`, `pfm-infra-iac`, `pfm-ingestion-pdf-service`, `pfm-ledger-service`, `pfm-nfce-scraper-service`, `pfm-notification-service`, `pfm-reconcile-service`, `pfm-web-portal`), preservando intocados os 14 repositorios oficiais da V2.
5. Faca `git add . && git commit -m "fix(shared-infra): align Envoy BFF port to 8081 and add RLS schema for learned_merchant_rules"` em `pfm-shared-infra`.
```

---

## Prompt de Remediacao 02 -- `pfm-ingestion-bff-go` (Rate Limiting por Tenant & Proxy gRPC para Forecast/Core Ledger)

```text
MODO DE EXECUCAO AUTONOMA: Execute todas as edicoes de arquivos, testes Go e commits Git locais de forma 100% autonoma ate concluir e validar tudo. So peca autorizacao caso precise executar comandos em APIs externas, GitHub remoto, AWS ou servicos de terceiros.

Atue como Staff Engineer Golang no repositorio `/home/dantas/workspace/pfm-platform/pfm-ingestion-bff-go`:

1. Adicione em `internal/adapter/in/http/rate_limiter.go` um middleware Token Bucket / Sliding Window por `X-Tenant-ID` (ADR-008: limite configuravel, retornando `HTTP 429 Too Many Requests` com header `Retry-After` quando excedido).
2. Adicione em `internal/adapter/out/grpc/forecast_ledger_client.go` o cliente gRPC/HTTP2 para consultar `GetTenantFinancialSummary` no `pfm-core-ledger-java` (host `localhost:18210` / container `localhost:9090`) e `SimulateContractAmortization` no `pfm-forecast-engine-go` (host `localhost:18110` / container `localhost:9090`), protegido por Timeout (3s) e Circuit Breaker.
3. Exponha em `internal/adapter/in/http/server.go` as rotas consumidas pelo frontend `pfm-web-nextjs`:
   - `GET /api/v1/dashboard` (com suporte a `ETag` / `If-None-Match` -> `304 Not Modified`)
   - `POST /api/v1/contracts/simulate`
4. Adicione testes unitarios em `internal/adapter/in/http/server_test.go` validando o Rate Limiter (`HTTP 429`) e as rotas `/api/v1/dashboard` e `/api/v1/contracts/simulate`.
5. Execute `go test -v -race ./...` ate passar 100% e faca `git add . && git commit -m "feat(bff): add per-tenant rate limiter and gRPC proxy routes for dashboard and contract simulation"`.
```

---

## Prompt de Remediacao 03 -- `pfm-ai-worker-python` (Mapeamento Canonico de Taxonomia Core Ledger & Migracao SQL)

```text
MODO DE EXECUCAO AUTONOMA: Execute todas as edicoes de arquivos, testes Pytest/Ruff e commits Git locais de forma 100% autonoma ate concluir e validar tudo. So peca autorizacao caso precise executar comandos em APIs externas, GitHub remoto, AWS ou servicos de terceiros.

Atue como Staff Data & AI Engineer no repositorio `/home/dantas/workspace/pfm-platform/pfm-ai-worker-python`:

1. Em `src/domain/taxonomy.py`, adicione um mapeador canonico `to_core_ledger_taxonomy(code: CategoryCode) -> tuple[str, str]` que converte cada `CategoryCode` do worker para a tupla `(level1_code, level2_code)` oficial do seed Flyway V1 do `pfm-core-ledger-java` (ex.: `VAR_FOOD_RESTAURANT` -> `("ALIMENTACAO", "RESTAURANTES_GASTRONOMIA")`, `VAR_FOOD_GROCERY` -> `("ALIMENTACAO", "SUPERMERCADO_MERCEARIA")`, `VAR_MOBILITY_FUEL` -> `("TRANSPORTE", "COMBUSTIVEL_ETANOL_GASOLINA")`, `VAR_FAMILY_CARE` -> `("SAUDE", "FARMACIA_MEDICAMENTOS")`, `SYS_UNCLASSIFIED` -> `("OUTROS", "NAO_CATEGORIZADO")`).
2. Inclua os campos `ledger_category_code` e `ledger_subcategory_code` em `CategorizedTransaction` (`src/domain/models.py`) para integracao direta com `CommitCategorizedTransactionUseCase` no Core Ledger Java.
3. Crie `migrations/V1__init_ai_rules_rls.sql` documentando o schema PostgreSQL RLS da tabela `learned_merchant_rules` no banco `pfm_ai_rules` (porta host 15433 / container 5432).
4. Adicione teste unitario em `tests/test_three_layer_pipeline.py` validando `to_core_ledger_taxonomy` e execute `.venv/bin/ruff check src tests` e `.venv/bin/pytest -v`.
5. Faca `git add . && git commit -m "feat(taxonomy): add canonical Core Ledger N1/N2 taxonomy mapping and RLS SQL migration"`.
```

---

## Prompt de Remediacao 04 -- Repositorios IaC 1:1 (`pfm-ingestion-bff-infra`, `pfm-forecast-engine-infra` e `pfm-web-infra`)

```text
MODO DE EXECUCAO AUTONOMA: Execute todas as criacoes de arquivos YAML Kubernetes/Helm, workflows CI/CD e commits Git locais de forma 100% autonoma ate concluir e validar tudo. So peca autorizacao caso precise executar comandos em APIs externas, GitHub remoto, AWS ou servicos de terceiros.

Atue como Staff Cloud SRE & DevSecOps Lead nos repositorios de infraestrutura 1:1:

1. Em `/home/dantas/workspace/pfm-platform/pfm-ingestion-bff-infra`:
   - Crie `helm/values.yaml`, `helm/templates/deployment.yaml`, `helm/templates/service.yaml`, `helm/templates/hpa.yaml` e `helm/templates/networkpolicy.yaml` (com limites de RAM, probes `/health`, variaveis OpenTelemetry e `NetworkPolicy` Zero-Trust).
   - Faca `git add . && git commit -m "feat(helm): add complete Kubernetes templates deployment, service, HPA and NetworkPolicy"`.

2. Em `/home/dantas/workspace/pfm-platform/pfm-forecast-engine-infra`:
   - Crie `helm/values.yaml`, `helm/templates/deployment.yaml`, `helm/templates/service.yaml` e `.github/workflows/ci-cd.yml` (validando OpenTofu, Helm e seguranca com `tfsec`/`checkov`).
   - Faca `git add . && git commit -m "feat(helm): add deployment, service templates and GitOps validation workflow"`.

3. Em `/home/dantas/workspace/pfm-platform/pfm-web-infra`:
   - Crie `helm/values.yaml`, `helm/templates/deployment.yaml`, `helm/templates/service.yaml` e `helm/templates/networkpolicy.yaml`.
   - Faca `git add . && git commit -m "feat(helm): add Kubernetes deployment, service and NetworkPolicy templates for pfm-web-nextjs"`.
```

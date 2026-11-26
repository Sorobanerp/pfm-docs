# Bloco 02 — Matriz de Conformidade Backend AppSec (OWASP Top 10 & FinOps First-Security)

> **Escopo:** `pfm-core-ledger-java`, `pfm-forecast-engine-go`, `pfm-ingestion-bff-go`, `pfm-ai-worker-python` e `pfm-finops-manager-infra`.  
> **Padrões de Referência:** OWASP Top 10 (2021/2025), OWASP API Security Top 10, LGPD (Lei nº 13.709/2018), AWS Well-Architected Security & Cost Optimization Pillars (ADR-006, ADR-008, ADR-009, ADR-010).

---

## 1. Matriz de Controles OWASP Top 10 nos Backends

| Categoria OWASP | Risco Mitigado | Implementação Técnica nos Microsserviços | Arquivos / Evidências |
| :--- | :--- | :--- | :--- |
| **A01 — Broken Access Control** | Cross-Tenant Data Leakage (IDOR), Bypass de RLS ou Elevação de Privilégio (`VIEWER` executando mutações) | - **PostgreSQL 16 `FORCE ROW LEVEL SECURITY`:** 100% dos adapters SQL no `pfm-core-ledger-java` injetam `SELECT set_config('app.current_tenant_id', ?, true)` de forma parametrizada na transação ativa.<br>- **Cross-Check JWT vs Header no BFF:** `pfm-ingestion-bff-go` valida `claims.TenantID == X-Tenant-ID` (`403 Forbidden` em divergência).<br>- **RBAC Estrito:** Role `VIEWER` bloqueada em todos os métodos `POST`, `PUT`, `PATCH`, `DELETE`. | `PostgresRlsLedgerRepositoryAdapter.java`, `PostgresRlsUserProfileAdapter.java`, `PostgresRlsTenantSubscriptionAdapter.java`, `internal/adapter/in/http/auth.go`, `server.go` |
| **A02 — Cryptographic Failures** | Exposição de PII em logs (CPF, Cartão, Senha de PDF, Tokens) ou segredos em texto plano | - **Envelope Encryption (AWS KMS):** DEK por tenant criptografada via CMK `alias/pfm-master-key`.<br>- **Sanitização Automática LGPD nos Loggers JSON:** Mascaramento recursivo de `cpf`, `password`, `pdf_password`, `token`, `access_token`, `refresh_token`, `secret`, `api_key`, `authorization`, `card_number` e `pan` nos 4 serviços.<br>- **PDF Password In-Memory Only:** Senhas de PDFs bancários são descartadas imediatamente após extração em RAM e bloqueadas de qualquer persistência ou evento Kafka. | `LgpdMaskingStructuredLogEncoder.java`, `ObservabilityLgpdSanitizer.java`, `otel_lgpd.go`, `src/observability.py`, `src/main.py` |
| **A03 — Injection (SQLi, Log Injection, Prompt Injection)** | SQL Injection em queries ou `SET LOCAL`, Log Forging (`\r\n`) e Prompt Injection no Gemini | - **Zero String Concatenation em SQL:** Uso exclusivo de `PreparedStatement` / `JdbcTemplate` parametrizado (`?`) inclusive em `set_config`.<br>- **Validação Estrita de Chave NFC-e:** Regex estrita `^\d{44}$` antes de qualquer consulta SEFAZ.<br>- **Isolamento de Prompt LLM:** Structured Outputs com schema estrito e sanitização de caracteres de controle. | `PostgresRlsLedgerRepositoryAdapter.java`, `src/observability.py` (`validate_nfce_access_key`) |
| **A04 — Insecure Design & DoS Computacional** | Loop infinito ou exaustão de CPU/Memória em simulações financeiras SAC/Price/Consórcio | - **Guardrails Matemáticos Determinísticos (`pfm-forecast-engine-go`):** Limite estrito de `MaxRemainingInstallments = 600` (50 anos), `maxBalance = 1_000_000_000`, taxas não-negativas `<= 1.0`, `ExtraPaymentCents <= CurrentBalanceCents` e `0 < CurrentDayOfMonth <= TotalDaysInMonth <= 31`. | `contract_amortization_simulator.go`, `run_rate_forecaster.go`, `domain_edge_cases_test.go` |
| **A05 — Security Misconfiguration** | CORS permissivo (`*` com credenciais), payloads gigantes (OOM) ou CloudWatch Logs órfãos | - **CORS Explícito:** Origens validadas via `ALLOWED_ORIGINS` sem wildcard `*` com credenciais em produção.<br>- **Body Size Limits:** `http.MaxBytesReader` limitando `/api/v1/statements/upload` a `10 MB` e rotas JSON a `1 MB`.<br>- **Edge Rate Limiting:** Limite por IP/Tenant em `/auth`, `/register`, `/verify` e `/api/v1/statements/upload`. | `pfm-ingestion-bff-go/internal/adapter/in/http/server.go` |
| **A07 — Identification and Authentication Failures** | Uso indevido de tokens de desenvolvimento (`dev-*`) fora de ambiente local | - **Hard-Block de Dev Tokens em Produção:** `pfm-ingestion-bff-go` rejeita `/api/v1/auth/dev-token` e prefixos `dev-*` sempre que `APP_ENV` não for `local`/`development`, exigindo `Authorization: Bearer <JWT>` assinado. | `pfm-ingestion-bff-go/internal/adapter/in/http/auth.go`, `server.go` |
| **A08 — Software and Data Integrity Failures** | Upload de binários maliciosos disfarçados de PDF | - **Validação de Magic Bytes em RAM:** Verificação obrigatória do cabeçalho `%PDF-` nos primeiros 5 bytes em memória antes de qualquer parsing ou envio ao S3. | `pfm-ingestion-bff-go/internal/adapter/in/http/server.go`, `pfm-ai-worker-python/src/observability.py` |
| **A09 — Security Logging and Monitoring Failures** | Cegueira operacional ou vazamento de PII para plataformas de observabilidade | - **Datadog Unified Service Tagging Plug-and-Play (ADR-010):** `DD_SERVICE`, `DD_ENV`, `DD_VERSION`, `DD_LOGS_INJECTION=true`, `DD_TRACE_SAMPLE_RATE=0.10` e `DD_API_KEY` injetada via AWS Secrets Manager (`secrets` block), com `CLOUDWATCH_LOGS_ENABLED=false`. | `pfm-*-infra/terraform/aws/main.tf`, `ativacao-datadog-pos-implantacao.md` |
| **A10 — Server-Side Request Forgery (SSRF)** | Consulta NFC-e redirecionada para AWS IMDSv1/v2 (`169.254.169.254`), `localhost` ou IPs privados RFC1918 | - **Validador Anti-SSRF (`validate_external_url_no_ssrf`):** Permite exclusivamente `https://`, bloqueia `169.254.169.254`, loopback, link-local e redes privadas, e restringe o domínio a portais autorizados (`*.gov.br`). | `pfm-ai-worker-python/src/observability.py`, `tests/test_adapters_and_wiring.py` |

---

## 2. Governança FinOps SRE & IAM Least Privilege (`pfm-finops-manager-infra`)

1. **Sincronia com a Infraestrutura Atualizada (`us-east-2`):**
   - Gerencia o ciclo `start`/`stop` dos 4 serviços ECS Fargate Spot (`pfm-core-ledger-java`, `pfm-forecast-engine-go`, `pfm-ingestion-bff-go`, `pfm-web-nextjs`) no cluster `pfm-pilot-prod` e da instância RDS PostgreSQL 16 (`pfm-postgres-shared-prod`).
2. **Guardrail Zero-CloudWatch:**
   - Audita continuamente os prefixos `/ecs/pfm`, `/aws/lambda/pfm`, `/aws/pfm` e `/aws/eks/pfm`. Caso qualquer Log Group residual seja detectado, aplica retenção mínima de 1 dia (`put_retention_policy`) e emite alerta estruturado `ZERO_CLOUDWATCH_ALERT` no stdout JSON do Datadog.
3. **IAM Least Privilege:**
   - Role `pfm-finops-manager-role-prod` restrita a ARNs prefixados com `pfm-*` e condição regional `aws:RequestedRegion = us-east-2` (0 wildcards irrestritos em mutações).

---

## 3. Esteira Shift-Left SAST & Supply Chain Security

Todos os repositórios de backend executam obrigatoriamente na branch `develop`:
- **Secret Scanning:** `gitleaks detect --exit-code 1`
- **Poliglota SAST:** `semgrep scan --config auto --error .`
- **Go SAST:** `gosec -exclude-generated -severity high ./...` (`pfm-forecast-engine-go` e `pfm-ingestion-bff-go`)
- **Python SAST:** `bandit -r src -ll -ii` (`pfm-ai-worker-python`)
- **IaC & Container Security:** `trivy config --exit-code 1 --severity CRITICAL,HIGH .` e `trivy image --exit-code 1 --severity CRITICAL,HIGH`

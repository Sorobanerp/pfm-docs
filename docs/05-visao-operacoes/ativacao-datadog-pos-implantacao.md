# Guia de Ativacao Plug-and-Play do Datadog Pos-Implantacao (ADR-010)

> **Escopo:** `pfm-core-ledger-java`, `pfm-forecast-engine-go`, `pfm-ingestion-bff-go`, `pfm-ai-worker-python`, `pfm-finops-manager-infra` e `pfm-shared-infra` (`us-east-2` / Datadog Site `us3.datadoghq.com`).
> **Politica FinOps:** `CLOUDWATCH_LOGS_ENABLED=false` (Zero-CloudWatch Logs) + `DD_TRACE_SAMPLE_RATE=0.10` em producao (`1.0` em ambiente local).

---

## 1. Arquitetura Plug-and-Play (Unified Service Tagging & OpenTelemetry)

Todos os microsservicos de backend e funcoes Lambda foram parametrizados nativamente com as variaveis do **Datadog Unified Service Tagging** e **OpenTelemetry OTLP**, mantendo a politica de **Zero-CloudWatch** e sanitizacao LGPD/PII na borda do logger:

| Variavel | `pfm-core-ledger-java` | `pfm-forecast-engine-go` | `pfm-ingestion-bff-go` | `pfm-ai-worker-python` | `pfm-finops-manager` |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `DD_SERVICE` | `pfm-core-ledger-java` | `pfm-forecast-engine-go` | `pfm-ingestion-bff-go` | `pfm-ai-worker-python` | `pfm-finops-manager` |
| `DD_ENV` | `prod` (`local` dev) | `prod` (`local` dev) | `prod` (`local` dev) | `prod` (`local` dev) | `prod` |
| `DD_VERSION` | `${IMAGE_TAG}` | `${IMAGE_TAG}` | `${IMAGE_TAG}` | `${IMAGE_TAG}` | `1.0.0` |
| `DD_LOGS_INJECTION` | `true` | `true` | `true` | `true` | `true` |
| `DD_TRACE_SAMPLE_RATE` | `0.10` (`1.0` local) | `0.10` (`1.0` local) | `0.10` (`1.0` local) | `0.10` (`1.0` local) | `0.10` |
| `DD_SITE` | `us3.datadoghq.com` | `us3.datadoghq.com` | `us3.datadoghq.com` | `us3.datadoghq.com` | `us3.datadoghq.com` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `https://otel-collector.pfm.internal:4318` | `https://otel-collector.pfm.internal:4318` | `https://otel-collector.pfm.internal:4318` | `https://otel-collector.pfm.internal:4318` | N/A (Lambda stdout JSON) |
| `CLOUDWATCH_LOGS_ENABLED` | `false` | `false` | `false` | `false` | `false` |
| `DD_API_KEY_SECRET_ARN` | `arn:aws:secretsmanager:us-east-2:*:secret:pfm/datadog/api-key-*` | `arn:aws:secretsmanager:us-east-2:*:secret:pfm/datadog/api-key-*` | `arn:aws:secretsmanager:us-east-2:*:secret:pfm/datadog/api-key-*` | `arn:aws:secretsmanager:us-east-2:*:secret:pfm/datadog/api-key-*` | Secret via KMS |

---

## 2. Passo a Passo para Ativacao em 5 Minutos Pos-Deploy

### Passo 1 -- Cadastrar a `DD_API_KEY` no AWS Secrets Manager (`us-east-2`)

O modulo `pfm-shared-infra` provisiona o segredo criptografado com KMS (`alias/pfm-master-key`) sob o prefixo `pfm/datadog/api-key-`. Para injetar a chave real do Datadog sem expor credenciais em codigo ou variaveis de texto plano:

```bash
# 1. Localize o ARN ou nome exato do segredo provisionado pelo OpenTofu:
SECRET_ID=$(aws secretsmanager list-secrets \
  --region us-east-2 \
  --filters Key=name,Values=pfm/datadog/api-key- \
  --query 'SecretList[0].ARN' \
  --output text)

# 2. Grave o valor da DD_API_KEY criptografado via KMS Master Key:
aws secretsmanager put-secret-value \
  --region us-east-2 \
  --secret-id "${SECRET_ID}" \
  --secret-string '{"DD_API_KEY":"<SUA_DATADOG_API_KEY_US3>"}'
```

### Passo 2 -- (Opcional) Ativar Dashboard Unificado e Monitores via OpenTofu

Caso tambem possua a `DD_APP_KEY` para provisionamento automatico dos monitores SLO e de seguranca (Cross-Tenant RLS, DLQ Kafka, p95 Latency e FinOps Budget):

```bash
cd /home/dantas/workspace/pfm-platform/pfm-shared-infra/terraform/environments/aws
tofu apply \
  -var="enable_datadog_monitors=true" \
  -var="datadog_api_key=${DD_API_KEY}" \
  -var="datadog_app_key=${DD_APP_KEY}"
```

### Passo 3 -- Reiniciar Tasks ECS com Zero-Downtime para Carregar o Segredo

Force um novo deployment rolling nas tasks do cluster `pfm-ecs-pilot` sem downtime:

```bash
for SVC in pfm-core-ledger-java pfm-forecast-engine-go pfm-ingestion-bff-go; do
  aws ecs update-service \
    --region us-east-2 \
    --cluster pfm-ecs-pilot \
    --service "${SVC}" \
    --force-new-deployment
done
```

---

## 3. Checklist de Validacao no Datadog (`us3.datadoghq.com`)

1. **Logs Estruturados & Sanitizacao LGPD (`Logs -> Explorer`):**
   - Filtre por `env:prod @service:(pfm-core-ledger-java OR pfm-forecast-engine-go OR pfm-ingestion-bff-go OR pfm-ai-worker-python OR pfm-finops-manager)`.
   - Verifique que todos os eventos exibem `dd.trace_id`, `dd.span_id`, `dd.service`, `dd.env`, `dd.version` e que campos sensiveis (`cpf`, `password`, `token`, `card_number`, `secret`, `api_key`) aparecem mascarados (`***.***.***-**` ou `***REDACTED***`).
2. **APM & Distributed Tracing (`APM -> Service Catalog`):**
   - Confirme a presenca dos servicos com `W3C Trace Context` propagado ponta a ponta (`pfm-ingestion-bff-go` -> `pfm-core-ledger-java` / `pfm-forecast-engine-go` -> Upstash Kafka -> `pfm-ai-worker-python`).
3. **Auditoria Zero-CloudWatch (`pfm-finops-manager`):**
   - Confirme que a execucao da Lambda `pfm-finops-manager-prod` reporta `"cloudwatch_logs_enabled": false` e `"residual_cloudwatch_log_groups": []`.

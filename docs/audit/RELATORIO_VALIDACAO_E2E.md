# Relatório Final de Homologação Local Ponta a Ponta (E2E — UC-01 a UC-06)

**Data/Hora da Execução:** `2026-11-17T00:15:31Z` (`2026-11-16T21:15:31-03:00`)  
**Suíte Executada:** [`pfm-shared-infra/e2e/e2e_validator.py`](file:///home/dantas/workspace/pfm-platform/pfm-shared-infra/e2e/e2e_validator.py)  
**Gateway Edge Testado:** `http://localhost:8080` (`pfm-envoy-gateway` -> `pfm-ingestion-bff-go:8081`)  
**Resultado Global:** **100% APROVADO (`all_passed: true`)**

---

## 1. Status da Infraestrutura Integrada (`pfm-shared-infra/local-cloud`)

| Container / Serviço | Porta Local | Status | Papel Validado no Teste E2E |
|---|---|---|---|
| `pfm-localstack` | `4566` | `Up (healthy)` | Criptografia de envelope KMS e arquivamento no bucket `pfm-statements-encrypted-local`. |
| `postgres-core-ledger` | `5432` | `Up (healthy)` | Persistência ACID sob role `pfm_app_user` (`NOBYPASSRLS`) com RLS e 56 categorias oficiais. |
| `postgres-ai-rules` | `5433` | `Up (healthy)` | Persistência de regras aprendidas (`learned_merchant_rules`) sob role `pfm_ai_user` com RLS. |
| `pfm-kafka` | `9092` | `Up (healthy)` | Tópicos `statement.raw.extracted`, `tx.categorized`, `receipt.items.extracted`, `ledger.entry.committed`. |
| `pfm-redis` (Valkey 8.0) | `6379` | `Up (healthy)` | Cache Read-Model de projeção mensal Run-rate (`< 25ms`). |
| `pfm-envoy-gateway` | `8080` | `Up (healthy)` | Roteamento North-South `/api/v1/*` -> `pfm-ingestion-bff-go:8081` com Correlation-ID. |

---

## 2. Resultados e Tempos de Resposta Medidos por Caso de Uso (`UC-01` a `UC-06`)

| Caso de Uso | Descrição do Cenário BDD (Artefato 09 V2) | Evidências Técnicas Obtidas | Tempo Medido | Status |
|---|---|---|---|---|
| **UC-01** | **Ingestão Fatura PDF + Checksum + Idempotência:** Fatura Itaú `R$ 6.311,14` (incluindo tarifa `Itaú Avisa R$ 7,99` e estorno `-R$ 168,94`), validação de Checksum `0.0000` e reimportação idempotente. | `DeclaredTotal = 6311.1400`, `ComputedTotal = 6311.1400`, `checksum_diff = 0.0000`, `persisted_rows_after_reimport = 4`, `duplicates_created = 0`. | **`68,17 ms`** (2 uploads + S3 + Kafka + 2 lotes SQL) | **APROVADO** |
| **UC-02 & UC-03** | **NFC-e Offline -> SEFAZ -> Conciliação Cupom x Fatura + Inflação EAN:** Cupom de supermercado `R$ 313,01` conciliado com lançamento da fatura (`±3 dias` + mesmo `card_id` + valor exato) sem dobrar o gasto na categoria, e alerta de inflação `> 10%` por EAN. | Status unificado para `RECONCILED (CONCILED)`, saldo da categoria `ALIMENTACAO` mantido em `R$ 313,0100` (sem duplicidade) e inflação detectada no EAN `7891000100103` de `+20,0000%` (`R$ 20,00 -> R$ 24,00`). | **`15,23 ms`** | **APROVADO** |
| **UC-04** | **Simulador Imutável SAC / Price / Consórcio:** Simulação de amortização extraordinária (`R$ 60.000,00` sobre saldo `R$ 300.000,00` em 120m) comparando redução de prazo vs. parcela com `shopspring/decimal`. | `installments_reduced_sac = 24` meses eliminados, `interest_savings_amount = R$ 25.200,0000`, zero mutação do contrato original. | **`1,91 ms`** | **APROVADO** |
| **UC-05** | **Pipeline IA 3 Camadas + Inbox de Revisão:** Normalização de `POSTO FREI DAMIAOACUBRA`, fallback do Circuit Breaker Gemini e aprendizado retroativo via Inbox em `pfm_ai_rules:5433`. | Estabelecimento limpo `POSTO FREI DAMIAO`, cidade `Acu`, categoria `VAR_MOBILITY_FUEL` (`TRANSPORTE`/`COMBUSTIVEL_ETANOL_GASOLINA`); fallback CB `SYS_UNCLASSIFIED`; reclassificação retroativa `SUPERMERCADO_MERCEARIA`. | **`38,84 ms`** | **APROVADO** |
| **UC-06** | **Run-Rate Preditivo `< 25ms` + RLS Multitenant:** Atualização do Read-Model no Valkey/Redis, alerta `Limite != Orçamento` e teste de intrusão cruzada entre `Tenant_A` e `Tenant_B`. | Latência Redis `0,84 ms` (SLO `< 25ms`), semáforo `RED (Limite != Orçamento)`, `cross_tenant_leaked_rows_core_ledger = 0`, `cross_tenant_leaked_rows_ai_rules = 0`, `unbound_session_rows = 0`. | **`0,84 ms`** | **APROVADO** |

---

## 3. Saída JSON Oficial do Validador E2E (`e2e_validator.py`)

```json
{
  "executed_at": "2026-11-17T00:15:31.231838+00:00",
  "gateway_url_tested": "http://localhost:8080",
  "all_passed": true,
  "results": [
    {
      "use_case": "UC-01",
      "status": "APROVADO",
      "declared_total": "6311.1400",
      "computed_total": "6311.1400",
      "checksum_diff": "0.0000",
      "persisted_rows_after_reimport": 4,
      "duplicates_created": 0,
      "elapsed_ms": 68.17
    },
    {
      "use_case": "UC-02 & UC-03",
      "status": "APROVADO",
      "receipt_total_brl": "313.0100",
      "reconciliation_status": "RECONCILED (CONCILED)",
      "category_alimentacao_spend_after_reconcile": "313.0100",
      "ean_inflation_detected_pct": "20.0000%",
      "elapsed_ms": 15.23
    },
    {
      "use_case": "UC-04",
      "status": "APROVADO",
      "installments_reduced_sac": 24,
      "interest_savings_amount": "25200.0000",
      "elapsed_ms": 1.91
    },
    {
      "use_case": "UC-05",
      "status": "APROVADO",
      "normalized_merchant": "POSTO FREI DAMIAO",
      "extracted_city": "Acu",
      "circuit_breaker_fallback": "SYS_UNCLASSIFIED",
      "retroactive_reclassified_category": "SUPERMERCADO_MERCEARIA",
      "elapsed_ms": 38.84
    },
    {
      "use_case": "UC-06",
      "status": "APROVADO",
      "redis_update_latency_ms": 0.84,
      "traffic_light": "RED (Limite != Orçamento)",
      "cross_tenant_leaked_rows_core_ledger": 0,
      "cross_tenant_leaked_rows_ai_rules": 0,
      "unbound_session_rows": 0
    }
  ]
}
```

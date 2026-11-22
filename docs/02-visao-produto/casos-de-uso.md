# 2.2. Casos de Uso do Produto (UC-01 a UC-08) -- Governanca Familiar, Contratos e SaaS Admin

<span class="badge-green">Artefato 05 - Casos de Uso (UC-01 a UC-08)</span>
<span class="badge-glow">Exemplos e Payloads 100% em BRL (R$)</span>

Este documento especifica os **8 Casos de Uso Oficiais (`UC-01` a `UC-08`)** da plataforma **PFM Core Banking**, cobrindo desde a ingestao de faturas PDF em memoria RAM e simulacao de financiamentos SAC/Price/Consorcio ate o Painel SaaS Admin (`US-12`) e a Central de Perfil, Familia e LGPD (`US-13`).

---

## 1. Matriz Consolidada dos Casos de Uso (`UC-01` a `UC-08`)

| Codigo | Titulo do Caso de Uso | Ator Principal | Servicos Envolvidos | Invariante de Negocio Validada |
| :---: | :--- | :--- | :--- | :--- |
| **`UC-01`** | Ingestao de Fatura PDF em RAM + Checksum + Idempotencia | Titular (`OWNER`) | `pfm-ingestion-bff-go`, `pfm-core-ledger-java` | Parsing 100% em RAM (`Zero-Disk`), validacao `soma(itens) == total_fatura` em `R$` (`RN04`) e deduplicacao SHA-256. |
| **`UC-02`** | Desdobramento de Parcelas e Residuo Decimal Bancario | Titular (`OWNER`), Membro (`MEMBER`) | `pfm-core-ledger-java` | Compra parcelada em `Nx` com alocacao do residuo de centavos na 1a parcela (`RN06`) e abatimento integral do limite do cartao (`RN02`). |
| **`UC-03`** | Apuracao de Regime de Competencia vs. Regime de Caixa | Titular (`OWNER`) | `pfm-core-ledger-java`, `pfm-ingestion-bff-go` | Separacao entre consumo de orcamento no mes da compra (Competencia) e liquidacao da fatura (Caixa) sem dupla contagem (`RN01`). |
| **`UC-04`** | Categorizacao Inteligente em 3 Camadas (Meta `< 5%` em Outros) | Motor IA | `pfm-ai-worker-python`, `pfm-core-ledger-java` | Funil de 3 camadas (Regras/Cache -> Modelo Local -> LLM Estruturado) isolado do banco transacional. |
| **`UC-05`** | Projecao de Fluxo de Caixa (30/60/90d) & Simulador SAC/Price/Consorcio | Titular (`OWNER`) | `pfm-forecast-engine-go` | Projecao de saldo livre em `R$` e simulacao matematica exata de amortizacao extraordinaria (Reduzir Prazo vs. Reduzir Parcela). |
| **`UC-06`** | Conciliacao NFC-e e Alertas Proativos de Orcamento (`80%` / `100%`) | Titular / Membro | `pfm-ingestion-bff-go`, `pfm-forecast-engine-go` | Leitura de QR Code SEFAZ, fusao sem duplicidade com fatura PDF (`RN04`) e alerta preventivo ao atingir `80%` do teto em `R$`. |
| **`UC-07`** | Painel SaaS Admin (Gestao de Tenants, Planos e Quotas) | Admin (`PLATFORM_ADMIN`) | `pfm-core-ledger-java`, `pfm-web-nextjs` | Gestao de planos (`FREE`, `INDIVIDUAL_PRO R$ 29,90`, `FAMILY_PLUS R$ 49,90`) com bloqueio Zero-Trust de acesso a lancamentos privados (`RN05`). |
| **`UC-08`** | Central de Perfil, Gestao Familiar e Direitos LGPD (Crypto-Shredding) | Titular (`OWNER`) | `pfm-core-ledger-java`, `pfm-ingestion-bff-go` | Convite de membros (`MEMBER`, `VIEWER`) com alca de gastos em `R$`, cofre KMS de senha PDF, exportacao JSON/CSV e Crypto-Shredding (`US-13`). |

---

## 2. Detalhamento dos Fluxos de Negocio e Payloads em BRL (`R$`)

### 2.1. `UC-01` e `UC-03` -- Upload de Fatura PDF e Resumo Executivo (Competencia vs. Caixa)

Quando o titular envia a fatura mensal do cartao de credito (ex.: total de `R$ 550,00` composto por Supermercado `R$ 350,00` e Farmacia `R$ 200,00`), o `pfm-ingestion-bff-go` valida o checksum em RAM e atualiza o painel executivo:

```json
{
  "tenant_id": "11111111-1111-1111-1111-111111111111",
  "scope": "FAMILY",
  "competence_month": "2026-11",
  "currency": "BRL",
  "realized_income": "18200.00",
  "settled_fixed_expenses": "5400.00",
  "current_card_invoices": "6890.45",
  "scheduled_installments": "2450.00",
  "variable_spend_to_date": "2180.00",
  "projected_free_cashflow": "7080.00"
}
```

### 2.2. `UC-05` -- Simulador de Contratos de Longo Prazo (SAC, Price e Consorcio)

Permite simular o impacto de uma amortizacao extraordinaria (ex.: aporte de `R$ 20.000,00` de FGTS ou bonus anual sobre um saldo devedor de `R$ 240.000,00` em 120 meses a `0,85% a.m.`):

```json
{
  "contract_id": "33333333-3333-3333-3333-333333333333",
  "amortization_system": "SAC",
  "prepayment_strategy": "REDUCE_TERM",
  "currency": "BRL",
  "outstanding_balance": "240000.00",
  "remaining_installments": 120,
  "monthly_interest_rate": "0.0085",
  "monthly_insurance_and_fees": "65.00",
  "extra_amortization_amount": "20000.00",
  "installments_reduced": 12,
  "interest_savings_amount": "24850.40",
  "effective_roi_percentage": "124.25"
}
```

### 2.3. `UC-07` -- Governanca do Painel SaaS Admin (`US-12`)

- **Atores Autorizados:** Exclusivamente `PLATFORM_ADMIN`.
- **Operacoes Permitidas:**
  - Listar tenants com status (`TRIAL`, `ACTIVE`, `PAST_DUE`, `SUSPENDED`) e plano (`FREE`, `INDIVIDUAL_PRO`, `FAMILY_PLUS`);
  - Alterar plano ou status de assinatura com gravacao obrigatoria no `audit_log` imutavel;
  - Consultar metricas globais anonimizadas.
- **Bloqueio Zero-Trust LGPD:** Qualquer tentativa de um token `PLATFORM_ADMIN` de acessar endpoints de transacoes (`/api/v1/transactions`) ou perfil privado (`/api/v1/profile`) retorna `403 Forbidden`.

### 2.4. `UC-08` -- Central de Perfil, Familia e Direitos LGPD (`US-13`)

- **Papeis Familiares (RBAC):**
  - `OWNER`: Titular da assinatura; gerencia membros, tetos em `R$`, senhas PDF de cartoes e direitos LGPD.
  - `MEMBER`: Registra gastos, escaneia NFC-e e acompanha seu teto mensal individual (ex.: `R$ 2.500,00/mes`).
  - `VIEWER`: Consulta dashboards em modo somente leitura (`403 Forbidden` para mutacoes).
- **Direitos Art. 18 da LGPD:**
  - `POST /api/v1/profile/export`: Exporta o pacote completo de dados do tenant em `JSON` ou `CSV`.
  - `POST /api/v1/profile/crypto-shred`: Destroi irreversivelmente a chave DEK do tenant no KMS e anonimiza os metadados.

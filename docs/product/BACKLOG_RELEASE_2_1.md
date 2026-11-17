# Backlog Estratégico — Release 2.1 (Pós-Piloto Familiar de 5 Usuários)

**Objetivo Executivo da Release 2.1:** Evoluir a plataforma PFM Core Banking V2 da operação validada no Piloto Familiar (5 usuários) para uma plataforma **B2C / Family Office Multi-Tenant comercial**, combinando conectividade automática via **Open Finance Brasil**, consolidação de investimentos (**B3 / Tesouro Direto / FIIs**), alertas proativos em tempo real (**FCM / Web Push**), **Assistente Conversacional RAG (`pgvector` + Gemini)** e **Billing SaaS recorrente (PIX Automático / Stripe)**.

---

## Visão Consolidada do Roadmap Release 2.1

| ID | Épico / Iniciativa Estratégica | Repositórios Impactados | Prioridade | Estimativa (Story Points / Sprints) |
|---|---|---|---|---|
| **R2.1-01** | Integração Direta **Open Finance Brasil** (Pluggy / Belvo) complementar ao PDF | `pfm-ingestion-bff-go`, `pfm-contracts`, `pfm-core-ledger-java` | **P0 (Alta)** | `21 SP` (~1,5 Sprints) |
| **R2.1-02** | Parser Nativo de **Extratos de Corretoras (B3 / Tesouro Direto / FIIs)** — Natureza `WEALTH` (`PATRIMONIO`) | `pfm-ingestion-bff-go`, `pfm-core-ledger-java`, `pfm-forecast-engine-go`, `pfm-web-nextjs` | **P1 (Alta)** | `13 SP` (~1 Sprint) |
| **R2.1-03** | **Notificações Push Proativas** (FCM Android + Web Push VAPID) para Run-rate, Faturas e Inflação EAN `>10%` | `pfm-forecast-engine-go`, `pfm-mobile-android`, `pfm-web-nextjs` | **P1 (Média-Alta)** | `13 SP` (~1 Sprint) |
| **R2.1-04** | **Assistente Conversacional Financeiro (RAG `pgvector` + Gemini)** em Linguagem Natural | `pfm-ai-worker-python`, `pfm-ingestion-bff-go`, `pfm-web-nextjs` | **P2 (Média)** | `21 SP` (~1,5 Sprints) |
| **R2.1-05** | **Onboarding Self-Service Multi-Tenant & Billing SaaS** (PIX Automático / Stripe + KMS DEK por Tenant) | `pfm-core-ledger-java`, `pfm-ingestion-bff-go`, `pfm-web-nextjs`, `pfm-shared-infra` | **P2 (Expansão Comercial)** | `21 SP` (~1,5 Sprints) |

---

## Detalhamento Técnico das Histórias (DoR, DoD e Critérios de Aceite)

### R2.1-01 — Integração Direta Open Finance Brasil (via Agregador Regulado Belvo / Pluggy)
- **Descrição:** Conectar contas correntes e cartões de crédito via API regulada do Open Finance Brasil (Pluggy/Belvo Webhook mTLS) no `pfm-ingestion-bff-go`, operando de forma **complementar** ao upload de faturas PDF (mantendo a mesma chave de idempotência SHA-256 `tenant_id|card_last4|competence_date|amount_fixed_4|merchant_normalized|parcela_atual/total` para evitar duplicidade caso o usuário suba o PDF de uma fatura já sincronizada via Open Finance).
- **Definition of Ready (DoR):**
  1. Credenciais Sandbox do agregador Open Finance (Pluggy/Belvo) provisionadas no AWS Secrets Manager / LocalStack.
  2. Contrato Protobuf `OpenFinanceSyncWebhookEvent` adicionado em `pfm-contracts`.
  3. Regra de deduplicação cruzada (`OpenFinance` x `PDFUpload`) validada com o domínio do `pfm-core-ledger-java`.
- **Definition of Done (DoD):**
  1. Adaptador `internal/adapter/in/webhook/openfinance_handler.go` no `pfm-ingestion-bff-go` validando assinatura HMAC-SHA256 / mTLS do webhook.
  2. Publicação no tópico `statement.raw.extracted` com `0` duplicatas ao cruzar lançamentos Open Finance com faturas PDF já importadas.
  3. Cobertura de testes unitários e de contrato `>= 90%` + Circuit Breaker (Timeout 5s).
- **Estimativa de Esforço:** `21 Story Points` (`~12 dias-engenheiro`).

---

### R2.1-02 — Parser Nativo para Extratos de Corretoras (B3 / Tesouro Direto / FIIs) — Natureza `WEALTH`
- **Descrição:** Adicionar suporte no `pfm-ingestion-bff-go` e `pfm-core-ledger-java` para ingestão de notas de corretagem SINACOR (PDF/CSV) e extratos consolidados da Área do Investidor B3 (Tesouro Direto, Ações, FIIs e CDBs), conciliando aportes mensais com a natureza `NEUTRAL_PATRIMONIAL` (`PATRIMONIO`: `APORTE_RENDA_FIXA`, `APORTE_RENDA_VARIAVEL`, `RESERVA_EMERGENCIA`) e proventos/dividendos em `RECEITAS` (`RENDIMENTOS_DIVIDENDOS`).
- **Definition of Ready (DoR):**
  1. Layout padrão de nota SINACOR e extrato CSV/XLSX da B3 mapeados com exemplos anonimizados.
  2. Regras contábeis de partida dobrada para compra/venda de ativos e recebimento de dividendos/JCP especificadas sem uso de `float`.
- **Definition of Done (DoD):**
  1. Parser em RAM `internal/adapter/out/b3/brokerage_note_parser.go` usando `shopspring/decimal` (escala 4, `RoundBank`).
  2. Visão de evolução patrimonial integrada ao `pfm-web-nextjs` distinguindo **Aporte Líquido do Mês** vs. **Valorização / Dividendos**.
  3. Testes automatizados validando cálculo de preço médio e proventos isentos.
- **Estimativa de Esforço:** `13 Story Points` (`~8 dias-engenheiro`).

---

### R2.1-03 — Notificações Push Proativas (FCM Android + Web Push VAPID)
- **Descrição:** Emitir alertas push acionáveis em tempo real para o app Android (`pfm-mobile-android`) e navegador (`pfm-web-nextjs`) em três gatilhos de domínio:
  1. **Mudança de Semáforo Run-Rate:** Transição de `GREEN` para `YELLOW` (`> 85%` da renda líquida) ou `RED` (`> 100%` / risco de déficit).
  2. **Fechamento / Vencimento de Fatura:** Lembrete `D-3` antes do `closing_day` e `due_day` de cada cartão na Matriz Multi-Cartões.
  3. **Alerta de Inflação Pessoal (`> 10%` por EAN):** Notificação imediata após sincronização do cupom NFC-e quando um item recorrente sofre alta abrupta.
- **Definition of Ready (DoR):**
  1. Tópico Kafka `notification.alert.triggered` definido em `pfm-contracts`.
  2. Chaves VAPID (Web Push) e configuração Firebase Cloud Messaging (FCM) parametrizadas via Secret Manager.
- **Definition of Done (DoD):**
  1. Deduplicação de alertas por janela de 24h (`idempotency_key` no Valkey/Redis) evitando *alert fatigue*.
  2. Deep-link na notificação abrindo diretamente a tela `/inbox`, `/cards` ou o detalhe do cupom no Android.
  3. Testes E2E cobrindo disparo e recebimento do alerta.
- **Estimativa de Esforço:** `13 Story Points` (`~7 dias-engenheiro`).

---

### R2.1-04 — Assistente Conversacional Financeiro (RAG sobre `pgvector` + Google Gemini)
- **Descrição:** Aproveitar a extensão `vector` (`pgvector`) já provisionada no banco `pfm_ai_rules` (`:5433`) e no `pfm_core_ledger` (`:5432`) para permitir que o titular faça perguntas financeiras em linguagem natural no portal Web e no Android (ex.: *"Quanto gastei em restaurantes em Acu nos últimos 6 meses?"*, *"Qual cartão tem mais parcelas livres a partir de março?"*, *"Qual produto subiu mais de preço no supermercado?"*).
- **Definition of Ready (DoR):**
  1. Schema de embeddings vetoriais (`vector(768)`) com índice `HNSW` e isolamento estrito `ENABLE/FORCE ROW LEVEL SECURITY` por `tenant_id`.
  2. Prompt de sistema Text-to-SQL / Tool-Calling seguro (somente leitura `SELECT` sob transação RLS `SET LOCAL app.current_tenant_id`).
- **Definition of Done (DoD):**
  1. Caso de uso `AskFinancialAssistantUseCase` no `pfm-ai-worker-python` retornando resposta estruturada com números exatos em `Decimal` (zero alucinação aritmética: toda soma é calculada pelo PostgreSQL/Python e apenas narrada pelo Gemini).
  2. Protegido por Timeout (8s), Rate Limiter por tenant e Circuit Breaker.
  3. Testes de segurança garantindo `0` vazamento de contexto entre `Tenant_A` e `Tenant_B` em consultas vetoriais `pgvector`.
- **Estimativa de Esforço:** `21 Story Points` (`~12 dias-engenheiro`).

---

### R2.1-05 — Onboarding Self-Service Multi-Tenant & Billing SaaS (Stripe / PIX Recorrente)
- **Descrição:** Automatizar o provisionamento self-service de novos tenants familiares além dos 5 usuários do piloto: criação automática do registro em `tenants`, geração de Data Encryption Key (DEK) exclusiva no KMS (`AesGcmEnvelopeEncryptionKmsAdapter`), convite de membros (`OWNER` / `MEMBER` com `spending_allowance`) e cobrança de assinatura mensal via PIX Automático (Banco Central) ou Stripe Billing.
- **Definition of Ready (DoR):**
  1. Planos de assinatura (`Pilot Free`, `Family Pro`, `Private Wealth`) e limites de cota (`TenantRateLimiter`) definidos.
  2. Fluxo de criação de DEK por tenant validado com AWS KMS / GCP Cloud KMS / Azure Key Vault.
- **Definition of Done (DoD):**
  1. Fluxo completo de cadastro, geração de DEK KMS, seed inicial de contas/cartões e webhook de confirmação de pagamento (`PIX` / `Stripe`).
  2. Exportação completa de dados (`LGPD Data Portability`) e exclusão criptográfica (*Crypto-Shredding* via revogação da DEK do tenant).
  3. Testes de integração multitenant validando isolamento completo desde o segundo zero do onboarding.
- **Estimativa de Esforço:** `21 Story Points` (`~13 dias-engenheiro`).

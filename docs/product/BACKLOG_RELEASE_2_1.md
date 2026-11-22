# Backlog Estrategico -- Release 2.1 (Pos-Piloto Familiar de 5 Usuarios)

**Objetivo Executivo da Release 2.1:** Evoluir a plataforma PFM Core Banking V2 da operacao validada no Piloto Familiar (5 usuarios) para uma plataforma **B2C / Family Office Multi-Tenant comercial**, combinando conectividade automatica via **Open Finance Brasil**, consolidacao de investimentos (**B3 / Tesouro Direto / FIIs**), alertas proativos em tempo real (**FCM / Web Push**), **Assistente Conversacional RAG (`pgvector` + Gemini)** e **Billing SaaS recorrente (PIX Automatico / Stripe)**.

---

## Visao Consolidada do Roadmap Release 2.1

| ID | Epico / Iniciativa Estrategica | Repositorios Impactados | Prioridade | Estimativa (Story Points / Sprints) |
|---|---|---|---|---|
| **R2.1-01** | Integracao Direta **Open Finance Brasil** (Pluggy / Belvo) complementar ao PDF | `pfm-ingestion-bff-go`, `pfm-contracts`, `pfm-core-ledger-java` | **P0 (Alta)** | `21 SP` (~1,5 Sprints) |
| **R2.1-02** | Parser Nativo de **Extratos de Corretoras (B3 / Tesouro Direto / FIIs)** -- Natureza `WEALTH` (`PATRIMONIO`) | `pfm-ingestion-bff-go`, `pfm-core-ledger-java`, `pfm-forecast-engine-go`, `pfm-web-nextjs` | **P1 (Alta)** | `13 SP` (~1 Sprint) |
| **R2.1-03** | **Notificacoes Push Proativas** (FCM Android + Web Push VAPID) para Run-rate, Faturas e Inflacao EAN `>10%` | `pfm-forecast-engine-go`, `pfm-mobile-android`, `pfm-web-nextjs` | **P1 (Media-Alta)** | `13 SP` (~1 Sprint) |
| **R2.1-04** | **Assistente Conversacional Financeiro (RAG `pgvector` + Gemini)** em Linguagem Natural | `pfm-ai-worker-python`, `pfm-ingestion-bff-go`, `pfm-web-nextjs` | **P2 (Media)** | `21 SP` (~1,5 Sprints) |
| **R2.1-05** | **Onboarding Self-Service Multi-Tenant & Billing SaaS** (PIX Automatico / Stripe + KMS DEK por Tenant) | `pfm-core-ledger-java`, `pfm-ingestion-bff-go`, `pfm-web-nextjs`, `pfm-shared-infra` | **P2 (Expansao Comercial)** | `21 SP` (~1,5 Sprints) |

---

## Detalhamento Tecnico das Historias (DoR, DoD e Criterios de Aceite)

### R2.1-01 -- Integracao Direta Open Finance Brasil (via Agregador Regulado Belvo / Pluggy)
- **Descricao:** Conectar contas correntes e cartoes de credito via API regulada do Open Finance Brasil (Pluggy/Belvo Webhook mTLS) no `pfm-ingestion-bff-go`, operando de forma **complementar** ao upload de faturas PDF (mantendo a mesma chave de idempotencia SHA-256 `tenant_id|card_last4|competence_date|amount_fixed_4|merchant_normalized|parcela_atual/total` para evitar duplicidade caso o usuario suba o PDF de uma fatura ja sincronizada via Open Finance).
- **Definition of Ready (DoR):**
  1. Credenciais Sandbox do agregador Open Finance (Pluggy/Belvo) provisionadas no AWS Secrets Manager / LocalStack.
  2. Contrato Protobuf `OpenFinanceSyncWebhookEvent` adicionado em `pfm-contracts`.
  3. Regra de deduplicacao cruzada (`OpenFinance` x `PDFUpload`) validada com o dominio do `pfm-core-ledger-java`.
- **Definition of Done (DoD):**
  1. Adaptador `internal/adapter/in/webhook/openfinance_handler.go` no `pfm-ingestion-bff-go` validando assinatura HMAC-SHA256 / mTLS do webhook.
  2. Publicacao no topico `statement.raw.extracted` com `0` duplicatas ao cruzar lancamentos Open Finance com faturas PDF ja importadas.
  3. Cobertura de testes unitarios e de contrato `>= 90%` + Circuit Breaker (Timeout 5s).
- **Estimativa de Esforco:** `21 Story Points` (`~12 dias-engenheiro`).

---

### R2.1-02 -- Parser Nativo para Extratos de Corretoras (B3 / Tesouro Direto / FIIs) -- Natureza `WEALTH`
- **Descricao:** Adicionar suporte no `pfm-ingestion-bff-go` e `pfm-core-ledger-java` para ingestao de notas de corretagem SINACOR (PDF/CSV) e extratos consolidados da Area do Investidor B3 (Tesouro Direto, Acoes, FIIs e CDBs), conciliando aportes mensais com a natureza `NEUTRAL_PATRIMONIAL` (`PATRIMONIO`: `APORTE_RENDA_FIXA`, `APORTE_RENDA_VARIAVEL`, `RESERVA_EMERGENCIA`) e proventos/dividendos em `RECEITAS` (`RENDIMENTOS_DIVIDENDOS`).
- **Definition of Ready (DoR):**
  1. Layout padrao de nota SINACOR e extrato CSV/XLSX da B3 mapeados com exemplos anonimizados.
  2. Regras contabeis de partida dobrada para compra/venda de ativos e recebimento de dividendos/JCP especificadas sem uso de `float`.
- **Definition of Done (DoD):**
  1. Parser em RAM `internal/adapter/out/b3/brokerage_note_parser.go` usando `shopspring/decimal` (escala 4, `RoundBank`).
  2. Visao de evolucao patrimonial integrada ao `pfm-web-nextjs` distinguindo **Aporte Liquido do Mes** vs. **Valorizacao / Dividendos**.
  3. Testes automatizados validando calculo de preco medio e proventos isentos.
- **Estimativa de Esforco:** `13 Story Points` (`~8 dias-engenheiro`).

---

### R2.1-03 -- Notificacoes Push Proativas (FCM Android + Web Push VAPID)
- **Descricao:** Emitir alertas push acionaveis em tempo real para o app Android (`pfm-mobile-android`) e navegador (`pfm-web-nextjs`) em tres gatilhos de dominio:
  1. **Mudanca de Semaforo Run-Rate:** Transicao de `GREEN` para `YELLOW` (`> 85%` da renda liquida) ou `RED` (`> 100%` / risco de deficit).
  2. **Fechamento / Vencimento de Fatura:** Lembrete `D-3` antes do `closing_day` e `due_day` de cada cartao na Matriz Multi-Cartoes.
  3. **Alerta de Inflacao Pessoal (`> 10%` por EAN):** Notificacao imediata apos sincronizacao do cupom NFC-e quando um item recorrente sofre alta abrupta.
- **Definition of Ready (DoR):**
  1. Topico Kafka `notification.alert.triggered` definido em `pfm-contracts`.
  2. Chaves VAPID (Web Push) e configuracao Firebase Cloud Messaging (FCM) parametrizadas via Secret Manager.
- **Definition of Done (DoD):**
  1. Deduplicacao de alertas por janela de 24h (`idempotency_key` no Valkey/Redis) evitando *alert fatigue*.
  2. Deep-link na notificacao abrindo diretamente a tela `/inbox`, `/cards` ou o detalhe do cupom no Android.
  3. Testes E2E cobrindo disparo e recebimento do alerta.
- **Estimativa de Esforco:** `13 Story Points` (`~7 dias-engenheiro`).

---

### R2.1-04 -- Assistente Conversacional Financeiro (RAG sobre `pgvector` + Google Gemini)
- **Descricao:** Aproveitar a extensao `vector` (`pgvector`) ja provisionada no banco `pfm_ai_rules` (`:5433`) e no `pfm_core_ledger` (`:5432`) para permitir que o titular faca perguntas financeiras em linguagem natural no portal Web e no Android (ex.: *"Quanto gastei em restaurantes em Acu nos ultimos 6 meses?"*, *"Qual cartao tem mais parcelas livres a partir de marco?"*, *"Qual produto subiu mais de preco no supermercado?"*).
- **Definition of Ready (DoR):**
  1. Schema de embeddings vetoriais (`vector(768)`) com indice `HNSW` e isolamento estrito `ENABLE/FORCE ROW LEVEL SECURITY` por `tenant_id`.
  2. Prompt de sistema Text-to-SQL / Tool-Calling seguro (somente leitura `SELECT` sob transacao RLS `SET LOCAL app.current_tenant_id`).
- **Definition of Done (DoD):**
  1. Caso de uso `AskFinancialAssistantUseCase` no `pfm-ai-worker-python` retornando resposta estruturada com numeros exatos em `Decimal` (zero alucinacao aritmetica: toda soma e calculada pelo PostgreSQL/Python e apenas narrada pelo Gemini).
  2. Protegido por Timeout (8s), Rate Limiter por tenant e Circuit Breaker.
  3. Testes de seguranca garantindo `0` vazamento de contexto entre `Tenant_A` e `Tenant_B` em consultas vetoriais `pgvector`.
- **Estimativa de Esforco:** `21 Story Points` (`~12 dias-engenheiro`).

---

### R2.1-05 -- Onboarding Self-Service Multi-Tenant & Billing SaaS (Stripe / PIX Recorrente)
- **Descricao:** Automatizar o provisionamento self-service de novos tenants familiares alem dos 5 usuarios do piloto: criacao automatica do registro em `tenants`, geracao de Data Encryption Key (DEK) exclusiva no KMS (`AesGcmEnvelopeEncryptionKmsAdapter`), convite de membros (`OWNER` / `MEMBER` com `spending_allowance`) e cobranca de assinatura mensal via PIX Automatico (Banco Central) ou Stripe Billing.
- **Definition of Ready (DoR):**
  1. Planos de assinatura (`Pilot Free`, `Family Pro`, `Private Wealth`) e limites de cota (`TenantRateLimiter`) definidos.
  2. Fluxo de criacao de DEK por tenant validado com AWS KMS / GCP Cloud KMS / Azure Key Vault.
- **Definition of Done (DoD):**
  1. Fluxo completo de cadastro, geracao de DEK KMS, seed inicial de contas/cartoes e webhook de confirmacao de pagamento (`PIX` / `Stripe`).
  2. Exportacao completa de dados (`LGPD Data Portability`) e exclusao criptografica (*Crypto-Shredding* via revogacao da DEK do tenant).
  3. Testes de integracao multitenant validando isolamento completo desde o segundo zero do onboarding.
- **Estimativa de Esforco:** `21 Story Points` (`~13 dias-engenheiro`).

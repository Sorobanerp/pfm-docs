# 2.3. Backlog Scrum (US-01 a US-14), Contratos DoR/DoD e Cenarios BDD Gherkin

<span class="badge-green">Artefatos 08 e 09 - Backlog &amp; BDD Gherkin</span>
<span class="badge-glow">100% dos Valores em Real Brasileiro (R$ / BRL)</span>

Este documento consolida os contratos de qualidade (**Definition of Ready** e **Definition of Done**), o **Backlog Scrum do Produto (`US-01` a `US-14`)** e as especificacoes executaveis em **Gherkin (BDD)** com todos os valores financeiros padronizados em **Real Brasileiro (`R$`)**.

---

## 1. Contratos de Governanca Agil (DoR & DoD)

### 1.1. Definition of Ready (DoR)
- [x] **Vinculo de Dominio:** Referencia explicita as regras `RN01` a `RN06` e aos casos de uso `UC-01` a `UC-08`.
- [x] **Contract-First (`pfm-contracts`):** Contratos OpenAPI 3.1 (`openapi.yaml`) e Protobuf v1 revisados.
- [x] **Criterios BDD em BRL (`R$`):** Cenarios Gherkin cobrindo caminho feliz, borda decimal e isolamento multi-tenant.
- [x] **Analise LGPD & RLS:** Impacto em `FORCE ROW LEVEL SECURITY` e `audit_log` mapeado.

### 1.2. Definition of Done (DoD)
- [x] **Arquitetura Hexagonal Isolada:** Dominio puro sem dependencia de frameworks externos.
- [x] **Qualidade & Cobertura:** Testes unitarios e de integracao aprovados com Quality Gate ativo no SonarCloud.
- [x] **Seguranca Zero-Trust:** Zero segredos no Git (`gitleaks`), `0` vulnerabilidades criticas (`trivy`) e RLS validado entre tenants distintos.

---

## 2. Backlog Scrum do Produto (`US-01` a `US-14`)

| ID | Epico | User Story (Formato Connextra) | Regras / Casos de Uso | Pontos | Prioridade |
| :-: | :--- | :--- | :---: | :---: | :---: |
| **US-01** | Seguranca & RLS | **Como** Engenheiro de Plataforma, **quero** isolar todas as operacoes por `tenant_id` via PostgreSQL 16 RLS e KMS Envelope Encryption, **para** garantir vazamento zero entre familias. | RN05, UC-08 | 8 | P0 |
| **US-02** | Core Ledger | **Como** Titular da Conta, **quero** registrar transacoes em `R$` com segregacao entre Data de Competencia e Data de Caixa em precisao `NUMERIC(19,4)`, **para** ter saldos exatos sem erros de centavos. | RN01, RN06, UC-03 | 8 | P0 |
| **US-03** | Cartoes & Parcelas | **Como** Titular do Cartao, **quero** registrar compras parceladas em `Nx` com alocacao do residuo de centavos na 1a parcela e abatimento imediato do limite total em `R$`, **para** controlar faturas futuras. | RN01, RN02, RN06, UC-02 | 8 | P0 |
| **US-04** | Cartoes & Estornos | **Como** Titular do Cartao, **quero** que estornos em faturas abertas ou fechadas sejam vinculados a categoria original sem apagar o historico, **para** recompor meu limite em `R$` sem inflar minha renda. | RN03, RN06, UC-03 | 5 | P1 |
| **US-05** | Orcamento Mensal | **Como** Titular da Conta, **quero** definir tetos de orcamento mensal em `R$` por categoria de 2 niveis apurados por Competencia, **para** receber alertas em `80%` e `100%` de consumo. | RN01, RN02, UC-06 | 5 | P1 |
| **US-06** | Ingestao PDF em RAM | **Como** Titular da Conta, **quero** importar faturas PDF processadas 100% em memoria RAM com validacao matematica de checksum em `R$`, **para** conciliar meus gastos sem gravar o PDF em disco. | RN04, RN06, UC-01 | 13 | P0 |
| **US-07** | Mobile NFC-e Offline | **Como** Usuario Mobile, **quero** escanear QR Codes de cupons fiscais NFC-e mesmo sem internet, **para** sincroniza-los automaticamente quando a conexao retornar. | RN04, UC-06 | 8 | P1 |
| **US-08** | SEFAZ Scraper | **Como** Plataforma de Ingestao, **quero** extrair itens, valores em `R$` e CNPJ de notas NFC-e com Circuit Breaker e Retries, **para** enriquecer os gastos e monitorar variacao de precos. | RN04, UC-06 | 8 | P1 |
| **US-09** | Categorizacao IA 3 Camadas | **Como** Titular da Conta, **quero** que meus lancamentos sejam classificados automaticamente na Taxonomia de 2 Niveis mantendo menos de `5%` em `OUTROS`, **para** eliminar trabalho manual. | Taxonomia 2 Niveis, UC-04 | 13 | P1 |
| **US-10** | Motor de Conciliacao | **Como** Titular da Conta, **quero** que cupons NFC-e e linhas de fatura PDF da mesma compra em `R$` sejam fundidos sem duplicidade, **para** manter meu orcamento integro. | RN04, UC-06 | 13 | P0 |
| **US-11** | Simulador de Contratos | **Como** Titular da Conta, **quero** simular amortizacoes extraordinarias em contratos SAC, Price e Consorcio em `R$`, **para** comparar a economia de juros entre reduzir prazo ou reduzir parcela. | RN06, UC-05 | 8 | P1 |
| **US-12** | Painel SaaS Admin | **Como** Administrador (`PLATFORM_ADMIN`), **quero** gerir planos (`FREE`, `INDIVIDUAL_PRO R$ 29,90`, `FAMILY_PLUS R$ 49,90`) e status de assinatura sem acesso a dados financeiros privados, **para** operar o SaaS com conformidade LGPD. | RN05, UC-07 | 8 | P1 |
| **US-13** | Perfil, Familia & LGPD | **Como** Titular (`OWNER`), **quero** convidar membros familiares (`MEMBER`, `VIEWER`) com alca em `R$`, exportar meus dados e solicitar Crypto-Shredding, **para** exercer soberania total sobre minha conta. | RN05, UC-08 | 8 | P1 |
| **US-14** | IDS Design System "PFM Pulse" | **Como** Usuario da Plataforma, **quero** visualizar meus indicadores financeiros em 10 segundos por dia na interface Web e Android com paleta `#8CBA51` e `#DEFF8B`, **para** decidir com clareza e zero fadiga visual. | IDS PFM Pulse | 8 | P1 |

---

## 3. Especificacoes Executaveis BDD (Cenarios Gherkin em BRL)

### Feature 01: Desdobramento de Parcelas, Competencia vs. Caixa e Residuo (US-02, US-03, US-05)

```gherkin
# language: pt
Funcionalidade: Escrituracao de Compra Parcelada no Cartao (Competencia vs. Caixa e Residuo RN06)
  Como um Titular da Conta PFM Core Banking
  Quero registrar compras parceladas no cartao de credito em Reais (R$)
  Para que meu limite total seja sensibilizado integralmente, meu orcamento mensal reflita apenas a competencia da parcela e o residuo de centavos fique na 1a parcela

  Contexto:
    Dado que o tenant autenticado possui o ID "11111111-1111-1111-1111-111111111111"
    E possui um cartao de credito ativo com Limite Total de R$ 5.000,00 e Limite Disponivel de R$ 5.000,00
    E possui um orcamento mensal na categoria "LAZER :: VIAGENS_HOSPEDAGEM" de R$ 500,00 para a competencia "2026-11"

  Cenario: Compra de R$ 100,00 em 3 parcelas sem juros com alocacao de residuo na 1a parcela (RN01, RN02, RN06)
    Quando o titular registra uma compra no cartao de credito no valor total de R$ 100,00 em 3 parcelas na data "2026-11-15" na categoria "LAZER :: VIAGENS_HOSPEDAGEM"
    Entao o sistema deve criar 3 parcelas vinculadas com precisao NUMERIC(19,4):
      | Parcela | Competencia | Valor da Parcela | Status Inicial |
      | 1/3     | 2026-11     | R$ 33,34         | OPEN_STATEMENT |
      | 2/3     | 2026-12     | R$ 33,33         | FUTURE_INSTALL |
      | 3/3     | 2027-01     | R$ 33,33         | FUTURE_INSTALL |
    E a soma exata das 3 parcelas deve ser R$ 100,00
    E o Limite Disponivel do cartao deve ser reduzido imediatamente em R$ 100,00 passando para R$ 4.900,00
    E o consumo do orcamento de "LAZER :: VIAGENS_HOSPEDAGEM" na competencia "2026-11" deve ser de apenas R$ 33,34
    E o Regime de Caixa de "2026-11" nao deve registrar saida de conta corrente ate a data de pagamento efetivo da fatura
```

---

### Feature 02: Tratamento Contabil de Estornos em Fatura Fechada (US-04 / RN03)

```gherkin
# language: pt
Funcionalidade: Processamento de Estorno em Fatura Posterior sem Exclusao de Historico (RN03)
  Como um Titular do Cartao
  Quero que estornos recebidos apos o fechamento da fatura ajustem meu saldo devedor em Reais (R$) e mantenham vinculo com a categoria original
  Para evitar distorcao artificial de receitas e preservar a trilha de auditoria

  Cenario: Estorno total de R$ 250,00 recebido na fatura seguinte apos fechamento da fatura original
    Dado que o titular realizou uma compra de R$ 250,00 em "LAZER :: VESTUARIO_CALCADOS" na competencia "2026-10" com ID "tx-orig-991"
    E a fatura da competencia "2026-10" encontra-se no status "CLOSED_AND_PAID"
    Quando a operadora envia um evento de estorno de R$ 250,00 na data "2026-11-12" referenciando a compra "tx-orig-991"
    Entao o lancamento original "tx-orig-991" deve permanecer inalterado no banco de dados (Append-Only)
    E um novo lancamento do tipo "REFUND_CREDIT" no valor de R$ -250,00 deve ser criado vinculado a "tx-orig-991"
    E o lancamento de estorno deve ser classificado em "LAZER :: VESTUARIO_CALCADOS" (e nunca como salario/renda)
    E o saldo a pagar da fatura aberta de "2026-11" deve ser reduzido em R$ 250,00
    E o Limite Disponivel do cartao deve ser recomposto em R$ 250,00
```

---

### Feature 03: Ingestao de Fatura PDF em RAM e Conciliacao com NFC-e sem Duplicidade (US-06, US-07, US-10)

```gherkin
# language: pt
Funcionalidade: Ingestao PDF Zero-Disk e Conciliacao Automatica com Cupom NFC-e (RN04)
  Como um Titular da Conta
  Quero que um gasto em Reais (R$) capturado via QR Code NFC-e seja conciliado automaticamente quando a fatura PDF for importada
  Para que eu tenha os itens detalhados da nota fiscal sem duplicar a despesa no meu orcamento

  Cenario: Conciliacao automatica entre NFC-e de R$ 184,90 e linha correspondente da Fatura PDF
    Dado que o titular escaneou um QR Code NFC-e no "SUPERMERCADO VERDE LTDA" em "2026-11-10T14:22:00" no valor de R$ 184,90
    E o cupom NFC-e gerou um lancamento provisorio "tx-nfce-101" na categoria "ALIMENTACAO :: SUPERMERCADO_MERCEARIA"
    Quando o titular faz upload da fatura PDF do cartao contendo a linha "10/11 SUPERMERCADO VERDE R$ 184,90"
    Entao o servico "pfm-ingestion-bff-go" deve processar o stream inteiramente em memoria RAM sem criar arquivos em disco
    E o motor de conciliacao deve identificar o match com score >= 0.90 com o lancamento "tx-nfce-101"
    E o status do lancamento "tx-nfce-101" deve mudar para "CONCILED"
    E nenhum segundo lancamento de R$ 184,90 deve ser debitado do orcamento
```

---

### Feature 04: Painel SaaS Admin, Gestao Familiar e Isolamento PostgreSQL RLS (US-01, US-12, US-13)

```gherkin
# language: pt
Funcionalidade: Governanca Familiar, Planos SaaS em BRL e Isolamento Zero-Trust via PostgreSQL 16 RLS (RN05)
  Como Titular da Conta e Engenheiro de Seguranca
  Quero garantir que nenhum tenant ou administrador SaaS acesse lancamentos privados de outro tenant

  Cenario: Bloqueio de leitura cross-tenant pelo PostgreSQL Row-Level Security (RN05)
    Dado que o Tenant Alpha ("11111111-1111-1111-1111-111111111111") registrou uma compra de R$ 450,75 em "ALIMENTACAO :: SUPERMERCADO_MERCEARIA"
    Quando o Tenant Beta ("22222222-2222-2222-2222-222222222222") consulta a listagem de transacoes "/api/v1/transactions"
    Entao a politica "FORCE ROW LEVEL SECURITY" do PostgreSQL 16 deve filtrar por "current_setting('app.current_tenant_id')"
    E a resposta para o Tenant Beta deve retornar 0 transacoes pertencentes ao Tenant Alpha

  Cenario: Convite de membro familiar no plano FAMILY_PLUS (R$ 49,90/mes) com teto mensal de R$ 2.000,00
    Dado que o titular "OWNER" possui assinatura ativa no plano "FAMILY_PLUS" (R$ 49,90/mes)
    Quando o titular convida "conjuge@familia.com.br" com papel "MEMBER" e alca mensal de R$ 2.000,00
    Entao o membro convidado pode registrar despesas ate o teto monitorado de R$ 2.000,00
    E o membro com papel "VIEWER" recebe HTTP 403 Forbidden caso tente alterar orcamentos ou remover membros
```

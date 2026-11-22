# Backlog Scrum (US-01 a US-15), Contratos DoR/DoD V3 & Cenarios BDD

Este documento define os contratos de qualidade de engenharia (**Definition of Ready V3** e **Definition of Done V3**), o **Backlog do Produto V3 (`US-01` a `US-15`)** priorizado por epicos e as especificacoes executaveis em **Gherkin (BDD)**.

---

## 1. Contratos de Governanca Agil (DoR & DoD V3)

### Definition of Ready (DoR V3) -- Criterios de Entrada na Sprint

Nenhuma User Story pode ser puxada para o Sprint Backlog sem cumprir **100%** dos itens abaixo:

- [x] **Vinculo de Dominio & Regra de Negocio**: A historia referencia explicitamente quais regras (**RN01 a RN06**) e ADRs (**ADR-001 a ADR-010**) sao impactados.
- [x] **Contrato First (`pfm-contracts`)**: Alteracoes de API REST (OpenAPI 3.1), gRPC (Protobuf v3) ou eventos Kafka (JSON Schema/Avro) ja estao especificadas e revisadas.
- [x] **Criterios de Aceite em Gherkin**: Minimo de 1 cenario de caminho feliz (*Happy Path*), 1 cenario de borda financeira/arredondamento e 1 cenario de falha/idempotencia escritos em Gherkin.
- [x] **Analise de Seguranca & Multitenancy**: Impacto em PostgreSQL RLS (`tenant_id`), `audit_log` append-only e privacidade (PII / LGPD) mapeado.
- [x] **Metricas de Observabilidade Definidas**: SLIs e spans OpenTelemetry (Tail-Based Sampling) esperados documentados na historia.

### Definition of Done (DoD V3) -- Criterios de Conclusao e Producao

Uma User Story so e considerada **DONE** quando validada automaticamente no pipeline CI/CD:

- [x] **Arquitetura Hexagonal Verificada**: Testes de arquitetura (*ArchUnit* no Java / linters em Go e Python) aprovados com **zero dependencias** de frameworks dentro do pacote `domain` (e zero acesso direto ao PostgreSQL no `pfm-ai-worker-python`).
- [x] **Cobertura de Testes Automatizados**:
  - Cobertura de linhas e branches $\ge 90\%$ no `domain` e Gate global $\ge 95\%$ no **SonarCloud Portfolio**;
  - Testes de integracao reais com **Testcontainers** (PostgreSQL 16 com RLS ativo, Kafka e Redis);
  - Testes de contrato (*Contract Testing*) e cenarios BDD Gherkin passando.
- [x] **Seguranca & Qualidade Estatica**: SAST (Semgrep + SonarCloud Quality Gate A), escaneamento de vulnerabilidades de container/IaC (Trivy sem CVEs `CRITICAL`/`HIGH`) e validacao de RLS cross-tenant.
- [x] **Governanca SemVer & Changelog**: Commits no padrao **Conventional Commits**, versionamento **SemVer 2.0.0** e entrada gerada no `CHANGELOG.md`.
- [x] **Telemetria Ativa & Auditoria**: Traces OTel exportados para o Datadog Unified Dashboard (com `Redaction Processor` Zero PII), eventos criticos gravados no `audit_log` append-only e DLQs cifradas via KMS configuradas.

---

## 2. Backlog Scrum Completo (US-01 a US-15)

| ID | Epico | User Story (Formato Connextra) | Regras / ADRs | Story Points | Prioridade |
| :-: | :--- | :--- | :---: | :---: | :---: |
| **US-01** | Seguranca & Multitenancy | **Como** Engenheiro de Plataforma, **quero** isolar todas as operacoes por `tenant_id` via PostgreSQL RLS e Envelope Encryption KMS, **para** garantir vazamento zero entre contas. | RN05, ADR-006 | 8 | P0 (Blocker) |
| **US-02** | Core Ledger | **Como** Titular da Conta, **quero** registrar transacoes com segregacao entre Data de Competencia e Data de Caixa em precisao `NUMERIC(19,4)`, **para** ter saldos exatos sem erros de centavos. | RN01, RN06, ADR-001 | 8 | P0 (Blocker) |
| **US-03** | Cartoes & Parcelas | **Como** Titular do Cartao, **quero** registrar compras parceladas em $N$ vezes com alocacao automatica do residuo de centavos na 1a parcela e sensibilizacao correta do limite total, **para** acompanhar faturas futuras e limite disponivel. | RN01, RN02, RN06 | 8 | P0 (Critica) |
| **US-04** | Cartoes & Estornos | **Como** Titular do Cartao, **quero** que estornos totais ou parciais em faturas abertas ou fechadas sejam vinculados a compra original sem apagar o historico, **para** recompor meu limite e ajustar a categoria correta. | RN03, RN06 | 5 | P1 (Alta) |
| **US-05** | Orcamento (Budget) | **Como** Titular da Conta, **quero** definir tetos de orcamento mensal por categoria de 2 niveis apurados pelo Regime de Competencia (independente do limite do cartao), **para** receber alertas em 80% e 100% de consumo. | RN01, RN02, ADR-005 | 5 | P1 (Alta) |
| **US-06** | Ingestao PDF (RAM) | **Como** Titular da Conta, **quero** enviar faturas PDF do meu cartao para processamento 100% em memoria RAM (`Zero-Disk`), **para** importar todos os lancamentos sem que meu arquivo fique salvo em disco. | RN06, ADR-001, ADR-006 | 13 | P0 (Critica) |
| **US-07** | Mobile NFC-e Offline | **Como** Usuario Mobile, **quero** escanear o QR Code de cupons fiscais NFC-e mesmo sem internet (modo offline-first), **para** que sejam sincronizados automaticamente quando houver conexao. | ADR-001, ADR-003, ADR-004 | 8 | P1 (Alta) |
| **US-08** | SEFAZ Scraper | **Como** Plataforma de Ingestao, **quero** extrair de forma resiliente os itens e CNPJ da NFC-e nos portais SEFAZ estaduais com Circuit Breaker e Retries, **para** enriquecer os gastos mesmo quando a SEFAZ oscilar. | ADR-004, ADR-005 | 8 | P1 (Alta) |
| **US-09** | IA Categorizer 3-Tier (Serverless) | **Como** Titular da Conta, **quero** que minhas transacoes sejam classificadas automaticamente na Taxonomia Oficial de 2 Niveis pelo Worker IA Serverless (**AWS Lambda Arm64**, custo $0 ocioso) em 3 camadas (L1 $\rightarrow$ L2 ONNX $\rightarrow$ L3 LLM) sem acesso direto ao PostgreSQL, **para** nao categorizar gastos manualmente com seguranca e baixo custo. | Taxonomia 2 Niveis, ADR-009 | 13 | P1 (Alta) |
| **US-10** | Motor de Conciliacao | **Como** Titular da Conta, **quero** que cupons NFC-e, faturas PDF e lancamentos do extrato referentes a mesma compra sejam conciliados sem duplicar meu saldo contabil, **para** manter minha contabilidade integra. | RN04, ADR-005 | 13 | P0 (Critica) |
| **US-11** | Web Portal & Dashboards | **Como** Titular da Conta, **quero** visualizar no Portal Web o comparativo de Regime de Competencia vs. Regime de Caixa, evolucao do orcamento e fila de conciliacao assistida, **para** tomar decisoes financeiras claras. | RN01, RN02, RN04 | 8 | P2 (Media) |
| **US-12** | Painel SaaS Admin | **Como** Administrador da Plataforma (`PLATFORM_ADMIN`), **quero** visualizar todos os tenants (familias/contas), gerenciar planos (`FREE`, `INDIVIDUAL_PRO`, `FAMILY_PLUS`), status de assinatura (`TRIAL`, `ACTIVE`, `PAST_DUE`, `SUSPENDED`), quotas de ingestao/IA e metricas globais de uso sem expor dados financeiros privados (respeitando PostgreSQL RLS), **para** administrar a plataforma com governanca e privacidade. | RN05, ADR-006 | 8 | P1 (Alta) |
| **US-13** | Perfil, Familia & LGPD | **Como** Titular (`OWNER`) ou Membro (`MEMBER`), **quero** gerenciar meu perfil, convidar/remover membros familiares com papeis (`OWNER`, `MEMBER`, `VIEWER`), configurar metas/tetos por categoria, gerenciar chaves/senhas de cartoes cifradas via KMS, exportar meus dados (LGPD) e solicitar exclusao criptografica (*Crypto-Shredding*), **para** ter controle total sobre minha familia e meus dados. | RN05, ADR-006 | 8 | P1 (Alta) |
| **US-14** | Design System & UX | **Como** Usuario da Plataforma, **quero** navegar por uma interface refinada no padrao Apple/Adobe Craft com paleta "Organic Financial Pulse" (`#8CBA51`, `#DEFF8B`, `#FBCEB5`, `#FF5D6C`), layout responsivo *fluid full-width* e jornadas guiadas para cada Caso de Uso (`UC-01` a `UC-08`), **para** gerenciar minhas financas com prazer estetico e clareza cognitiva. | Design System, WCAG AAA | 8 | P1 (Alta) |
| **US-15** | FinOps Manager Lambda | **Como** Engenheiro SRE/FinOps, **quero** estacionar automaticamente as tarefas computacionais e o RDS PostgreSQL as 20h30 BRT e religa-los as 06h00 BRT via AWS Lambda + EventBridge Scheduler (`pfm-finops-manager-infra`), **para** reduzir custos ociosos noturnos em `us-east-2`. | FinOps MVP, ADR-008 | 5 | P1 (Alta) |

---

## 3. Especificacoes Executaveis BDD (Cenarios Gherkin)

### Feature 01: Desdobramento de Parcelas, Competencia vs. Caixa e Residuo (US-02, US-03, US-05)

```gherkin
# language: pt
Funcionalidade: Escrituracao de Compra Parcelada no Cartao (Competencia vs. Caixa e Residuo RN06)
  Como um Titular da Conta PFM Core Banking
  Quero registrar compras parceladas no cartao de credito
  Para que meu limite total seja sensibilizado integralmente, meu orcamento mensal reflita apenas a competencia da parcela e o residuo de centavos seja alocado na 1a parcela

  Contexto:
    Dado que o tenant autenticado possui o ID "01933000-0000-7000-8000-000000000001"
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
  Quero que estornos recebidos apos o fechamento da fatura ajustem meu saldo devedor e mantenham vinculo com a compra original
  Para evitar distorcao artificial de receitas e preservar a trilha de auditoria

  Cenario: Estorno total recebido na fatura seguinte apos fechamento da fatura original
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
Funcionalidade: Ingestao PDF Zero-Disk e Conciliacao Automatica com Cupom NFC-e (RN04, ADR-006)
  Como um Titular da Conta
  Quero que um gasto capturado via QR Code NFC-e seja conciliado automaticamente quando a fatura PDF for importada
  Para que eu tenha os itens detalhados da nota fiscal sem duplicar a despesa no meu orcamento

  Cenario: Conciliacao automatica de alta confianca entre NFC-e previamente escaneada e linha de Fatura PDF
    Dado que o titular escaneou offline um QR Code NFC-e no "SUPERMERCADO VERDE LTDA" (CNPJ "12.345.678/0001-90") em "2026-11-10T14:22:00" no valor de R$ 184,90
    E o cupom NFC-e gerou um lancamento provisorio "tx-nfce-101" na categoria "ALIMENTACAO :: SUPERMERCADO_MERCEARIA" contendo 14 itens fiscais
    Quando o titular faz upload da fatura PDF do cartao contendo a linha "10/11 SUPERMERCADO VERDE R$ 184,90"
    Entao o servico "pfm-ingestion-pdf-service" deve processar o stream inteiramente em memoria RAM sem criar arquivos em disco
    E o servico "pfm-reconcile-service" deve identificar o match com score >= 0.90 com o lancamento "tx-nfce-101"
    E o status do lancamento "tx-nfce-101" deve mudar para "CONCILED" vinculado a fatura do cartao
    E nenhum segundo lancamento de R$ 184,90 deve ser debitado do orcamento de "ALIMENTACAO :: SUPERMERCADO_MERCEARIA"
```

---

### Feature 04: Isolamento Multitenant PostgreSQL RLS e Pipeline IA 3 Camadas (US-01, US-09)

```gherkin
# language: pt
Funcionalidade: Isolamento Zero-Trust via RLS (RN05) e Degradacao Graciosa na Categorizacao IA (ADR-004)
  Como Engenheiro de Confiabilidade e Seguranca
  Quero garantir que um tenant jamais acesse registros de outro tenant e que falhas no provedor LLM nao interrompam o registro contabil

  Cenario: Bloqueio de leitura cross-tenant pelo PostgreSQL Row-Level Security (RN05 / ADR-006)
    Dado que o Tenant "A" ("01933000-0000-7000-8000-00000000000A") possui 50 transacoes gravadas na tabela "ledger_entries"
    E o Tenant "B" ("01933000-0000-7000-8000-00000000000B") autentica-se com um JWT valido no API Gateway
    Quando uma consulta SQL sem clausula WHERE explicita e executada na sessao do Tenant "B"
    Entao a politica "FORCE ROW LEVEL SECURITY" do PostgreSQL deve filtrar estritamente por "current_setting('app.current_tenant_id')"
    E nenhum registro pertencente ao Tenant "A" deve ser retornado

  Cenario: Fallback gracioso quando a Camada 3 (Cloud LLM) sofre timeout para um estabelecimento desconhecido
    Dado uma transacao com descricao atipica "PG *X9Z KIOSK 441" que nao obteve match na Camada 1 (Regras/Cache)
    E cujo modelo local ONNX na Camada 2 retornou confianca de 0.48 (abaixo do limiar minimo de 0.82)
    E o provedor externo de Cloud LLM (Camada 3) esta indisponivel com Circuit Breaker no estado "OPEN"
    Quando o "pfm-ledger-service" solicita a categorizacao ao "pfm-ai-categorizer-service"
    Entao o categorizador deve responder em menos de 50ms com a categoria de fallback "OUTROS :: NAO_CATEGORIZADO" e flag "requires_review = true"
    E a transacao deve ser persistida com sucesso no Ledger sem retornar erro 5xx ao usuario
```

---

### Feature 05: Painel SaaS Admin e Gestao de Quotas/Planos Multitenant (US-12 / RN05 / ADR-006)

```gherkin
# language: pt
Funcionalidade: Painel SaaS Admin com Visibilidade Global e Protecao Estrita Zero-Trust RLS (US-12)
  Como um Administrador da Plataforma (PLATFORM_ADMIN)
  Quero visualizar metricas agregadas de todos os tenants, gerenciar planos e status de assinatura
  Para administrar a operacao SaaS com governanca comercial sem jamais violar a privacidade e o sigilo bancario dos clientes

  Contexto:
    Dado que o usuario autenticado possui o papel "PLATFORM_ADMIN"
    E existem 150 tenants cadastrados na plataforma distribuidos entre planos "FREE", "INDIVIDUAL_PRO" e "FAMILY_PLUS"

  Cenario: Visualizacao de metricas agregadas de faturamento e consumo sem exposicao de lancamentos privados
    Quando o administrador acessa o endpoint "/api/v1/admin/tenants/metrics"
    Entao o sistema deve retornar o total consolidado de tenants por status:
      | Status    | Quantidade |
      | ACTIVE    | 138        |
      | TRIAL     | 8          |
      | PAST_DUE  | 3          |
      | SUSPENDED | 1          |
    E o painel deve exibir o volume global de transacoes ingeridas e o consumo de tokens de IA
    E nenhuma linha de lancamento contabil ("ledger_entries") ou fatura privada ("card_statements") de nenhum tenant deve ser retornada na resposta

  Cenario: Transicao de assinatura para PAST_DUE e SUSPENDED com bloqueio de ingestao e preservacao de leitura
    Dado que o tenant "01933000-0000-7000-8000-00000000000C" no plano "FAMILY_PLUS" teve falha de cobranca ha 6 dias
    Quando o job de conciliacao de faturamento executa
    Entao o status da assinatura do tenant deve ser atualizado para "SUSPENDED"
    E tentativas de upload de nova fatura PDF pelo titular devem retornar erro HTTP 402 Payment Required com a mensagem "Assinatura suspensa. Por favor, regularize seu pagamento para continuar importando faturas."
    E a consulta ao extrato historico de lancamentos existentes deve continuar liberada em modo leitura (Read-Only)
```

---

### Feature 06: Central de Perfil, Gestao Familiar e Crypto-Shredding LGPD (US-13 / RN05 / ADR-006)

```gherkin
# language: pt
Funcionalidade: Gestao de Membros Familiares, Funcoes RBAC e Exclusao Criptografica Crypto-Shredding (US-13)
  Como um Titular da Conta (OWNER)
  Quero convidar membros familiares com permissoes segregadas e exercer meu direito de esquecimento LGPD via Crypto-Shredding
  Para governar o orcamento colaborativo da minha familia e manter controle soberano sobre meus dados pessoais

  Cenario: Convite de membro familiar com papel MEMBER e teto de gastos individual
    Dado que o titular "OWNER" do tenant "01933000-0000-7000-8000-00000000000D" possui plano "FAMILY_PLUS"
    Quando o titular envia um convite para o e-mail "conjuge@familia.com" com papel "MEMBER" e teto mensal de R$ 2.000,00
    Entao um token de convite com validade de 48 horas deve ser gerado
    E quando o membro aceita o convite, ele deve visualizar apenas seu proprio consumo e lancamentos autorizados
    E o membro "MEMBER" nao deve ter permissao para alterar os dados de faturamento da assinatura ou remover outros membros

  Cenario: Exclusao definitiva de conta via Crypto-Shredding (Destruicao Irreversivel de Chave KMS)
    Dado que o titular da conta solicita o encerramento definitivo e exclusao dos dados da familia conforme o Artigo 18 da LGPD
    E confirma a solicitacao digitando "EXCLUIR_DEFINITIVAMENTE_MINHA_CONTA" com autenticacao em dois fatores (MFA)
    Quando o comando de Crypto-Shredding e processado pelo servico de seguranca
    Entao o adaptador KMS deve revogar e destruir permanentemente a Data Encryption Key (DEK) vinculada ao "tenant_id"
    E todos os registros nas tabelas do PostgreSQL devem ter status alterado para "CRYPTO_SHREDDED" com metadados PII zerados
    E qualquer tentativa futura de decifrar os dados historicos nos backups resultara em falha criptografica irrecuperavel
```

---

### Feature 07: Experiencia Visual, Responsividade Full-Width e Paleta Organic Pulse (US-14 / Design System)

```gherkin
# language: pt
Funcionalidade: Interface Widescreen Fluida, Design System Apple Craft e Paleta Organic Financial Pulse (US-14)
  Como um Usuario da Plataforma PFM
  Quero interagir com um dashboard financeiro que responda fluidamente em qualquer resolucao e utilize cores funcionais
  Para tomar decisoes financeiras sem cansaco visual e com feedback instantaneo sobre minha saude financeira

  Cenario: Aplicacao funcional da paleta "Organic Financial Pulse" e alinhamento numerico bancario
    Dado que o usuario acessa o dashboard executivo no portal Web
    Quando o saldo da conta e as metas do mes estao em conformidade com o planejado (consumo < 80%)
    Entao o componente de pulso financeiro deve exibir a cor primaria "#8CBA51" (Organic Olive) com acentos luminosos em "#DEFF8B" (Vibrant Lime)
    E quando uma categoria atinge 85% do teto, a badge de status deve transicionar suavemente para "#FBCEB5" (Warm Peach)
    E quando uma categoria atinge 102% do teto, o indicador deve alertar em "#FF5D6C" (Coral Red)
    E todas as tabelas contabeis devem renderizar valores com a familia tipografica "SF Mono" / "JetBrains Mono" alinhados estritamente a direita

  Cenario: Layout responsivo fluid full-width sem rolagem horizontal em telas ultrawide
    Dado que o usuario acessa a plataforma em um monitor Ultrawide (2560x1080 ou 3440x1440)
    Quando a tela e renderizada
    Entao os paineis de "Regime de Competencia", "Regime de Caixa" e "Fila de Conciliacao" devem ocupar a largura total util da viewport
    E nenhuma barra de rolagem horizontal indesejada deve ser gerada no navegador
    E a barra de navegacao lateral deve manter estado colapsavel com transicoes suaves a 60 FPS
```

---

### Feature 08: Auditoria Imutavel (`audit_log` + RLS), DLQ Cifrada KMS & Worker IA Serverless (US-09 / ADR-009 / ADR-010)

```gherkin
# language: pt
Funcionalidade: Trilha de Auditoria Imutavel, DLQ Cifrada KMS e Execucao Serverless do Worker IA (ADR-009 / ADR-010)
  Como Engenheiro de Seguranca e SRE
  Quero garantir que toda mutacao critica gere um registro append-only protegido por RLS, que falhas persistentes sejam isoladas em DLQ cifrada e que o Worker IA opere isolado do PostgreSQL
  Para assegurar conformidade regulatoria e custo zero ocioso em IA

  Cenario: Imutabilidade estrita da tabela audit_log e isolamento por tenant via RLS (ADR-010)
    Dado que o titular "OWNER" alterou o teto de orcamento da categoria "ALIMENTACAO"
    E um registro de auditoria foi gravado na tabela "audit_log" com "tenant_id" e "trace_id"
    Quando uma rotina de aplicacao tenta executar UPDATE ou DELETE sobre a tabela "audit_log"
    Entao o PostgreSQL deve rejeitar a operacao por ausencia de privilegio (Role Append-Only)
    E qualquer consulta de outro tenant deve retornar 0 registros devido ao FORCE ROW LEVEL SECURITY

  Cenario: Worker IA Serverless (AWS Lambda Arm64) processa evento Kafka sem abrir conexao SQL e envia falha irrecuperavel para DLQ cifrada (ADR-009)
    Dado um lote de 50 transacoes publicado no topico Upstash Kafka "pfm.transactions.raw"
    Quando a funcao AWS Lambda Arm64 "pfm-ai-worker-python" e acionada pelo evento
    Entao ela deve executar a categorizacao L1/L2/L3 utilizando apenas Upstash Redis e modelos ONNX em memoria
    E nenhuma conexao TCP ou driver PostgreSQL deve ser inicializado pelo worker
    E caso uma mensagem possua schema corrompido apos 3 tentativas, o payload deve ser cifrado via KMS e encaminhado para "pfm.transactions.raw.dlq"
```

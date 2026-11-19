# Backlog Scrum (US-01 a US-15), Contratos DoR/DoD V2 & Cenários BDD

Este documento define os contratos de qualidade de engenharia (**Definition of Ready V2** e **Definition of Done V2**), o **Backlog do Produto (US-01 a US-11)** priorizado por épicos e as especificações executáveis em **Gherkin (BDD)**.

---

## 1. Contratos de Governança Ágil (DoR & DoD V2)

### Definition of Ready (DoR V2) — Critérios de Entrada na Sprint

Nenhuma User Story pode ser puxada para o Sprint Backlog sem cumprir **100%** dos itens abaixo:

- [x] **Vínculo de Domínio & Regra de Negócio**: A história referencia explicitamente quais regras (**RN01 a RN06**) e ADRs (**ADR-001 a ADR-007**) são impactados.
- [x] **Contrato First (`pfm-contracts`)**: Alterações de API REST (OpenAPI 3.1), gRPC (Protobuf v3) ou eventos Kafka (JSON Schema/Avro) já estão especificadas e revisadas.
- [x] **Critérios de Aceite em Gherkin**: Mínimo de 1 cenário de caminho feliz (*Happy Path*), 1 cenário de borda financeira/arredondamento e 1 cenário de falha/idempotência escritos em Gherkin.
- [x] **Análise de Segurança & Multitenancy**: Impacto em PostgreSQL RLS (`tenant_id`) e privacidade (PII / LGPD) mapeado.
- [x] **Métricas de Observabilidade Definidas**: SLIs e spans OpenTelemetry esperados documentados na história.

### Definition of Done (DoD V2) — Critérios de Conclusão e Produção

Uma User Story só é considerada **DONE** quando validada automaticamente no pipeline CI/CD:

- [x] **Arquitetura Hexagonal Verificada**: Testes de arquitetura (*ArchUnit* no Java / linters em Go e Python) aprovados com **zero dependências** de frameworks dentro do pacote `domain`.
- [x] **Cobertura de Testes Automatizados**:
  - Cobertura de linhas e branches $\ge 90\%$ no `domain` (regras contábeis RN01–RN06);
  - Testes de integração reais com **Testcontainers** (PostgreSQL 16 com RLS ativo, Kafka e Redis);
  - Testes de contrato (*Contract Testing*) e cenários BDD Gherkin passando.
- [x] **Segurança & Qualidade Estática**: SAST (SonarQube Quality Gate A), escaneamento de vulnerabilidades de container (Trivy sem CVEs `CRITICAL`/`HIGH`) e validação de RLS cross-tenant (tentativa de leitura por outro tenant deve retornar 0 registros).
- [x] **Idempotência & Resiliência**: Mutação validada com repetição de `Idempotency-Key` e Transactional Outbox testado.
- [x] **Telemetria Ativa**: Traces OpenTelemetry, logs JSON estruturados (com `trace_id`, `span_id`, `tenant_id` e zero PII) e métricas Prometheus expostas.

---

## 2. Backlog Scrum Completo (US-01 a US-15)

| ID | Épico | User Story (Formato Connextra) | Regras / ADRs | Story Points | Prioridade |
| :-: | :--- | :--- | :---: | :---: | :---: |
| **US-01** | Segurança & Multitenancy | **Como** Engenheiro de Plataforma, **quero** isolar todas as operações por `tenant_id` via PostgreSQL RLS e Envelope Encryption KMS, **para** garantir vazamento zero entre contas. | RN05, ADR-006 | 8 | P0 (Blocker) |
| **US-02** | Core Ledger | **Como** Titular da Conta, **quero** registrar transações com segregação entre Data de Competência e Data de Caixa em precisão `NUMERIC(19,4)`, **para** ter saldos exatos sem erros de centavos. | RN01, RN06, ADR-001 | 8 | P0 (Blocker) |
| **US-03** | Cartões & Parcelas | **Como** Titular do Cartão, **quero** registrar compras parceladas em $N$ vezes com alocação automática do resíduo de centavos na 1ª parcela e sensibilização correta do limite total, **para** acompanhar faturas futuras e limite disponível. | RN01, RN02, RN06 | 8 | P0 (Crítica) |
| **US-04** | Cartões & Estornos | **Como** Titular do Cartão, **quero** que estornos totais ou parciais em faturas abertas ou fechadas sejam vinculados à compra original sem apagar o histórico, **para** recompor meu limite e ajustar a categoria correta. | RN03, RN06 | 5 | P1 (Alta) |
| **US-05** | Orçamento (Budget) | **Como** Titular da Conta, **quero** definir tetos de orçamento mensal por categoria de 2 níveis apurados pelo Regime de Competência (independente do limite do cartão), **para** receber alertas em 80% e 100% de consumo. | RN01, RN02, ADR-005 | 5 | P1 (Alta) |
| **US-06** | Ingestão PDF (RAM) | **Como** Titular da Conta, **quero** enviar faturas PDF do meu cartão para processamento 100% em memória RAM (`Zero-Disk`), **para** importar todos os lançamentos sem que meu arquivo fique salvo em disco. | RN06, ADR-001, ADR-006 | 13 | P0 (Crítica) |
| **US-07** | Mobile NFC-e Offline | **Como** Usuário Mobile, **quero** escanear o QR Code de cupons fiscais NFC-e mesmo sem internet (modo offline-first), **para** que sejam sincronizados automaticamente quando houver conexão. | ADR-001, ADR-003, ADR-004 | 8 | P1 (Alta) |
| **US-08** | SEFAZ Scraper | **Como** Plataforma de Ingestão, **quero** extrair de forma resiliente os itens e CNPJ da NFC-e nos portais SEFAZ estaduais com Circuit Breaker e Retries, **para** enriquecer os gastos mesmo quando a SEFAZ oscilar. | ADR-004, ADR-005 | 8 | P1 (Alta) |
| **US-09** | IA Categorizer 3-Tier | **Como** Titular da Conta, **quero** que minhas transações sejam classificadas automaticamente na Taxonomia Oficial de 2 Níveis pelo pipeline de 3 camadas (Regras $\rightarrow$ ONNX Local $\rightarrow$ LLM), **para** não categorizar gastos manualmente. | Taxonomia 2 Níveis, ADR-001, ADR-004 | 13 | P1 (Alta) |
| **US-10** | Motor de Conciliação | **Como** Titular da Conta, **quero** que cupons NFC-e, faturas PDF e lançamentos do extrato referentes à mesma compra sejam conciliados sem duplicar meu saldo contábil, **para** manter minha contabilidade íntegra. | RN04, ADR-005 | 13 | P0 (Crítica) |
| **US-11** | Web Portal & Dashboards | **Como** Titular da Conta, **quero** visualizar no Portal Web o comparativo de Regime de Competência vs. Regime de Caixa, evolução do orçamento e fila de conciliação assistida, **para** tomar decisões financeiras claras. | RN01, RN02, RN04 | 8 | P2 (Média) |
| **US-12** | Painel SaaS Admin | **Como** Administrador da Plataforma (`PLATFORM_ADMIN`), **quero** visualizar todos os tenants (famílias/contas), gerenciar planos (`FREE`, `INDIVIDUAL_PRO`, `FAMILY_PLUS`), status de assinatura (`TRIAL`, `ACTIVE`, `PAST_DUE`, `SUSPENDED`), quotas de ingestão/IA e métricas globais de uso sem expor dados financeiros privados (respeitando PostgreSQL RLS), **para** administrar a plataforma com governança e privacidade. | RN05, ADR-006 | 8 | P1 (Alta) |
| **US-13** | Perfil, Família & LGPD | **Como** Titular (`OWNER`) ou Membro (`MEMBER`), **quero** gerenciar meu perfil, convidar/remover membros familiares com papéis (`OWNER`, `MEMBER`, `VIEWER`), configurar metas/tetos por categoria, gerenciar chaves/senhas de cartões cifradas via KMS, exportar meus dados (LGPD) e solicitar exclusão criptográfica (*Crypto-Shredding*), **para** ter controle total sobre minha família e meus dados. | RN05, ADR-006 | 8 | P1 (Alta) |
| **US-14** | Design System & UX | **Como** Usuário da Plataforma, **quero** navegar por uma interface refinada no padrão Apple/Adobe Craft com paleta "Organic Financial Pulse" (`#8CBA51`, `#DEFF8B`, `#FBCEB5`, `#FF5D6C`), layout responsivo *fluid full-width* e jornadas guiadas para cada Caso de Uso (`UC-01` a `UC-08`), **para** gerenciar minhas finanças com prazer estético e clareza cognitiva. | Design System, WCAG AAA | 8 | P1 (Alta) |
| **US-15** | FinOps Manager Lambda | **Como** Engenheiro SRE/FinOps, **quero** estacionar automaticamente as tarefas computacionais e o RDS PostgreSQL às 20h30 BRT e religá-los às 06h00 BRT via AWS Lambda + EventBridge Scheduler (`pfm-finops-manager-infra`), **para** reduzir custos ociosos noturnos em `us-east-2`. | FinOps MVP, ADR-008 | 5 | P1 (Alta) |

---

## 3. Especificações Executáveis BDD (Cenários Gherkin)

### Feature 01: Desdobramento de Parcelas, Competência vs. Caixa e Resíduo (US-02, US-03, US-05)

```gherkin
# language: pt
Funcionalidade: Escrituração de Compra Parcelada no Cartão (Competência vs. Caixa e Resíduo RN06)
  Como um Titular da Conta PFM Core Banking
  Quero registrar compras parceladas no cartão de crédito
  Para que meu limite total seja sensibilizado integralmente, meu orçamento mensal reflita apenas a competência da parcela e o resíduo de centavos seja alocado na 1ª parcela

  Contexto:
    Dado que o tenant autenticado possui o ID "01933000-0000-7000-8000-000000000001"
    E possui um cartão de crédito ativo com Limite Total de R$ 5.000,00 e Limite Disponível de R$ 5.000,00
    E possui um orçamento mensal na categoria "LAZER :: VIAGENS_HOSPEDAGEM" de R$ 500,00 para a competência "2026-11"

  Cenário: Compra de R$ 100,00 em 3 parcelas sem juros com alocação de resíduo na 1ª parcela (RN01, RN02, RN06)
    Quando o titular registra uma compra no cartão de crédito no valor total de R$ 100,00 em 3 parcelas na data "2026-11-15" na categoria "LAZER :: VIAGENS_HOSPEDAGEM"
    Então o sistema deve criar 3 parcelas vinculadas com precisão NUMERIC(19,4):
      | Parcela | Competência | Valor da Parcela | Status Inicial |
      | 1/3     | 2026-11     | R$ 33,34         | OPEN_STATEMENT |
      | 2/3     | 2026-12     | R$ 33,33         | FUTURE_INSTALL |
      | 3/3     | 2027-01     | R$ 33,33         | FUTURE_INSTALL |
    E a soma exata das 3 parcelas deve ser R$ 100,00
    E o Limite Disponível do cartão deve ser reduzido imediatamente em R$ 100,00 passando para R$ 4.900,00
    E o consumo do orçamento de "LAZER :: VIAGENS_HOSPEDAGEM" na competência "2026-11" deve ser de apenas R$ 33,34
    E o Regime de Caixa de "2026-11" não deve registrar saída de conta corrente até a data de pagamento efetivo da fatura
```

---

### Feature 02: Tratamento Contábil de Estornos em Fatura Fechada (US-04 / RN03)

```gherkin
# language: pt
Funcionalidade: Processamento de Estorno em Fatura Posterior sem Exclusão de Histórico (RN03)
  Como um Titular do Cartão
  Quero que estornos recebidos após o fechamento da fatura ajustem meu saldo devedor e mantenham vínculo com a compra original
  Para evitar distorção artificial de receitas e preservar a trilha de auditoria

  Cenário: Estorno total recebido na fatura seguinte após fechamento da fatura original
    Dado que o titular realizou uma compra de R$ 250,00 em "LAZER :: VESTUARIO_CALCADOS" na competência "2026-10" com ID "tx-orig-991"
    E a fatura da competência "2026-10" encontra-se no status "CLOSED_AND_PAID"
    Quando a operadora envia um evento de estorno de R$ 250,00 na data "2026-11-12" referenciando a compra "tx-orig-991"
    Então o lançamento original "tx-orig-991" deve permanecer inalterado no banco de dados (Append-Only)
    E um novo lançamento do tipo "REFUND_CREDIT" no valor de R$ -250,00 deve ser criado vinculado a "tx-orig-991"
    E o lançamento de estorno deve ser classificado em "LAZER :: VESTUARIO_CALCADOS" (e nunca como salário/renda)
    E o saldo a pagar da fatura aberta de "2026-11" deve ser reduzido em R$ 250,00
    E o Limite Disponível do cartão deve ser recomposto em R$ 250,00
```

---

### Feature 03: Ingestão de Fatura PDF em RAM e Conciliação com NFC-e sem Duplicidade (US-06, US-07, US-10)

```gherkin
# language: pt
Funcionalidade: Ingestão PDF Zero-Disk e Conciliação Automática com Cupom NFC-e (RN04, ADR-006)
  Como um Titular da Conta
  Quero que um gasto capturado via QR Code NFC-e seja conciliado automaticamente quando a fatura PDF for importada
  Para que eu tenha os itens detalhados da nota fiscal sem duplicar a despesa no meu orçamento

  Cenário: Conciliação automática de alta confiança entre NFC-e previamente escaneada e linha de Fatura PDF
    Dado que o titular escaneou offline um QR Code NFC-e no "SUPERMERCADO VERDE LTDA" (CNPJ "12.345.678/0001-90") em "2026-11-10T14:22:00" no valor de R$ 184,90
    E o cupom NFC-e gerou um lançamento provisório "tx-nfce-101" na categoria "ALIMENTACAO :: SUPERMERCADO_MERCEARIA" contendo 14 itens fiscais
    Quando o titular faz upload da fatura PDF do cartão contendo a linha "10/11 SUPERMERCADO VERDE R$ 184,90"
    Então o serviço "pfm-ingestion-pdf-service" deve processar o stream inteiramente em memória RAM sem criar arquivos em disco
    E o serviço "pfm-reconcile-service" deve identificar o match com score >= 0.90 com o lançamento "tx-nfce-101"
    E o status do lançamento "tx-nfce-101" deve mudar para "CONCILED" vinculado à fatura do cartão
    E nenhum segundo lançamento de R$ 184,90 deve ser debitado do orçamento de "ALIMENTACAO :: SUPERMERCADO_MERCEARIA"
```

---

### Feature 04: Isolamento Multitenant PostgreSQL RLS e Pipeline IA 3 Camadas (US-01, US-09)

```gherkin
# language: pt
Funcionalidade: Isolamento Zero-Trust via RLS (RN05) e Degradação Graciosa na Categorização IA (ADR-004)
  Como Engenheiro de Confiabilidade e Segurança
  Quero garantir que um tenant jamais acesse registros de outro tenant e que falhas no provedor LLM não interrompam o registro contábil

  Cenário: Bloqueio de leitura cross-tenant pelo PostgreSQL Row-Level Security (RN05 / ADR-006)
    Dado que o Tenant "A" ("01933000-0000-7000-8000-00000000000A") possui 50 transações gravadas na tabela "ledger_entries"
    E o Tenant "B" ("01933000-0000-7000-8000-00000000000B") autentica-se com um JWT válido no API Gateway
    Quando uma consulta SQL sem cláusula WHERE explícita é executada na sessão do Tenant "B"
    Então a política "FORCE ROW LEVEL SECURITY" do PostgreSQL deve filtrar estritamente por "current_setting('app.current_tenant_id')"
    E nenhum registro pertencente ao Tenant "A" deve ser retornado

  Cenário: Fallback gracioso quando a Camada 3 (Cloud LLM) sofre timeout para um estabelecimento desconhecido
    Dado uma transação com descrição atípica "PG *X9Z KIOSK 441" que não obteve match na Camada 1 (Regras/Cache)
    E cujo modelo local ONNX na Camada 2 retornou confiança de 0.48 (abaixo do limiar mínimo de 0.82)
    E o provedor externo de Cloud LLM (Camada 3) está indisponível com Circuit Breaker no estado "OPEN"
    Quando o "pfm-ledger-service" solicita a categorização ao "pfm-ai-categorizer-service"
    Então o categorizador deve responder em menos de 50ms com a categoria de fallback "OUTROS :: NAO_CATEGORIZADO" e flag "requires_review = true"
    E a transação deve ser persistida com sucesso no Ledger sem retornar erro 5xx ao usuário
```

---

### Feature 05: Painel SaaS Admin e Gestão de Quotas/Planos Multitenant (US-12 / RN05 / ADR-006)

```gherkin
# language: pt
Funcionalidade: Painel SaaS Admin com Visibilidade Global e Proteção Estrita Zero-Trust RLS (US-12)
  Como um Administrador da Plataforma (PLATFORM_ADMIN)
  Quero visualizar métricas agregadas de todos os tenants, gerenciar planos e status de assinatura
  Para administrar a operação SaaS com governança comercial sem jamais violar a privacidade e o sigilo bancário dos clientes

  Contexto:
    Dado que o usuário autenticado possui o papel "PLATFORM_ADMIN"
    E existem 150 tenants cadastrados na plataforma distribuídos entre planos "FREE", "INDIVIDUAL_PRO" e "FAMILY_PLUS"

  Cenário: Visualização de métricas agregadas de faturamento e consumo sem exposição de lançamentos privados
    Quando o administrador acessa o endpoint "/api/v1/admin/tenants/metrics"
    Então o sistema deve retornar o total consolidado de tenants por status:
      | Status    | Quantidade |
      | ACTIVE    | 138        |
      | TRIAL     | 8          |
      | PAST_DUE  | 3          |
      | SUSPENDED | 1          |
    E o painel deve exibir o volume global de transações ingeridas e o consumo de tokens de IA
    E nenhuma linha de lançamento contábil ("ledger_entries") ou fatura privada ("card_statements") de nenhum tenant deve ser retornada na resposta

  Cenário: Transição de assinatura para PAST_DUE e SUSPENDED com bloqueio de ingestão e preservação de leitura
    Dado que o tenant "01933000-0000-7000-8000-00000000000C" no plano "FAMILY_PLUS" teve falha de cobrança há 6 dias
    Quando o job de conciliação de faturamento executa
    Então o status da assinatura do tenant deve ser atualizado para "SUSPENDED"
    E tentativas de upload de nova fatura PDF pelo titular devem retornar erro HTTP 402 Payment Required com a mensagem "Assinatura suspensa. Por favor, regularize seu pagamento para continuar importando faturas."
    E a consulta ao extrato histórico de lançamentos existentes deve continuar liberada em modo leitura (Read-Only)
```

---

### Feature 06: Central de Perfil, Gestão Familiar e Crypto-Shredding LGPD (US-13 / RN05 / ADR-006)

```gherkin
# language: pt
Funcionalidade: Gestão de Membros Familiares, Funções RBAC e Exclusão Criptográfica Crypto-Shredding (US-13)
  Como um Titular da Conta (OWNER)
  Quero convidar membros familiares com permissões segregadas e exercer meu direito de esquecimento LGPD via Crypto-Shredding
  Para governar o orçamento colaborativo da minha família e manter controle soberano sobre meus dados pessoais

  Cenário: Convite de membro familiar com papel MEMBER e teto de gastos individual
    Dado que o titular "OWNER" do tenant "01933000-0000-7000-8000-00000000000D" possui plano "FAMILY_PLUS"
    Quando o titular envia um convite para o e-mail "conjuge@familia.com" com papel "MEMBER" e teto mensal de R$ 2.000,00
    Então um token de convite com validade de 48 horas deve ser gerado
    E quando o membro aceita o convite, ele deve visualizar apenas seu próprio consumo e lançamentos autorizados
    E o membro "MEMBER" não deve ter permissão para alterar os dados de faturamento da assinatura ou remover outros membros

  Cenário: Exclusão definitiva de conta via Crypto-Shredding (Destruição Irreversível de Chave KMS)
    Dado que o titular da conta solicita o encerramento definitivo e exclusão dos dados da família conforme o Artigo 18 da LGPD
    E confirma a solicitação digitando "EXCLUIR_DEFINITIVAMENTE_MINHA_CONTA" com autenticação em dois fatores (MFA)
    Quando o comando de Crypto-Shredding é processado pelo serviço de segurança
    Então o adaptador KMS deve revogar e destruir permanentemente a Data Encryption Key (DEK) vinculada ao "tenant_id"
    E todos os registros nas tabelas do PostgreSQL devem ter status alterado para "CRYPTO_SHREDDED" com metadados PII zerados
    E qualquer tentativa futura de decifrar os dados históricos nos backups resultará em falha criptográfica irrecuperável
```

---

### Feature 07: Experiência Visual, Responsividade Full-Width e Paleta Organic Pulse (US-14 / Design System)

```gherkin
# language: pt
Funcionalidade: Interface Widescreen Fluida, Design System Apple Craft e Paleta Organic Financial Pulse (US-14)
  Como um Usuário da Plataforma PFM
  Quero interagir com um dashboard financeiro que responda fluidamente em qualquer resolução e utilize cores funcionais
  Para tomar decisões financeiras sem cansaço visual e com feedback instantâneo sobre minha saúde financeira

  Cenário: Aplicação funcional da paleta "Organic Financial Pulse" e alinhamento numérico bancário
    Dado que o usuário acessa o dashboard executivo no portal Web
    Quando o saldo da conta e as metas do mês estão em conformidade com o planejado (consumo < 80%)
    Então o componente de pulso financeiro deve exibir a cor primária "#8CBA51" (Organic Olive) com acentos luminosos em "#DEFF8B" (Vibrant Lime)
    E quando uma categoria atinge 85% do teto, a badge de status deve transicionar suavemente para "#FBCEB5" (Warm Peach)
    E quando uma categoria atinge 102% do teto, o indicador deve alertar em "#FF5D6C" (Coral Red)
    E todas as tabelas contábeis devem renderizar valores com a família tipográfica "SF Mono" / "JetBrains Mono" alinhados estritamente à direita

  Cenário: Layout responsivo fluid full-width sem rolagem horizontal em telas ultrawide
    Dado que o usuário acessa a plataforma em um monitor Ultrawide (2560x1080 ou 3440x1440)
    Quando a tela é renderizada
    Então os painéis de "Regime de Competência", "Regime de Caixa" e "Fila de Conciliação" devem ocupar a largura total útil da viewport
    E nenhuma barra de rolagem horizontal indesejada deve ser gerada no navegador
    E a barra de navegação lateral deve manter estado colapsável com transições suaves a 60 FPS
```

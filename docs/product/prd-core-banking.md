# PRD Core Banking — Regras de Negócio (RN01–RN06) & Taxonomia Oficial

Este documento estabelece o **Product Requirements Document (PRD)** de engenharia de domínio da plataforma **PFM Core Banking**, especificando as invariantes contábeis obrigatórias (**RN01 a RN06**) e a **Taxonomia Oficial de 2 Níveis**.

---

## 1. Regras de Negócio Fundamentais (RN01 a RN06)

### RN01 — Segregação Estrita entre Regime de Competência e Regime de Caixa

!!! important "Regra de Ouro Contábil (RN01)"
    Toda transação financeira possui dupla dimensão temporal obrigatória: **Data de Competência (`competence_date`)** e **Data de Caixa (`cash_date`)**. É proibido misturar ambos os regimes na apuração de orçamentos ou fluxo de caixa.

1. **Regime de Competência (*Accrual Basis*)**:
   - Reconhece o fato gerador no momento da compra/consumo (ou no mês de referência de cada parcela $i/N$).
   - **Consumo de Orçamento Mensal**: Todo orçamento de categoria (`pfm-budget-service`) é calculado **exclusivamente pelo Regime de Competência**.
   - **Compras Parceladas no Cartão**: Uma compra de $\text{R\$ } 1.200,00$ em $12\times$ sem juros realizada em 10/Novembro aloca $\text{R\$ } 100,00$ na competência de Novembro e projeta 11 parcelas futuras de $\text{R\$ } 100,00$ nas competências subsequentes.
2. **Regime de Caixa (*Cash Basis*)**:
   - Reconhece a saída ou entrada efetiva de liquidez na conta corrente/carteira no dia da liquidação financeira.
   - **Pagamento da Fatura do Cartão**: A liquidação da fatura em 10/Dezembro representa um evento de **Caixa** (transferência entre Conta Corrente $\rightarrow$ Passivo Cartão de Crédito), **jamais** devendo ser contabilizada novamente como despesa de orçamento para evitar dupla contagem (*double counting*).

---

### RN02 — Limite de Cartão de Crédito $\neq$ Orçamento Financeiro

!!! warning "Invariante de Produto (RN02)"
    O **Limite Total/Disponível do Cartão de Crédito** é uma linha de risco concedida pelo emissor bancário (gerida pelo `pfm-cards-service`), enquanto o **Orçamento (Budget)** é o teto de gastos planejado pelo usuário por categoria/competência (gerido pelo `pfm-budget-service`).

| Dimensão | Limite do Cartão (`pfm-cards-service`) | Orçamento Mensal (`pfm-budget-service`) |
| :--- | :--- | :--- |
| **Natureza Contábil** | Capacidade de endividamento rotativo/parcelado no emissor | Meta de alocação de renda mensal por categoria |
| **Impacto de Compra Parcelada ($\text{R\$ } 1.200$ em $12\times$)** | Consome **$\text{R\$ } 1.200,00$ imediatamente** do Limite Disponível Total | Consome apenas **$\text{R\$ } 100,00$** no orçamento da competência atual |
| **Recomposição** | Recomposto proporcionalmente conforme o pagamento efetivo de cada fatura (Caixa) | Renovado a cada novo ciclo mensal de competência (`YYYY-MM`) |
| **Alertas Associados** | Alerta de uso de limite de crédito ($> 80\%$ do limite do cartão) | Alerta de estouro de orçamento da categoria ($80\%$ Warning / $100\%$ Critical) |

---

### RN03 — Tratamento de Estornos, Cancelamentos e Chargebacks

Estornos (*refunds* / *chargebacks*) jamais apagam fisicamente (`DELETE`) a transação original. O histórico contábil é **imutável (Append-Only Ledger)**:

1. **Vínculo Obrigatório**: Todo estorno gera um lançamento de ajuste reverso (`entry_type = REFUND_CREDIT`) vinculado ao `original_transaction_id` quando identificável, ou vinculado à categoria original da compra.
2. **Estorno em Fatura Aberta (Mesma Competência)**:
   - Abate imediatamente o consumo do orçamento na competência vigente e recompõe o limite disponível do cartão.
3. **Estorno em Fatura Fechada (Competência Posterior)**:
   - **Visão de Competência Histórica**: Preserva a rastreabilidade vinculando o crédito redutor à categoria original, evitando distorcer artificialmente a renda do mês seguinte como se o estorno fosse "salário/receita".
   - **Visão de Fatura/Caixa**: Gera crédito redutor no saldo a pagar da fatura aberta atual (ou saldo credor para a fatura seguinte caso o estorno supere os gastos do ciclo).
4. **Estorno de Compra Parcelada**:
   - Caso o emissor lance o crédito integral antecipado ou cancele as parcelas vincendas, o `pfm-cards-service` reconcilia as parcelas futuras pendentes (`CANCELLED_BY_REFUND`) e recompõe o limite total do cartão.

---

### RN04 — Conciliação Multiconteúdo sem Duplicidade Contábil

Um único evento econômico real (ex.: jantar em restaurante pago com cartão de crédito) pode ingressar na plataforma por **até 3 canais distintos**:
1. Captura do QR Code da **NFC-e** no momento da compra;
2. Lançamento manual ou notificação no app;
3. Importação da **Fatura PDF** ao final do ciclo mensal.

**Regras do Motor de Conciliação (`pfm-reconcile-service`)**:

- **Proibição de Duplicidade**: Quando a NFC-e e a linha da fatura PDF correspondem à mesma compra, o sistema funde os metadados em um **único lançamento contábil ativo (`CONCILED`)**, preservando o valor financeiro da fatura/extrato e anexando o detalhamento de itens fiscais da NFC-e.
- **Critérios de Matching Automático (Score $\ge 0.90$)**:
  - Igualdade de `tenant_id`;
  - Diferença absoluta de valor $|\Delta V| \le \text{R\$ } 0,05$ (tolerância para arredondamento de bomba de combustível/balança);
  - Diferença temporal $|\Delta t| \le 48\text{ horas}$ entre a emissão da NFC-e e a data da transação na fatura;
  - Similaridade de CNPJ raiz ou nome fantasia (*Jaro-Winkler / Trigram similarity* $\ge 0.75$).
- **Conciliação Assistida**: Quando $0.60 \le \text{Score} < 0.90$, o registro entra na fila de revisão do usuário com sugestão em 1 clique no Portal Web / App Mobile.

---

### RN05 — Multitenancy Estrito & Isolamento Zero-Trust

1. **Identidade Imutável do Tenant**: O `tenant_id` (UUID v4/v7) nunca é aceito a partir do corpo da requisição JSON enviada pelo cliente; ele é extraído exclusivamente da assinatura criptográfica validada do token JWT (`sub`/`tenant_id` claim) no API Gateway e propagado via mTLS metadata.
2. **Isolamento no Banco de Dados (PostgreSQL RLS)**:
   - Todas as tabelas de todos os schemas possuem `tenant_id UUID NOT NULL` e política `ROW LEVEL SECURITY` forçada (`FORCE ROW LEVEL SECURITY`).
   - Qualquer query executada sem `app.current_tenant_id` definido na sessão transacional retorna zero linhas ou lança exceção de segurança.
3. **Isolamento no Cache e Mensageria**:
   - Chaves Redis seguem o prefixo obrigatório `tenant:{tenant_id}:{domain}:{key}`.
   - Tópicos Kafka utilizam `tenant_id` como chave de partição e cabeçalho autenticado, e chaves criptográficas DEK são segregadas por tenant via Envelope Encryption (KMS).

---

### RN06 — Precisão Decimal Bancária e Distribuição de Resíduo em Parcelas

!!! danger "Proibição Absoluta de Ponto Flutuante (IEEE 754)"
    É terminantemente proibido o uso de `float`, `double`, `FLOAT4`, `FLOAT8` ou `Number` (JavaScript sem biblioteca decimal) para representar valores monetários, taxas ou percentuais de rateio em qualquer camada da plataforma.

1. **Representação Persistente e em Memória**:
   - **PostgreSQL**: Tipo `NUMERIC(19, 4)` para valores monetários e `NUMERIC(19, 2)` para exibição final em moeda fiduciária (`BRL`).
   - **Java 25**: `java.math.BigDecimal` com escala explícita e `RoundingMode.HALF_EVEN` (Arredondamento Bancário ABNT NBR 5891).
   - **Golang**: Inteiros em centavos/ décimos de milésimo (`int64` scaled) ou `shopspring/decimal`.
   - **Python**: `decimal.Decimal` com contexto `ROUND_HALF_EVEN`.
2. **Fórmula de Desdobramento de Parcelas e Resíduo de Centavos**:
   Seja $V_{\text{total}}$ o valor total de uma compra parcelada em $N$ parcelas ($N \ge 2$):
   - Valor base da parcela:
     $$V_{\text{base}} = \text{floor\_cents}\left(\frac{V_{\text{total}}}{N}\right)$$
   - Resíduo aritmético de centavos:
     $$R = V_{\text{total}} - (V_{\text{base}} \times N)$$
   - **Regra de Alocação do Resíduo**: O resíduo $R$ é integralmente alocado na **1ª parcela ($i = 1$)**, garantindo que a soma exata das parcelas seja sempre idêntica ao total da compra:
     $$V_1 = V_{\text{base}} + R, \quad V_i = V_{\text{base}} \;\;\forall i \in \{2, \dots, N\} \implies \sum_{i=1}^{N} V_i = V_{\text{total}}$$
   - *Exemplo Prático*: Compra de $\text{R\$ } 100,00$ em $3\times$:
     - $1\text{ª Parcela} = \text{R\$ } 33,34$
     - $2\text{ª Parcela} = \text{R\$ } 33,33$
     - $3\text{ª Parcela} = \text{R\$ } 33,33$
     - $\text{Soma} = \text{R\$ } 100,00$ (Zero perda ou criação de centavos).

---

## 2. Taxonomia Oficial de 2 Níveis (Categorias & Subcategorias)

Toda movimentação financeira na plataforma PFM Core Banking é classificada obrigatoriamente em uma estrutura hierárquica estrita de **2 Níveis**: **Categoria Principal (Nível 1)** e **Subcategoria (Nível 2)**. Não são permitidas transações órfãs (sem Nível 2) nem árvores de profundidade arbitrária que degradem a agregação analítica.

| Código N1 | Categoria Principal (Nível 1) | Natureza | Subcategorias Oficiais (Nível 2) |
| :--- | :--- | :---: | :--- |
| **`MORADIA`** | Moradia & Utilidades | Despesa Essencial | `ALUGUEL_CONDOMINIO`, `FINANCIAMENTO_IMOBILIARIO`, `ENERGIA_ELETRICA`, `AGUA_SANEAMENTO`, `GAS_ENCANADO`, `INTERNET_TV_TELEFONIA`, `MANUTENCAO_REPAROS`, `IPTU_TAXAS_MUNICIPAIS` |
| **`ALIMENTACAO`** | Alimentação & Supermercado | Despesa Essencial / Variável | `SUPERMERCADO_MERCEARIA`, `PADARIA_FEIRA_ACOUGUE`, `RESTAURANTES_GASTRONOMIA`, `DELIVERY_APLICATIVOS`, `CAFE_LANCHES` |
| **`TRANSPORTE`** | Transporte & Mobilidade | Despesa Essencial / Variável | `COMBUSTIVEL_ETANOL_GASOLINA`, `APLICATIVOS_MOBILIDADE`, `TRANSPORTE_PUBLICO`, `ESTACIONAMENTO_PEDAGIO`, `MANUTENCAO_VEICULAR`, `SEGURO_IPVA_LICENCIAMENTO` |
| **`SAUDE`** | Saúde & Bem-Estar | Despesa Essencial | `PLANO_SAUDE`, `FARMACIA_MEDICAMENTOS`, `CONSULTAS_EXAMES`, `ODONTOLOGIA`, `TERAPIA_PSICOLOGIA`, `ACADEMIA_ATIVIDADE_FISICA` |
| **`EDUCACAO`** | Educação & Desenvolvimento | Investimento Pessoal | `MENSALIDADE_ESCOLAR_FACULDADE`, `CURSOS_CERTIFICACOES`, `LIVROS_MATERIAL_DIDATICO`, `IDIOMAS` |
| **`LAZER`** | Lazer, Cultura & Estilo de Vida | Despesa Variável / Estilo de Vida | `STREAMING_ASSINATURAS_DIGITAIS`, `VIAGENS_HOSPEDAGEM`, `PASSAGENS_AEREAS`, `CINEMA_SHOWS_EVENTOS`, `HOBBIES_JOGOS`, `VESTUARIO_CALCADOS`, `CUIDADOS_PESSOAIS_BELEZA`, `PETS_VETERINARIO` |
| **`FINANCEIRO`** | Serviços Financeiros & Impostos | Despesa Financeira | `IOF_IMPOSTOS_FINANCEIROS`, `ANUIDADE_TARIFAS_BANCARIAS`, `JUROS_ENCARGOS_ROTATIVO`, `SEGURO_VIDA_PATRIMONIAL`, `IRPF_TRIBUTOS_FEDERAIS` |
| **`RECEITAS`** | Receitas & Entradas | Entrada de Caixa / Competência | `SALARIO_PRO_LABORE`, `BONUS_PLR_13_SALARIO`, `RENDIMENTOS_DIVIDENDOS`, `FREELANCE_PRESTACAO_SERVICOS`, `REEMBOLSO_CORPORATIVO`, `ESTORNO_CREDITO` |
| **`PATRIMONIO`** | Investimentos & Movimentações Neutras | Neutro (Patrimonial / Caixa) | `APORTE_RENDA_FIXA`, `APORTE_RENDA_VARIAVEL`, `RESERVA_EMERGENCIA`, `PAGAMENTO_FATURA_CARTAO`, `TRANSFERENCIA_MESMA_TITULARIDADE` |
| **`OUTROS`** | Outros & Pendências de Classificação | Transitório / Diversos | `DOACOES_PRESENTES`, `DESPESAS_EVENTUAIS`, `NAO_CATEGORIZADO` |

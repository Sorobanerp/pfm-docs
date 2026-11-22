# 2.1. PRD Core Banking V3 -- Regras de Negocio (RN01 a RN06) e Taxonomia Oficial

<span class="badge-green">Artefato 01 - PRD Core Banking V3</span>
<span class="badge-glow">100% em Real Brasileiro (R$ / BRL)</span>
<span class="badge-peach">Meta &lt; 5% em Nao Categorizado</span>

Este documento estabelece o **Product Requirements Document (PRD V3)** da plataforma **PFM Core Banking**, especificando as 6 regras de negocio contabeis imutaveis (**RN01 a RN06**), a **Taxonomia Oficial de 2 Niveis** e a meta de qualidade de classificacao (`< 5%` em `OUTROS :: NAO_CATEGORIZADO`).

---

## 1. Regras de Negocio Fundamentais (RN01 a RN06)

### RN01 -- Segregacao Estrita entre Regime de Competencia e Regime de Caixa

!!! important "Regra de Ouro Contabil (RN01)"
    Toda transacao financeira possui dupla dimensao temporal obrigatoria: **Data de Competencia (`competence_date`)** e **Data de Caixa (`cash_date`)**. E proibido misturar ambos os regimes na apuracao de orcamentos ou fluxo de caixa.

1. **Regime de Competencia (*Accrual Basis*):**
   - Reconhece o fato gerador no momento da compra/consumo (ou no mes de referencia de cada parcela `i/N`).
   - **Consumo de Orcamento Mensal:** Todo orcamento de categoria e calculado **exclusivamente pelo Regime de Competencia**.
   - **Compras Parceladas no Cartao:** Uma compra de `R$ 1.200,00` em `12x` sem juros realizada em 10/Novembro aloca `R$ 100,00` na competencia de Novembro e projeta 11 parcelas futuras de `R$ 100,00` nas competencias subsequentes.
2. **Regime de Caixa (*Cash Basis*):**
   - Reconhece a saida ou entrada efetiva de liquidez na conta corrente no dia da liquidacao financeira.
   - **Pagamento da Fatura do Cartao:** A liquidacao da fatura de `R$ 6.890,45` em 10/Dezembro representa um evento neutro de **Caixa** (transferencia entre Conta Corrente -> Passivo Cartao de Credito), **jamais** devendo ser contabilizada novamente como despesa de orcamento para evitar dupla contagem.

---

### RN02 -- Limite de Cartao de Credito != Orcamento Financeiro

!!! warning "Invariante de Produto (RN02)"
    O **Limite Total/Disponivel do Cartao de Credito** e uma linha de risco concedida pelo emissor bancario, enquanto o **Orcamento (Budget)** e o teto de gastos planejado pelo usuario por categoria/competencia.

| Dimensao | Limite do Cartao | Orcamento Mensal por Categoria |
| :--- | :--- | :--- |
| **Natureza Contabil** | Capacidade de compra rotativa/parcelada no emissor | Meta de alocacao de renda mensal por categoria |
| **Impacto de Compra Parcelada (`R$ 1.200,00` em `12x`)** | Consome **`R$ 1.200,00` imediatamente** do Limite Disponivel Total | Consome apenas **`R$ 100,00`** no orcamento da competencia atual |
| **Recomposicao** | Recomposto conforme o pagamento efetivo de cada fatura (Caixa) | Renovado a cada novo ciclo mensal de competencia (`YYYY-MM`) |
| **Alertas Associados** | Alerta de uso de limite de credito (`> 80%` do limite do cartao) | Alerta de orcamento da categoria (`80%` Atencao / `100%` Critico) |

---

### RN03 -- Tratamento de Estornos, Cancelamentos e Chargebacks

Estornos (*refunds* / *chargebacks*) jamais apagam fisicamente (`DELETE`) a transacao original. O livro-razao contabil e **imutavel (Append-Only Ledger)**:

1. **Vinculo Obrigatorio:** Todo estorno gera um lancamento reverso (`entry_type = REFUND_CREDIT`) vinculado ao `original_transaction_id` ou diretamente a **categoria original da compra**.
2. **Estorno em Fatura Aberta (Mesma Competencia):** Abate imediatamente o consumo do orcamento na competencia vigente e recompoe o limite disponivel do cartao em `R$`.
3. **Estorno em Fatura Fechada (Competencia Posterior):** Vincula o credito redutor (ex.: `R$ -250,00`) a categoria original da despesa (ex.: `LAZER :: VESTUARIO_CALCADOS`), evitando distorcer a renda do mes seguinte como se o estorno fosse salario/receita.
4. **Estorno de Compra Parcelada:** Reconcilia as parcelas futuras pendentes (`CANCELLED_BY_REFUND`) e recompoe o limite total do cartao.

---

### RN04 -- Conciliacao Multiconteudo e Checksum Matematico de Fatura PDF

1. **Checksum Obrigatorio na Importacao de Faturas PDF:**
   - Toda fatura PDF importada valida matematicamente se a soma exata dos lancamentos extraidos (`sum(items)`) equivale ao total declarado no cabecalho da fatura (`declared_total`). Caso `diff != R$ 0,00`, a operacao e rejeitada com `409 Conflict` indicando o valor exato da divergencia.
2. **Conciliacao sem Duplicidade (NFC-e + Fatura PDF):**
   - Quando um cupom fiscal NFC-e (ex.: `R$ 184,90`) e a linha da fatura PDF correspondem a mesma compra (diferenca de valor `<= R$ 0,05`, janela `<= 48 horas` e similaridade de estabelecimento `>= 0.75`), o sistema funde os metadados em um **unico lancamento contabil (`CONCILED`)**, anexando os itens da nota fiscal sem duplicar o debito no orcamento.

---

### RN05 -- Multitenancy Estrito & Isolamento Zero-Trust

1. **Identidade do Tenant:** O `tenant_id` (UUID) e extraido do contexto autenticado e propagado ate a sessao transacional do banco de dados.
2. **Isolamento no Banco de Dados (PostgreSQL 16 RLS):** Todas as tabelas possuem `tenant_id UUID NOT NULL` com `ENABLE ROW LEVEL SECURITY` e `FORCE ROW LEVEL SECURITY`. Qualquer query sem `app.current_tenant_id` definido retorna zero linhas.

---

### RN06 -- Precisao Decimal Bancaria e Distribuicao de Residuo em Parcelas

!!! danger "Proibicao Absoluta de Ponto Flutuante (IEEE 754)"
    E terminantemente proibido o uso de `float`, `double`, `FLOAT4`, `FLOAT8` ou `Number` (IEEE 754) para representar valores monetarios em `R$` ou taxas percentuais.

1. **Representacao Exata:**
   - **PostgreSQL 16:** `NUMERIC(19, 4)` para armazenamento e calculo interno; `NUMERIC(19, 2)` para exibicao em `BRL (R$)`.
   - **Java 25:** `java.math.BigDecimal` com `RoundingMode.HALF_EVEN`.
   - **Golang:** `shopspring/decimal`.
   - **Python:** `decimal.Decimal` (`ROUND_HALF_EVEN`).
2. **Regra de Alocacao do Residuo na 1a Parcela:**
   - Em uma compra parcelada de valor total $V_{\text{total}}$ em $N$ parcelas:
     - $V_{\text{base}} = \text{floor\_cents}(V_{\text{total}} / N)$
     - $R = V_{\text{total}} - (V_{\text{base}} \times N)$
     - $V_1 = V_{\text{base}} + R$ e $V_i = V_{\text{base}}$ para $i \in \{2, \dots, N\}$.
   - *Exemplo Pratico:* Compra de `R$ 100,00` em `3x`:
     - 1a Parcela = `R$ 33,34` | 2a Parcela = `R$ 33,33` | 3a Parcela = `R$ 33,33` -> Soma exata = `R$ 100,00`.

---

## 2. Taxonomia Oficial de 2 Niveis e Meta `< 5%` em Outros

Toda movimentacao financeira e classificada em uma hierarquia estrita de **2 Niveis (`Categoria Nivel 1 :: Subcategoria Nivel 2`)**. O motor de IA em 3 camadas combinado ao aprendizado de regras do tenant garante que menos de **5%** do volume financeiro mensal permaneca em `OUTROS :: NAO_CATEGORIZADO`.

| Codigo N1 | Categoria Principal (Nivel 1) | Natureza | Subcategorias Oficiais (Nivel 2) |
| :--- | :--- | :---: | :--- |
| **`MORADIA`** | Moradia & Utilidades | Despesa Essencial | `ALUGUEL_CONDOMINIO`, `FINANCIAMENTO_IMOBILIARIO`, `ENERGIA_ELETRICA`, `AGUA_SANEAMENTO`, `GAS_ENCANADO`, `INTERNET_TV_TELEFONIA`, `MANUTENCAO_REPAROS`, `IPTU_TAXAS_MUNICIPAIS` |
| **`ALIMENTACAO`** | Alimentacao & Supermercado | Despesa Essencial / Variavel | `SUPERMERCADO_MERCEARIA`, `PADARIA_FEIRA_ACOUGUE`, `RESTAURANTES_GASTRONOMIA`, `DELIVERY_APLICATIVOS`, `CAFE_LANCHES` |
| **`TRANSPORTE`** | Transporte & Mobilidade | Despesa Essencial / Variavel | `COMBUSTIVEL_ETANOL_GASOLINA`, `APLICATIVOS_MOBILIDADE`, `TRANSPORTE_PUBLICO`, `ESTACIONAMENTO_PEDAGIO`, `MANUTENCAO_VEICULAR`, `SEGURO_IPVA_LICENCIAMENTO` |
| **`SAUDE`** | Saude & Bem-Estar | Despesa Essencial | `PLANO_SAUDE`, `FARMACIA_MEDICAMENTOS`, `CONSULTAS_EXAMES`, `ODONTOLOGIA`, `TERAPIA_PSICOLOGIA`, `ACADEMIA_ATIVIDADE_FISICA` |
| **`EDUCACAO`** | Educacao & Desenvolvimento | Investimento Pessoal | `MENSALIDADE_ESCOLAR_FACULDADE`, `CURSOS_CERTIFICACOES`, `LIVROS_MATERIAL_DIDATICO`, `IDIOMAS` |
| **`LAZER`** | Lazer, Cultura & Estilo de Vida | Despesa Variavel | `STREAMING_ASSINATURAS_DIGITAIS`, `VIAGENS_HOSPEDAGEM`, `PASSAGENS_AEREAS`, `CINEMA_SHOWS_EVENTOS`, `HOBBIES_JOGOS`, `VESTUARIO_CALCADOS`, `CUIDADOS_PESSOAIS_BELEZA`, `PETS_VETERINARIO` |
| **`FINANCEIRO`** | Servicos Financeiros & Impostos | Despesa Financeira | `IOF_IMPOSTOS_FINANCEIROS`, `ANUIDADE_TARIFAS_BANCARIAS`, `JUROS_ENCARGOS_ROTATIVO`, `SEGURO_VIDA_PATRIMONIAL`, `IRPF_TRIBUTOS_FEDERAIS` |
| **`RECEITAS`** | Receitas & Entradas | Entrada | `SALARIO_PRO_LABORE`, `BONUS_PLR_13_SALARIO`, `RENDIMENTOS_DIVIDENDOS`, `FREELANCE_PRESTACAO_SERVICOS`, `REEMBOLSO_CORPORATIVO`, `ESTORNO_CREDITO` |
| **`PATRIMONIO`** | Investimentos & Movimentacoes Neutras | Neutro (Caixa) | `APORTE_RENDA_FIXA`, `APORTE_RENDA_VARIAVEL`, `RESERVA_EMERGENCIA`, `PAGAMENTO_FATURA_CARTAO`, `TRANSFERENCIA_MESMA_TITULARIDADE` |
| **`OUTROS`** | Outros & Pendencias de Classificacao | Transitorio (Meta `< 5%`) | `DOACOES_PRESENTES`, `DESPESAS_EVENTUAIS`, `NAO_CATEGORIZADO` |

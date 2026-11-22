# 1. Visao de Negocio -- Proposta de Valor, Mercado e Modelo SaaS (BRL)

<span class="badge-green">Visao 01 - Negocio &amp; Estrategia</span>
<span class="badge-glow">Moeda Oficial: Real Brasileiro (R$ / BRL)</span>
<span class="badge-peach">Conformidade LGPD (Lei 13.709/2018)</span>

Este documento apresenta a tese executiva de negocio do **PFM Pulse** (ecossistema **Soroban**), detalhando o problema de mercado resolvido, a filosofia **"Big Numbers First"**, o modelo de monetizacao SaaS em Real Brasileiro (`R$`) e os diferenciais competitivos de governanca e eficiencia operacional.

---

## 1. O Problema: A Falencia das Planilhas e a Ilusao do Saldo em Conta

Profissionais de alta performance, executivos e familias brasileiras enfrentam tres dores cronicas na gestao financeira pessoal e patrimonial:

1. **Atriccao Operacional das Planilhas:** Manter planilhas manuais exige horas mensais de digitacao, falha na sincronizacao entre membros da familia e quebra diante de parcelamentos longos, estornos ou multiplos cartoes de credito.
2. **Confusao entre Regime de Competencia e Regime de Caixa:** Aplicativos comuns somam o pagamento da fatura do cartao com as compras do mes vigente, gerando dupla contagem ou ocultando o comprometimento real da renda futura com parcelas vincendas.
3. **Gastos Invisiveis ("Buraco Negro" da Categoria Outros):** Extratos bancarios exibem siglas truncadas (`IFD*`, `PAG*`, `MP*`), levando mais de 25% do orcamento familiar a cair em categorias genericas sem valor analitico.

---

## 2. A Tese do Produto: "Big Numbers First" (Clareza em 10 Segundos por Dia)

O **PFM Pulse** substitui o microgerenciamento de tabelas extensas por uma jornada executiva de **10 segundos por dia**, respondendo imediatamente as tres perguntas que governam a tomada de decisao financeira:

<div class="grid cards" markdown>

-   **1. Quanto tenho livre para gastar hoje, na semana e no mes?**

    ---

    Exibicao em destaque do **Fluxo de Caixa Livre Projetado** (ex.: `R$ 7.080,00` no mes / `R$ 1.652,00` na semana / `R$ 236,00` hoje), ja descontando despesas fixas liquidadas, faturas abertas e parcelas futuras contratadas.

-   **2. Meu ritmo de consumo vai fechar o mes dentro da meta?**

    ---

    Projecao preditiva de 30, 60 e 90 dias com alertas preventivos suaves quando qualquer categoria atinge `80%` do teto planejado (ex.: `R$ 2.000,00` consumidos de um teto de `R$ 2.500,00` em Supermercado).

-   **3. Para onde foi cada centavo da fatura e qual o impacto dos contratos?**

    ---

    Auditoria automatica de faturas PDF com validacao matematica de centavos, meta estrita de **`< 5%` em gastos nao categorizados** e simulador de amortizacao (SAC, Tabela Price e Consorcios) revelando a economia exata em `R$`.

</div>

---

## 3. Modelo de Receita SaaS e Planos Comerciais (100% em BRL)

A plataforma opera no modelo **Software as a Service (SaaS) Multi-Tenant** com tres faixas de assinatura precificadas em **Real Brasileiro (`R$`)**:

| Plano Comercial | Mensalidade (BRL) | Publico-Alvo | Quotas e Capacidades Incluidas |
| :--- | :---: | :--- | :--- |
| **`FREE`** | **R$ 0,00 / mes** | Entrada individual e validacao inicial | 1 titular, 1 cartao de credito, ate 3 uploads de faturas PDF/mes e categorizacao deterministica. |
| **`INDIVIDUAL_PRO`** | **R$ 29,90 / mes** | Profissionais, executivos e consultores | 1 titular, cartoes e contas ilimitados, categorizacao IA em 3 camadas, scanner NFC-e ilimitado, projecao 90 dias e simulador SAC/Price/Consorcio. |
| **`FAMILY_PLUS`** | **R$ 49,90 / mes** | Familias e gestao patrimonial conjunta | Ate 5 membros familiares (`OWNER`, `MEMBER`, `VIEWER`), tetos individuais em `R$`, cofre criptografado de senhas PDF de cartoes e exportacao fiscal completa. |

### Regras Comerciais do Ciclo de Assinatura
- **Experimentacao (`TRIAL`):** 14 dias gratuitos com recursos completos do plano `FAMILY_PLUS`.
- **Adimplencia (`ACTIVE`):** Renovacao mensal automatica via PIX ou Cartao de Credito.
- **Tolerancia (`PAST_DUE`):** 5 dias corridos de aviso amigavel sem bloqueio de leitura ou uso basico.
- **Suspensao Segura (`SUSPENDED`):** Modo somente leitura (*Read-Only*) garantindo ao titular o direito soberano de consultar seu historico e exportar 100% dos seus dados a qualquer momento.

---

## 4. Governanca LGPD, Sigilo Bancario e Credibilidade Enterprise

Diferente de aplicativos gratuitos que monetizam dados de consumo dos usuarios, o **PFM Pulse** adota o principio de **Sigilo Bancario Zero-Trust**:

1. **Administracao Cega a Dados Pessoais (Zero-PII Admin):** A equipe de operacao da plataforma visualiza apenas indicadores agregados de saude do servico e status de assinatura, sendo tecnicamente impedida pelo banco de dados de ler transacoes, saldos ou faturas privadas dos clientes.
2. **Processamento de Faturas sem Rastro em Disco:** Faturas PDF sao lidas e validadas integralmente em memoria volatil, sem gravacao de arquivos brutos em servidores de disco.
3. **Soberania e Direito ao Esquecimento (Art. 18 da LGPD):** O titular pode exportar todo o seu livro-razao em formato aberto (`JSON` / `CSV`) ou acionar a exclusao criptografica definitiva (*Crypto-Shredding*) com um clique.

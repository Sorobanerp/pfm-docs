# Roteiro de Demonstracao Executiva ao Vivo (20 Minutos Cronometrados)

**Publico-Alvo:** Stakeholders Executivos, C-Level, Arquitetos de Core Banking e Usuarios do Piloto Familiar
**Tenant de Demonstracao:** `Familia Silva - Piloto MVP` (`dddddddd-dddd-4ddd-8ddd-dddddddddddd`)
**Pre-Requisito (1 comando antes de entrar na sala):**
```bash
/home/dantas/workspace/pfm-platform/pfm-shared-infra/demo/run_demo_check.sh
```

---

## Cronograma Executivo (20 Minutos)

| Bloco | Tempo | Modulo / Tela | Foco da Demonstracao |
|---|---|---|---|
| **Bloco 1** | `00:00 -- 04:00` | `http://localhost:18300/` | Visao Consolidada vs. Por Titular, Run-rate (`Semaforo: RED`) e Regra de Ouro `"Limite disponivel != Orcamento"` (RN02). |
| **Bloco 2** | `04:00 -- 08:00` | `http://localhost:18300/cards` | Matriz Multi-Cartoes (`Itau 5285`, `Itau 1360`, `BB 7741`, `Marisa 0912`), Parcelamento 10x e Upload em Lote PDF em RAM (Zero-Persistence). |
| **Bloco 3** | `08:00 -- 12:00` | `http://localhost:18300/inbox` | Pipeline IA em 3 Camadas: Limpeza de Adquirentes (`JIM.COM*`, `MP *`), Extracao de Cidade (`Acu / RN`) e Aprendizado Retroativo na Camada 1. |
| **Bloco 4** | `12:00 -- 16:00` | `http://localhost:18300/contracts` | Simulador Imutavel de Contratos (`SAC 360m`, `Price` e `Consorcio 72m`): Reduzir Prazo vs. Reduzir Parcela e ROI Efetivo isento de IR. |
| **Bloco 5** | `16:00 -- 20:00` | Terminal & Mobile Offline-First | Conciliacao Cupom NFC-e +/-3 dias + Alerta de Inflacao `>10%` por EAN (`7891000100103`) e Prova ao Vivo de Isolamento Zero-Trust PostgreSQL 16 RLS. |

---

## Passo a Passo Detalhado (O Que Clicar e O Que Destacar)

### Bloco 1 (`00:00 -- 04:00`) -- Visao Consolidada & Termometro Orcamentario (`/`)
1. **Abra `http://localhost:18300/` no navegador.**
2. **Destaque o Banner Superior (RN02):**
   - Aponte para o alerta ambar: *"Regra de Ouro (RN02): Limite disponivel de cartao != Orcamento"*.
   - Explique: *"A Familia Silva possui **R$ 64.500,00** de limite somado nos 4 cartoes, mas a renda liquida realizada do mes e **R$ 18.200,00**. Bancos e planilhas comuns mostram limite disponivel como poder de compra; o PFM Core Banking confronta o gasto projetado exclusivamente contra a renda liquida regular."*
3. **Destaque o Card Central (Projecao Run-rate & Semaforo):**
   - Mostre o badge **`Semaforo: RED`** e a projecao de fechamento de **R$ 18.828,45** (**103,5% da renda**, gerando deficit projetado de **-R$ 628,45**).
   - Mostre o indicador **`Fonte: LIVE_API`** (ou `ETAG_304_CACHE` no refresh, comprovando cache HTTP/3-HTTP/2 em `< 6ms`).
4. **Clique no Seletor de Escopo:**
   - Alterne ao vivo de **`Familia Consolidada`** para **`Por Titular: Dantas`** (`OWNER`) e **`Por Titular: Conjuge`** (`MEMBER`), mostrando a decomposicao instantanea sem misturar orcamentos individuais.

---

### Bloco 2 (`04:00 -- 08:00`) -- Matriz Multi-Cartoes & Upload PDF Zero-Persistence (`/cards`)
1. **Clique na aba `2. Matriz Multi-Cartoes` (`/cards`).**
2. **Destaque as Colunas Temporais da Tabela Comparativa:**
   - Mostre lado a lado os 4 cartoes da familia (`Itau Black 5285`, `Itau Platinum 1360`, `BB Ourocard 7741`, `Marisa 0912`).
   - Explique a diferenca entre **Fatura Atual (M)** (`R$ 6.890,45`), **Proxima Fatura (M+1)** (`R$ 4.540,30`) e **Demais Faturas (M+2..N)** (`R$ 14.910,00`), incluindo a compra parcelada em 10x (`R$ 1.000,03` -> 9 parcelas de `R$ 100,00` e 10a parcela de `R$ 100,03` sem perda de centavos `HALF_EVEN`).
3. **Execute o Upload em Lote ao Vivo:**
   - Selecione um arquivo PDF de fatura, preencha a senha opcional e clique em **`Processar Faturas e Validar Checksum`**.
   - Destaque: *"O desbloqueio do PDF ocorre **100% em buffer de memoria RAM** no `pfm-ingestion-bff-go` e os bytes sao zerados via `defer clear(buf)` antes do retorno (ADR-006 Zero-Persistence). Alem disso, o motor valida matematicamente se a soma de compras + tarifas ocultas (`Itau Avisa R$ 7,99`) - estornos (`-R$ 168,94`) bate exatamente com o total declarado da fatura."*

---

### Bloco 3 (`08:00 -- 12:00`) -- Inbox de Revisao & Pipeline IA 3 Camadas (`/inbox`)
1. **Clique na aba `3. Inbox de Revisao (IA Camada 1)` (`/inbox`).**
2. **Mostre a Normalizacao Deterministica da Camada 2:**
   - Aponte para o item `JIM.COM* COMERCIO SERTAO LTDAACUBRA`: mostre que o sistema ja removeu o prefixo da maquininha (`JIM.COM*`), limpou o nome para **`COMERCIO SERTAO LTDA`** e extraiu automaticamente o municipio **`Cidade: Acu / RN`**.
   - Aponte tambem para `MP *CHURRASCARIA GAUCHAACUBRA`: explique como a Camada 2 corrige falsos positivos de adquirentes classificando churrascarias em `Restaurantes & Gastronomia`.
3. **Clique em `Aplicar para todo o historico deste estabelecimento (6)`:**
   - Mostre o banner verde imediato confirmando a gravacao da regra na **Camada 1 (`pfm_ai_rules`)** e a reclassificacao retroativa de todo o historico do tenant sem precisar acionar a API do Gemini nas proximas faturas (FinOps).

---

### Bloco 4 (`12:00 -- 16:00`) -- Simulador Imutavel SAC / Price / Consorcio (`/contracts`)
1. **Clique na aba `4. Simulador SAC / Price / Consorcio` (`/contracts`).**
2. **Simule uma Amortizacao Extraordinaria no Financiamento Imobiliario SAC:**
   - Com saldo devedor de **R$ 320.000,00** e aporte extraordinario (ex.: FGTS) de **R$ 50.000,00**, mostre o comparativo entre **`Reduzir Prazo (Maior Economia)`** e **`Reduzir Valor da Parcela (Alivio Mensal)`**.
   - Destaque a economia total de juros/seguros e o **ROI Efetivo isento de IR** calculado em `< 2ms` pelo `pfm-forecast-engine-go` sem alterar o contrato original no banco.
3. **Alterne para `Consorcio Veicular`:**
   - Demonstre a simulacao de lance (`ExtraAmortizationAmount`) abatendo taxa de administracao diluida e reajuste anual.

---

### Bloco 5 (`16:00 -- 20:00`) -- Conciliacao NFC-e + Inflacao `>10%` por EAN & Prova Zero-Trust RLS no Terminal
1. **Mostre a Conciliacao Automatica Cupom NFC-e x Fatura e Inflacao Pessoal por EAN:**
   - Execute no terminal:
     ```bash
     docker exec -i postgres-core-ledger psql -U pfm_app_user -d pfm_core_ledger -c "
       BEGIN;
       SET LOCAL app.current_tenant_id = 'dddddddd-dddd-4ddd-8ddd-dddddddddddd';
       SELECT ean, description, unit_price, issued_at::date FROM receipt_items WHERE ean = '7891000100103' ORDER BY issued_at;
       COMMIT;"
     ```
   - Destaque: *"O Cafe Torrado 500g (`EAN 7891000100103`) subiu de **R$ 20,0000** para **R$ 23,5000** (**+17,50% > limite de 10%**), disparando o `PriceInflationAlert` e conciliando com a linha de **R$ 313,01** da fatura do cartao sem duplicar a despesa na categoria Alimentacao."*
2. **Prova Final ao Vivo de Seguranca Bancaria (PostgreSQL 16 Row-Level Security):**
   - Execute no terminal uma query com a conexao da aplicacao (`pfm_app_user`) sem `tenant_id` (ou com outro tenant):
     ```bash
     docker exec -i postgres-core-ledger psql -U pfm_app_user -d pfm_core_ledger -c "SELECT count(*) AS registros_vazados FROM ledger_entries;"
     ```
   - Mostre o resultado **`0`** linhas: mesmo sem clausula `WHERE` na query SQL, o motor do PostgreSQL 16 bloqueia 100% do acesso quando o `ScopedValue` do tenant nao esta vinculado a transacao.

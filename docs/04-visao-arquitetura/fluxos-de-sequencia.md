# 4.2. Fluxos de Sequencia Criticos (PDF em RAM, IA 3 Camadas, NFC-e e Contratos)

<span class="badge-green">Artefato 04 - Fluxos de Sequencia</span>
<span class="badge-glow">Zero-Disk RAM Parsing &amp; Event-Driven</span>

Este documento apresenta os fluxogramas de sequencia ponta a ponta dos quatro fluxos arquiteturais criticos da plataforma **PFM Core Banking**.

---

## 1. Ingestao de Fatura PDF 100% em Memoria RAM (`Zero-Disk Persistence`)

Nenhum arquivo PDF de fatura repousa em disco nao-cifrado. O `pfm-ingestion-bff-go` le o stream em buffer volatil (`io.LimitReader` de 15 MB), valida o checksum matematico (`soma(itens) == total_declarado`), limpa o slice da memoria (`clear(rawBody)`) e publica o evento para categorizacao.

```mermaid
sequenceDiagram
    autonumber
    actor User as Titular (Web / Android)
    participant BFF as pfm-ingestion-bff-go (:8080)
    participant S3 as AWS S3 + KMS (Envelope Encryption)
    participant KAFKA as Kafka (statement.raw.extracted)
    participant AI as pfm-ai-worker-python (Lambda Arm64)
    participant LEDGER as pfm-core-ledger-java (:9090)

    User->>BFF: POST /api/v1/statements/upload (X-Tenant-ID + Stream PDF)
    Note over BFF: Leitura 100% em RAM (Zero escrita em disco)
    BFF->>BFF: Valida Checksum (Soma dos Itens == Total da Fatura em R$)
    alt Divergencia de Checksum (diff != R$ 0,00)
        BFF-->>User: 409 Conflict (Checksum Mismatch)
    else Checksum Integro
        BFF->>S3: PutObject cifrado com SSE-KMS (alias/pfm-master-key)
        BFF->>BFF: Limpa buffer RAM (clear slice)
        BFF->>KAFKA: Publica StatementRawExtracted (key=tenant_id)
        BFF-->>User: 200 OK (Resumo extraido e lote enfileirado)
    end

    KAFKA->>AI: Aciona pipeline de 3 camadas (Sem tocar no PostgreSQL)
    AI->>KAFKA: Publica CategorizedTransaction (topico: tx.categorized)
    KAFKA->>LEDGER: Consome tx.categorized
    LEDGER->>LEDGER: Persiste sob FORCE RLS + Outbox + audit_log append-only
```

---

## 2. Pipeline de Categorizacao por IA em 3 Camadas (`pfm-ai-worker-python`)

```mermaid
sequenceDiagram
    autonumber
    participant KAFKA as Topico statement.raw.extracted
    participant WORKER as pfm-ai-worker-python
    participant L1 as Camada 1: Regras Deterministicas & Cache
    participant L2 as Camada 2: Similaridade Local (pgvector / ONNX)
    participant L3 as Camada 3: Gemini 2.5 Flash (JSON Schema Strict)
    participant OUT as Topico tx.categorized / tx.dlq

    KAFKA->>WORKER: Evento bruto (tenant_id, merchant_raw, amount_brl)
    WORKER->>WORKER: Sanitiza PII (remove CPF, cartao e nomes proprios)
    WORKER->>L1: Consulta regra exata aprendida pelo tenant
    alt Match Deterministico (Confianca = 1.00)
        L1-->>WORKER: Categoria Nivel 1 :: Nivel 2
        WORKER->>OUT: Publica em tx.categorized
    else Sem Match na Camada 1
        WORKER->>L2: Executa classificacao vetorial local (< 12ms)
        alt Confianca >= 0.82
            L2-->>WORKER: Categoria Nivel 1 :: Nivel 2
            WORKER->>OUT: Publica em tx.categorized
        else Caso Ambiguo (< 5% do volume)
            WORKER->>L3: Inferencia estruturada Pydantic (response_schema)
            L3-->>WORKER: Categoria sugerida ou fallback OUTROS :: NAO_CATEGORIZADO
            WORKER->>OUT: Publica em tx.categorized (ou tx.dlq apos retries)
        end
    end
```

---

## 3. Captura de Cupom Fiscal NFC-e e Conciliacao sem Duplicidade (`RN04`)

```mermaid
sequenceDiagram
    autonumber
    actor User as Usuario Mobile / Web
    participant BFF as pfm-ingestion-bff-go (:8080)
    participant SEFAZ as Portal SEFAZ Estadual
    participant LEDGER as pfm-core-ledger-java (:9090)
    participant PG as PostgreSQL 16 (FORCE RLS)

    User->>BFF: POST /api/v1/receipts/nfce (qrCodeUrl, cardId, idempotencyKey)
    BFF->>SEFAZ: HTTP GET com Circuit Breaker + Exponential Backoff
    SEFAZ-->>BFF: Nota Fiscal Autorizada (CNPJ, Itens, Valor Total em R$)
    BFF->>LEDGER: Forward ProcessReceipt (X-Tenant-ID)
    LEDGER->>PG: BEGIN + SET LOCAL app.current_tenant_id
    LEDGER->>PG: Busca transacao candidata (+/- R$ 0,05 e janela <= 48h)
    alt Match Encontrado (Score >= 0.90)
        LEDGER->>PG: Atualiza lancamento para CONCILED (sem duplicar saldo)
    else Nova Compra
        LEDGER->>PG: Insere lancamento contabil + itens fiscais + audit_log
    end
    LEDGER->>PG: COMMIT
    LEDGER-->>BFF: ProcessReceiptOutput
    BFF-->>User: 200 OK (Recibo conciliado)
```

---

## 4. Simulacao Quantitativa de Amortizacao SAC, Price e Consorcio (`pfm-forecast-engine-go`)

```mermaid
sequenceDiagram
    autonumber
    actor User as Titular (Web / Swagger UI)
    participant BFF as pfm-ingestion-bff-go (:8080)
    participant FORECAST as pfm-forecast-engine-go (:9091 gRPC)

    User->>BFF: POST /api/v1/contracts/simulate (X-Tenant-ID + Payload SAC/Price/Consorcio)
    BFF->>FORECAST: gRPC SimulateContractAmortization (shopspring/decimal)
    FORECAST->>FORECAST: Calcula cronograma original vs. cronograma apos aporte extra em R$
    FORECAST->>FORECAST: Apura economia total de juros (R$), parcelas eliminadas e ROI (%)
    FORECAST-->>BFF: SimulateContractResponse (Zero float64)
    BFF-->>User: 200 OK (Tabela comparativa e economia projetada em R$)
```

# Fluxos Críticos & Diagramas de Sequência

Esta seção documenta os três fluxos arquiteturais mais críticos da plataforma **PFM Core Banking**, detalhando a interação assíncrona e síncrona entre os microsserviços, garantias de segurança em memória e mecanismos de resiliência.

---

## 1. Ingestão de Fatura PDF 100% em RAM (`Zero-Disk Persistence`)

Em conformidade com o **ADR-006 (Privacidade & LGPD)**, nenhum arquivo PDF de fatura de cartão de crédito pode tocar discos persistentes (EBS, S3, discos locais de nós Kubernetes). Todo o ciclo de recepção, descriptografia de senha (se aplicável), extração tabular e descarte seguro (`zero-fill` do slice de bytes) ocorre estritamente em memória volátil (`bytes.Reader` / `tmpfs`).

```mermaid
sequenceDiagram
    autonumber
    actor User as 👤 Titular (Web/Mobile)
    participant GW as 🛡️ pfm-api-gateway
    participant PDF as 📄 pfm-ingestion-pdf-service (Go)
    participant REDIS as ⚡ Redis (Idempotency)
    participant AI as 🧠 pfm-ai-categorizer-service (Py)
    participant KAFKA as 📨 Apache Kafka
    participant CARDS as 💳 pfm-cards-service (Java 25)
    participant LEDGER as 📒 pfm-ledger-service (Java 25)

    User->>GW: POST /v1/statements/upload (Multipart Stream + Idempotency-Key)
    GW->>GW: Valida JWT, extrai tenant_id e verifica Content-Length <= 15MB
    GW->>PDF: gRPC StreamUploadStatement (mTLS + X-Tenant-ID)
    
    PDF->>REDIS: SETNX idempotency:{tenant_id}:{sha256_pdf} (TTL 72h)
    alt Fatura já processada anteriormente
        REDIS-->>PDF: Key Exists (Retorna statement_batch_id existente)
        PDF-->>GW: 200 OK (Idempotent Replay)
        GW-->>User: 200 OK (Resumo do processamento anterior)
    else Novo processamento em RAM
        REDIS-->>PDF: OK (Lock adquirido)
        Note over PDF: Aloca buffer em memória volátil (bytes.Reader)<br/>PROIBIDO: os.Create() ou escrita em disco
        PDF->>PDF: Extrai metadados da fatura (Data Fechamento, Vencimento, Total)
        PDF->>PDF: Faz parsing das linhas de lançamento (Data Compra, Descrição, Parcela i/N, Valor)
        PDF->>PDF: Zero-fill no buffer de bytes do PDF (memclr) e libera ponteiro
        
        PDF->>AI: gRPC BatchCategorize(items[]) [Timeout: 800ms]
        AI-->>PDF: Categorias Nível 1 & Nível 2 + Confidence Score
        
        PDF->>KAFKA: Produce StatementParsedEvent (key=tenant_id)
        PDF-->>GW: 202 Accepted (statement_batch_id, total_items)
        GW-->>User: 202 Accepted (Processamento iniciado)
    end

    KAFKA->>CARDS: Consume StatementParsedEvent
    CARDS->>CARDS: Atualiza ciclo da fatura, desdobra parcelas futuras e aplica RN03 (Estornos)
    CARDS->>KAFKA: Transactional Outbox -> CardTransactionsReadyEvent
    
    KAFKA->>LEDGER: Consume CardTransactionsReadyEvent
    LEDGER->>LEDGER: Escritura lançamentos em Regime de Competência (RN01) com NUMERIC(19,4) (RN06)
```

### Garantias de Engenharia do Fluxo PDF

- **Zero-Disk Security**: O container do `pfm-ingestion-pdf-service` roda com `readOnlyRootFilesystem: true` no Kubernetes, impedindo a nível de Kernel qualquer tentativa acidental de gravação em disco.
- **Deduplicação Criptográfica**: O hash `SHA-256` do stream binário combinado ao `tenant_id` impede que o reenvio da mesma fatura duplique lançamentos no Ledger.

---

## 2. Pipeline de Categorização por IA em 3 Camadas (`pfm-ai-categorizer-service`)

Para equilibrar **baixa latência**, **custo operacional (FinOps)** e **alta acurácia semântica**, o serviço de categorização implementa uma arquitetura em funil de 3 camadas, mapeando toda transação obrigatoriamente para a **Taxonomia Oficial de 2 Níveis (Categoria Principal -> Subcategoria)**.

```mermaid
sequenceDiagram
    autonumber
    participant CALLER as ⚙️ Ledger / PDF / NFC-e Service
    participant API as 🧠 Categorizer FastAPI (Python 3.12)
    participant L1 as ⚡ Camada 1: Exact/Regex + Redis Cache
    participant L2 as 🤖 Camada 2: Local ONNX ML (MiniLM + LightGBM)
    participant L3 as ☁️ Camada 3: Cloud LLM (Anonimizado)

    CALLER->>API: gRPC CategorizeTransaction(merchant_raw, cnpj, amount, mcc)
    API->>API: Normaliza texto e remove PII (CPF, nomes próprios, números de cartão)

    rect rgb(230, 245, 255)
        Note over API,L1: CAMADA 1: Determinística & Memória (< 2ms | ~65% do volume)
        API->>L1: Lookup por CNPJ exato, MCC determinístico ou Regra Customizada do Tenant
        alt Match encontrado na Camada 1
            L1-->>API: Categoria (Nível 1, Nível 2) | Confidence = 1.00 | Source = L1_RULE
            API-->>CALLER: Return CategorizationResult
        end
    end

    rect rgb(235, 250, 235)
        Note over API,L2: CAMADA 2: Inferência Local em CPU/ONNX (< 12ms | ~30% do volume)
        API->>L2: Gera embedding local + classifica na Taxonomia Oficial de 2 Níveis
        L2-->>API: Predição + Confidence Score (0.00 a 1.00)
        alt Confidence Score >= 0.82
            API->>L1: Atualiza cache semântico no Redis (TTL 30 dias)
            API-->>CALLER: Return CategorizationResult (Source = L2_ONNX)
        end
    end

    rect rgb(255, 245, 230)
        Note over API,L3: CAMADA 3: Fallback Cloud LLM com Circuit Breaker (< 600ms | ~5% do volume)
        API->>L3: Prompt estruturado (JSON Schema Strict) apenas com descrição sanitizada
        alt LLM responde dentro do SLA e Confiança >= 0.70
            L3-->>API: Categoria (Nível 1, Nível 2) | Source = L3_LLM
            API->>L1: Salva aprendizado no Redis Cache para futuras ocorrências
            API-->>CALLER: Return CategorizationResult
        else Timeout / Circuit Breaker Aberto / Baixa Confiança
            L3-->>API: Fallback Seguro (Degradação Graciosa - ADR-004)
            API-->>CALLER: Return OUTROS :: NAO_CATEGORIZADO (Requer revisão do usuário)
        end
    end
```

### Resumo de Performance e FinOps do Funil de IA

| Camada | Tecnologia | Latência Alvo (P95) | % Retenção Estimada | Custo Marginal por 1M Transações |
| :--- | :--- | :---: | :---: | :---: |
| **Camada 1 (L1)** | Redis Lookup (CNPJ / Histórico Tenant / Regex) | $< 2\text{ ms}$ | ~65% | $\approx \$0.00$ (Memória existente) |
| **Camada 2 (L2)** | ONNX Runtime CPU (`int8` quantized embedding) | $< 12\text{ ms}$ | ~30% | $\approx \$0.08$ (Compute K8s local) |
| **Camada 3 (L3)** | Cloud LLM Flash/Mini (JSON Schema Constrained) | $< 600\text{ ms}$ | ~5% | $\approx \$0.45$ (Apenas 5% chegam ao LLM) |

---

## 3. Captura Offline de NFC-e via QR Code & Conciliação Automática

O aplicativo `pfm-mobile-android` opera sob paradigma **Offline-First**. O usuário escaneia o QR Code de uma Nota Fiscal de Consumidor Eletrônica (NFC-e) no caixa do estabelecimento mesmo sem conexão 4G/Wi-Fi. Assim que a conectividade é restabelecida, a nota é sincronizada, raspada na SEFAZ e conciliada automaticamente com o lançamento do cartão ou conta corrente (**RN04**).

```mermaid
sequenceDiagram
    autonumber
    actor User as 👤 Usuário no Estabelecimento
    participant MOB as 📱 pfm-mobile-android (Kotlin Offline-First)
    participant GW as 🛡️ pfm-api-gateway
    participant NFCE as 🧾 pfm-nfce-scraper-service (Go)
    participant SEFAZ as 🏛️ Portal SEFAZ Estadual
    participant KAFKA as 📨 Apache Kafka
    participant RECON as 🔄 pfm-reconcile-service (Java 25)
    participant LEDGER as 📒 pfm-ledger-service (Java 25)

    User->>MOB: Escaneia QR Code da NFC-e com a câmera (Sem Internet / Modo Avião)
    MOB->>MOB: Extrai Chave de Acesso (44 dígitos), URL SEFAZ e Timestamp local
    MOB->>MOB: Persiste no banco local criptografado (Room + SQLCipher) com status PENDING_SYNC
    MOB-->>User: Feedback instantâneo (< 150ms): "Cupom salvo! Sincronizará quando houver rede."

    Note over MOB,GW: Conectividade 4G/5G/Wi-Fi detectada pelo Android WorkManager
    MOB->>GW: POST /v1/nfce/sync (Chave 44 dígitos + QR URL + Idempotency-Key)
    GW->>NFCE: gRPC EnqueueNfceScrape (mTLS + tenant_id)
    NFCE-->>GW: 202 Accepted (scrape_job_id)
    GW-->>MOB: 202 Accepted (Atualiza status local para PROCESSING)

    NFCE->>SEFAZ: HTTP GET URL QR Code (Com Circuit Breaker, Pool de IPs e Retry Backoff)
    alt SEFAZ Disponível
        SEFAZ-->>NFCE: HTML/XML da Nota Fiscal Autorizada
        NFCE->>NFCE: Extrai CNPJ, Razão Social, Data/Hora Emissão, Forma Pagamento, Valor Total e Itens
        NFCE->>KAFKA: Produce NfceExtractedEvent (key=tenant_id)
    else SEFAZ Indisponível / Instável (Erro 5xx ou Timeout)
        SEFAZ-->>NFCE: 503 Service Unavailable
        NFCE->>KAFKA: Agenda retentativa assíncrona (Backoff até 24h sem perder o cupom)
    end

    KAFKA->>RECON: Consume NfceExtractedEvent
    RECON->>LEDGER: gRPC FindCandidateTransactions(tenant_id, valor ± R$ 0,05, janela ± 48h)
    LEDGER-->>RECON: Lista de candidatos (ex: Compra Cartão ou Pix de mesmo valor)

    alt Match Único de Alta Confiança (Score >= 90%)
        RECON->>RECON: Cria vínculo de conciliação (RN04) sem duplicar o saldo contábil
        RECON->>LEDGER: gRPC EnrichTransactionWithNfceItems(transaction_id, nfce_items[], cnpj)
        LEDGER-->>RECON: 200 OK (Transação enriquecida e auditada)
    else Múltiplos Candidatos ou Divergência Parcial
        RECON->>RECON: Registra sugestão de conciliação assistida (PENDING_USER_APPROVAL)
    else Nenhum Lançamento Existente (Ex: Pagamento em Espécie ou Fatura ainda não importada)
        RECON->>LEDGER: gRPC CreateProvisionalTransactionFromNfce(nfce_data)
    end
```

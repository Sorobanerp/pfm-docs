# Fluxos Críticos & Diagramas de Sequência (V3)

Esta seção documenta os fluxos arquiteturais mais críticos da plataforma **PFM Core Banking V3**, detalhando a interação entre os serviços em **ECS Fargate Spot / Service Connect**, a execução **Serverless Event-Driven da Lambda IA Arm64 (ADR-009)**, a ingestão PDF em RAM (`Zero-Disk`) e o pipeline de **Observabilidade Tail-Sampled + Auditoria Imutável (ADR-010)**.

---

## 1. Ingestão de Fatura PDF 100% em RAM (`Zero-Disk Persistence`)

Em conformidade com o **ADR-006 (Privacidade & LGPD)**, nenhum arquivo PDF de fatura de cartão de crédito toca discos persistentes não-cifrados. Todo o ciclo de recepção, extração tabular e descarte seguro (`memclr` do slice de bytes) ocorre estritamente em memória volátil (`bytes.Reader`), sendo os metadados cifrados via KMS quando necessário.

```mermaid
sequenceDiagram
    autonumber
    actor User as 👤 Titular (Web/Mobile)
    participant GW as 🛡️ Edge ALB / Envoy Gateway
    participant BFF as 📄 pfm-ingestion-bff-go (ECS Spot)
    participant REDIS as ⚡ Upstash Redis Serverless
    participant KAFKA as 📨 Upstash Kafka Serverless
    participant AI as 🧠 pfm-ai-worker-python (Lambda Arm64)
    participant LEDGER as 📒 pfm-core-ledger-java (ECS Spot)

    User->>GW: POST /v1/statements/upload (Multipart Stream + Idempotency-Key)
    GW->>GW: Valida JWT OIDC, extrai tenant_id e verifica Content-Length <= 15MB
    GW->>BFF: HTTP/gRPC StreamUploadStatement (X-Tenant-ID)

    BFF->>REDIS: SETNX idempotency:{tenant_id}:{sha256_pdf} (TTL 72h)
    alt Fatura já processada anteriormente
        REDIS-->>BFF: Key Exists (Retorna statement_batch_id existente)
        BFF-->>GW: 200 OK (Idempotent Replay)
        GW-->>User: 200 OK (Resumo do processamento anterior)
    else Novo processamento em RAM
        REDIS-->>BFF: OK (Lock adquirido)
        Note over BFF: Aloca buffer em memória volátil (bytes.Reader)<br/>PROIBIDO: os.Create() ou escrita em disco
        BFF->>BFF: Extrai metadados e linhas (diff = 0.0000 vs total declarado)
        BFF->>BFF: Zero-fill no buffer de bytes do PDF (memclr) e libera ponteiro

        BFF->>KAFKA: Produce StatementParsedEvent (key=tenant_id)
        BFF-->>GW: 202 Accepted (statement_batch_id, total_items)
        GW-->>User: 202 Accepted (Processamento iniciado)
    end

    KAFKA->>AI: Trigger Lambda Arm64 (StatementParsedEvent)
    Note over AI: Sem conexão direta ao PostgreSQL (ADR-009)
    AI->>AI: Executa funil 3 camadas (L1 Redis -> L2 ONNX -> L3 LLM)
    AI->>KAFKA: Produce StatementCategorizedEvent (key=tenant_id)

    KAFKA->>LEDGER: Consume StatementCategorizedEvent
    LEDGER->>LEDGER: Escritura partidas dobradas (RN01/RN06), RLS e grava audit_log append-only
```

### Garantias de Engenharia do Fluxo PDF

- **Zero-Disk Security**: O container `pfm-ingestion-bff-go` roda em modo `readonlyRootFilesystem`, impedindo qualquer escrita acidental no sistema de arquivos.
- **Deduplicação Criptográfica**: O hash `SHA-256` do stream binário combinado ao `tenant_id` impede que o reenvio da mesma fatura duplique lançamentos no Core Ledger.

---

## 2. Pipeline de Categorização por IA em 3 Camadas (`AWS Lambda Arm64`)

Em conformidade com o **ADR-009**, o `pfm-ai-worker-python` opera como **AWS Lambda Arm64 Event-Driven** (custo **US$ 0,00** quando ocioso), estritamente isolado via **Arquitetura Hexagonal** e **sem acesso direto ao PostgreSQL**. Os resultados retornam via Kafka ou gRPC ao Core Ledger.

```mermaid
sequenceDiagram
    autonumber
    participant KAFKA as 📨 Upstash Kafka / gRPC Caller
    participant LAMBDA as 🧠 pfm-ai-worker-python (Lambda Arm64)
    participant L1 as ⚡ Camada 1: Upstash Redis / Exact Regex
    participant L2 as 🤖 Camada 2: Local ONNX ML (MiniLM + LightGBM)
    participant L3 as ☁️ Camada 3: Cloud LLM (Anonimizado)
    participant OUT as 📤 Kafka Topic: ai.categorized / DLQ KMS

    KAFKA->>LAMBDA: Trigger Event (merchant_raw, cnpj, amount, mcc, tenant_id)
    LAMBDA->>LAMBDA: Normaliza texto e remove PII (CPF, nomes, números de cartão)

    rect rgb(230, 245, 255)
        Note over LAMBDA,L1: CAMADA 1: Determinística & Memória (< 2ms | ~65% do volume)
        LAMBDA->>L1: Lookup por CNPJ exato, MCC ou Regra Customizada do Tenant
        alt Match encontrado na Camada 1
            L1-->>LAMBDA: Categoria (Nível 1, Nível 2) | Confidence = 1.00 | Source = L1_RULE
            LAMBDA->>OUT: Publica CategorizationResult (Sem tocar no DB!)
        end
    end

    rect rgb(235, 250, 235)
        Note over LAMBDA,L2: CAMADA 2: Inferência Local em CPU Arm64/ONNX (< 12ms | ~30% do volume)
        LAMBDA->>L2: Gera embedding local + classifica na Taxonomia Oficial de 2 Níveis
        L2-->>LAMBDA: Predição + Confidence Score (0.00 a 1.00)
        alt Confidence Score >= 0.82
            LAMBDA->>L1: Atualiza cache semântico no Upstash Redis (TTL 30 dias)
            LAMBDA->>OUT: Publica CategorizationResult (Source = L2_ONNX)
        end
    end

    rect rgb(255, 245, 230)
        Note over LAMBDA,L3: CAMADA 3: Fallback Cloud LLM com Circuit Breaker (< 600ms | ~5% do volume)
        LAMBDA->>L3: Prompt estruturado (JSON Schema Strict) com descrição sanitizada
        alt LLM responde dentro do SLA e Confiança >= 0.70
            L3-->>LAMBDA: Categoria (Nível 1, Nível 2) | Source = L3_LLM
            LAMBDA->>L1: Salva aprendizado no Redis Cache
            LAMBDA->>OUT: Publica CategorizationResult
        else Timeout / Circuit Breaker Aberto / Erro Persistente
            L3-->>LAMBDA: Fallback Seguro (Degradação Graciosa - ADR-004)
            LAMBDA->>OUT: Publica OUTROS :: NAO_CATEGORIZADO (ou envia falha irrecuperável para DLQ cifrada KMS)
        end
    end
```

### Resumo de Performance e FinOps do Funil de IA

| Camada | Tecnologia | Latência Alvo (P95) | % Retenção Estimada | Custo Marginal por 1M Transações |
| :--- | :--- | :---: | :---: | :---: |
| **Camada 1 (L1)** | Upstash Redis Lookup (CNPJ / Regex) | $< 2\text{ ms}$ | ~65% | $\approx \$0.00$ (Cache Serverless) |
| **Camada 2 (L2)** | ONNX Runtime Arm64 (`int8` quantized) | $< 12\text{ ms}$ | ~30% | $\approx \$0.05$ (Lambda Arm64 ms) |
| **Camada 3 (L3)** | Cloud LLM Flash/Mini (JSON Strict) | $< 600\text{ ms}$ | ~5% | $\approx \$0.45$ (Apenas 5% chegam ao LLM) |

---

## 3. Captura Offline de NFC-e via QR Code & Conciliação Automática

O aplicativo `pfm-mobile-android` opera sob paradigma **Offline-First**. O usuário escaneia o QR Code de uma NFC-e no caixa mesmo sem rede; ao reconectar, o cupom é raspado na SEFAZ pelo `pfm-ingestion-bff-go` e conciliado automaticamente pelo `pfm-core-ledger-java` (**RN04**).

```mermaid
sequenceDiagram
    autonumber
    actor User as 👤 Usuário no Estabelecimento
    participant MOB as 📱 pfm-mobile-android (Kotlin Offline-First)
    participant GW as 🛡️ Edge ALB / Envoy Gateway
    participant BFF as 🧾 pfm-ingestion-bff-go (ECS Spot)
    participant SEFAZ as 🏛️ Portal SEFAZ Estadual
    participant KAFKA as 📨 Upstash Kafka Serverless
    participant LEDGER as 📒 pfm-core-ledger-java (ECS Spot)

    User->>MOB: Escaneia QR Code da NFC-e com a câmera (Sem Internet / Modo Avião)
    MOB->>MOB: Extrai Chave de Acesso (44 dígitos), URL SEFAZ e Timestamp local
    MOB->>MOB: Persiste no Room + SQLCipher com status PENDING_SYNC
    MOB-->>User: Feedback instantâneo (< 150ms): "Cupom salvo! Sincronizará quando houver rede."

    Note over MOB,GW: Conectividade 4G/5G/Wi-Fi detectada pelo Android WorkManager
    MOB->>GW: POST /v1/nfce/sync (Chave 44 dígitos + QR URL + Idempotency-Key)
    GW->>BFF: HTTP/gRPC EnqueueNfceScrape (tenant_id)
    BFF-->>GW: 202 Accepted (scrape_job_id)
    GW-->>MOB: 202 Accepted (Atualiza status local para PROCESSING)

    BFF->>SEFAZ: HTTP GET URL QR Code (Circuit Breaker + Retry Backoff)
    alt SEFAZ Disponível
        SEFAZ-->>BFF: HTML/XML da Nota Fiscal Autorizada
        BFF->>BFF: Extrai CNPJ, Razão Social, Emissão, Forma Pagamento, Valor e Itens
        BFF->>KAFKA: Produce NfceExtractedEvent (key=tenant_id)
    else SEFAZ Indisponível (Erro 5xx / Timeout)
        SEFAZ-->>BFF: 503 Service Unavailable
        BFF->>KAFKA: Agenda retentativa assíncrona (ou encaminha para DLQ cifrada KMS após limite)
    end

    KAFKA->>LEDGER: Consume NfceExtractedEvent
    LEDGER->>LEDGER: Busca candidatos (valor ± R$ 0,05, janela ± 48h) via RLS

    alt Match Único de Alta Confiança (Score >= 90%)
        LEDGER->>LEDGER: Cria vínculo de conciliação (RN04) sem duplicar saldo + grava audit_log
    else Múltiplos Candidatos ou Divergência Parcial
        LEDGER->>LEDGER: Registra sugestão de conciliação assistida (PENDING_USER_APPROVAL)
    else Nenhum Lançamento Existente
        LEDGER->>LEDGER: Cria lançamento provisório enriquecido com itens fiscais
    end
```

---

## 4. Observabilidade Multi-Cloud (OTel Tail-Sampling) & Auditoria Imutável (ADR-010)

Para manter visibilidade completa de falhas e latência entre AWS, Azure e GCP sem explodir custos de ingestão SaaS, todos os fluxos passam pelo pipeline **OTel Tail-Based Sampling $\rightarrow$ Datadog** e gravam trilha de auditoria imutável no PostgreSQL:

```mermaid
flowchart LR
    subgraph Services["Microsserviços & Lambda (AWS / Azure / GCP)"]
        S1["Core Ledger (Java 25)"]
        S2["Ingestion BFF & Forecast (Go)"]
        S3["AI Worker (Lambda Python)"]
    end

    subgraph OTel["OpenTelemetry Collector"]
        FILT["Filter Processor<br/>Descarta /health & /actuator"]
        RED["Redaction Processor<br/>Mascara CPF/Cartão/PII"]
        TAIL["Tail-Based Sampling<br/>100% Erros | 100% Latência > 500ms<br/>5-10% Sucessos Rápidos"]
    end

    subgraph Governance["Visão Unificada & Auditoria"]
        DD["📊 Datadog Unified Dashboard<br/>Jornadas UC-01..UC-08 Multi-Cloud"]
        AUDIT[("🔒 Tabela audit_log (PostgreSQL)<br/>Append-Only + FORCE RLS")]
        DLQ[["🔐 Dead Letter Queue (.dlq)<br/>Payload Cifrado via KMS"]]
    end

    S1 & S2 & S3 -->|"OTLP/gRPC"| FILT --> RED --> TAIL -->|"OTLP HTTPS"| DD
    S1 -->|"Mesma Transação ACID"| AUDIT
    S2 & S3 -.->|"Falha após Retries"| DLQ
```

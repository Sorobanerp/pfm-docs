# Fluxos Criticos & Diagramas de Sequencia (V3)

Esta secao documenta os fluxos arquiteturais mais criticos da plataforma **PFM Core Banking V3**, detalhando a interacao entre os servicos em **ECS Fargate Spot / Service Connect**, a execucao **Serverless Event-Driven da Lambda IA Arm64 (ADR-009)**, a ingestao PDF em RAM (`Zero-Disk`) e o pipeline de **Observabilidade Tail-Sampled + Auditoria Imutavel (ADR-010)**.

---

## 1. Ingestao de Fatura PDF 100% em RAM (`Zero-Disk Persistence`)

Em conformidade com o **ADR-006 (Privacidade & LGPD)**, nenhum arquivo PDF de fatura de cartao de credito toca discos persistentes nao-cifrados. Todo o ciclo de recepcao, extracao tabular e descarte seguro (`memclr` do slice de bytes) ocorre estritamente em memoria volatil (`bytes.Reader`), sendo os metadados cifrados via KMS quando necessario.

```mermaid
sequenceDiagram
    autonumber
    actor User as  Titular (Web/Mobile)
    participant GW as  Edge ALB / Envoy Gateway
    participant BFF as  pfm-ingestion-bff-go (ECS Spot)
    participant REDIS as  Upstash Redis Serverless
    participant KAFKA as  Upstash Kafka Serverless
    participant AI as  pfm-ai-worker-python (Lambda Arm64)
    participant LEDGER as  pfm-core-ledger-java (ECS Spot)

    User->>GW: POST /v1/statements/upload (Multipart Stream + Idempotency-Key)
    GW->>GW: Valida JWT OIDC, extrai tenant_id e verifica Content-Length <= 15MB
    GW->>BFF: HTTP/gRPC StreamUploadStatement (X-Tenant-ID)

    BFF->>REDIS: SETNX idempotency:{tenant_id}:{sha256_pdf} (TTL 72h)
    alt Fatura ja processada anteriormente
        REDIS-->>BFF: Key Exists (Retorna statement_batch_id existente)
        BFF-->>GW: 200 OK (Idempotent Replay)
        GW-->>User: 200 OK (Resumo do processamento anterior)
    else Novo processamento em RAM
        REDIS-->>BFF: OK (Lock adquirido)
        Note over BFF: Aloca buffer em memoria volatil (bytes.Reader)<br/>PROIBIDO: os.Create() ou escrita em disco
        BFF->>BFF: Extrai metadados e linhas (diff = 0.0000 vs total declarado)
        BFF->>BFF: Zero-fill no buffer de bytes do PDF (memclr) e libera ponteiro

        BFF->>KAFKA: Produce StatementParsedEvent (key=tenant_id)
        BFF-->>GW: 202 Accepted (statement_batch_id, total_items)
        GW-->>User: 202 Accepted (Processamento iniciado)
    end

    KAFKA->>AI: Trigger Lambda Arm64 (StatementParsedEvent)
    Note over AI: Sem conexao direta ao PostgreSQL (ADR-009)
    AI->>AI: Executa funil 3 camadas (L1 Redis -> L2 ONNX -> L3 LLM)
    AI->>KAFKA: Produce StatementCategorizedEvent (key=tenant_id)

    KAFKA->>LEDGER: Consume StatementCategorizedEvent
    LEDGER->>LEDGER: Escritura partidas dobradas (RN01/RN06), RLS e grava audit_log append-only
```

### Garantias de Engenharia do Fluxo PDF

- **Zero-Disk Security**: O container `pfm-ingestion-bff-go` roda em modo `readonlyRootFilesystem`, impedindo qualquer escrita acidental no sistema de arquivos.
- **Deduplicacao Criptografica**: O hash `SHA-256` do stream binario combinado ao `tenant_id` impede que o reenvio da mesma fatura duplique lancamentos no Core Ledger.

---

## 2. Pipeline de Categorizacao por IA em 3 Camadas (`AWS Lambda Arm64`)

Em conformidade com o **ADR-009**, o `pfm-ai-worker-python` opera como **AWS Lambda Arm64 Event-Driven** (custo **US$ 0,00** quando ocioso), estritamente isolado via **Arquitetura Hexagonal** e **sem acesso direto ao PostgreSQL**. Os resultados retornam via Kafka ou gRPC ao Core Ledger.

```mermaid
sequenceDiagram
    autonumber
    participant KAFKA as  Upstash Kafka / gRPC Caller
    participant LAMBDA as  pfm-ai-worker-python (Lambda Arm64)
    participant L1 as  Camada 1: Upstash Redis / Exact Regex
    participant L2 as  Camada 2: Local ONNX ML (MiniLM + LightGBM)
    participant L3 as  Camada 3: Cloud LLM (Anonimizado)
    participant OUT as  Kafka Topic: ai.categorized / DLQ KMS

    KAFKA->>LAMBDA: Trigger Event (merchant_raw, cnpj, amount, mcc, tenant_id)
    LAMBDA->>LAMBDA: Normaliza texto e remove PII (CPF, nomes, numeros de cartao)

    rect rgb(230, 245, 255)
        Note over LAMBDA,L1: CAMADA 1: Deterministica & Memoria (< 2ms | ~65% do volume)
        LAMBDA->>L1: Lookup por CNPJ exato, MCC ou Regra Customizada do Tenant
        alt Match encontrado na Camada 1
            L1-->>LAMBDA: Categoria (Nivel 1, Nivel 2) | Confidence = 1.00 | Source = L1_RULE
            LAMBDA->>OUT: Publica CategorizationResult (Sem tocar no DB!)
        end
    end

    rect rgb(235, 250, 235)
        Note over LAMBDA,L2: CAMADA 2: Inferencia Local em CPU Arm64/ONNX (< 12ms | ~30% do volume)
        LAMBDA->>L2: Gera embedding local + classifica na Taxonomia Oficial de 2 Niveis
        L2-->>LAMBDA: Predicao + Confidence Score (0.00 a 1.00)
        alt Confidence Score >= 0.82
            LAMBDA->>L1: Atualiza cache semantico no Upstash Redis (TTL 30 dias)
            LAMBDA->>OUT: Publica CategorizationResult (Source = L2_ONNX)
        end
    end

    rect rgb(255, 245, 230)
        Note over LAMBDA,L3: CAMADA 3: Fallback Cloud LLM com Circuit Breaker (< 600ms | ~5% do volume)
        LAMBDA->>L3: Prompt estruturado (JSON Schema Strict) com descricao sanitizada
        alt LLM responde dentro do SLA e Confianca >= 0.70
            L3-->>LAMBDA: Categoria (Nivel 1, Nivel 2) | Source = L3_LLM
            LAMBDA->>L1: Salva aprendizado no Redis Cache
            LAMBDA->>OUT: Publica CategorizationResult
        else Timeout / Circuit Breaker Aberto / Erro Persistente
            L3-->>LAMBDA: Fallback Seguro (Degradacao Graciosa - ADR-004)
            LAMBDA->>OUT: Publica OUTROS :: NAO_CATEGORIZADO (ou envia falha irrecuperavel para DLQ cifrada KMS)
        end
    end
```

### Resumo de Performance e FinOps do Funil de IA

| Camada | Tecnologia | Latencia Alvo (P95) | % Retencao Estimada | Custo Marginal por 1M Transacoes |
| :--- | :--- | :---: | :---: | :---: |
| **Camada 1 (L1)** | Upstash Redis Lookup (CNPJ / Regex) | $< 2\text{ ms}$ | ~65% | $\approx \$0.00$ (Cache Serverless) |
| **Camada 2 (L2)** | ONNX Runtime Arm64 (`int8` quantized) | $< 12\text{ ms}$ | ~30% | $\approx \$0.05$ (Lambda Arm64 ms) |
| **Camada 3 (L3)** | Cloud LLM Flash/Mini (JSON Strict) | $< 600\text{ ms}$ | ~5% | $\approx \$0.45$ (Apenas 5% chegam ao LLM) |

---

## 3. Captura Offline de NFC-e via QR Code & Conciliacao Automatica

O aplicativo `pfm-mobile-android` opera sob paradigma **Offline-First**. O usuario escaneia o QR Code de uma NFC-e no caixa mesmo sem rede; ao reconectar, o cupom e raspado na SEFAZ pelo `pfm-ingestion-bff-go` e conciliado automaticamente pelo `pfm-core-ledger-java` (**RN04**).

```mermaid
sequenceDiagram
    autonumber
    actor User as  Usuario no Estabelecimento
    participant MOB as  pfm-mobile-android (Kotlin Offline-First)
    participant GW as  Edge ALB / Envoy Gateway
    participant BFF as  pfm-ingestion-bff-go (ECS Spot)
    participant SEFAZ as  Portal SEFAZ Estadual
    participant KAFKA as  Upstash Kafka Serverless
    participant LEDGER as  pfm-core-ledger-java (ECS Spot)

    User->>MOB: Escaneia QR Code da NFC-e com a camera (Sem Internet / Modo Aviao)
    MOB->>MOB: Extrai Chave de Acesso (44 digitos), URL SEFAZ e Timestamp local
    MOB->>MOB: Persiste no Room + SQLCipher com status PENDING_SYNC
    MOB-->>User: Feedback instantaneo (< 150ms): "Cupom salvo! Sincronizara quando houver rede."

    Note over MOB,GW: Conectividade 4G/5G/Wi-Fi detectada pelo Android WorkManager
    MOB->>GW: POST /v1/nfce/sync (Chave 44 digitos + QR URL + Idempotency-Key)
    GW->>BFF: HTTP/gRPC EnqueueNfceScrape (tenant_id)
    BFF-->>GW: 202 Accepted (scrape_job_id)
    GW-->>MOB: 202 Accepted (Atualiza status local para PROCESSING)

    BFF->>SEFAZ: HTTP GET URL QR Code (Circuit Breaker + Retry Backoff)
    alt SEFAZ Disponivel
        SEFAZ-->>BFF: HTML/XML da Nota Fiscal Autorizada
        BFF->>BFF: Extrai CNPJ, Razao Social, Emissao, Forma Pagamento, Valor e Itens
        BFF->>KAFKA: Produce NfceExtractedEvent (key=tenant_id)
    else SEFAZ Indisponivel (Erro 5xx / Timeout)
        SEFAZ-->>BFF: 503 Service Unavailable
        BFF->>KAFKA: Agenda retentativa assincrona (ou encaminha para DLQ cifrada KMS apos limite)
    end

    KAFKA->>LEDGER: Consume NfceExtractedEvent
    LEDGER->>LEDGER: Busca candidatos (valor +/- R$ 0,05, janela +/- 48h) via RLS

    alt Match Unico de Alta Confianca (Score >= 90%)
        LEDGER->>LEDGER: Cria vinculo de conciliacao (RN04) sem duplicar saldo + grava audit_log
    else Multiplos Candidatos ou Divergencia Parcial
        LEDGER->>LEDGER: Registra sugestao de conciliacao assistida (PENDING_USER_APPROVAL)
    else Nenhum Lancamento Existente
        LEDGER->>LEDGER: Cria lancamento provisorio enriquecido com itens fiscais
    end
```

---

## 4. Observabilidade Multi-Cloud (OTel Tail-Sampling) & Auditoria Imutavel (ADR-010)

Para manter visibilidade completa de falhas e latencia entre AWS, Azure e GCP sem explodir custos de ingestao SaaS, todos os fluxos passam pelo pipeline **OTel Tail-Based Sampling $\rightarrow$ Datadog** e gravam trilha de auditoria imutavel no PostgreSQL:

```mermaid
flowchart LR
    subgraph Services["Microsservicos & Lambda (AWS / Azure / GCP)"]
        S1["Core Ledger (Java 25)"]
        S2["Ingestion BFF & Forecast (Go)"]
        S3["AI Worker (Lambda Python)"]
    end

    subgraph OTel["OpenTelemetry Collector"]
        FILT["Filter Processor<br/>Descarta /health & /actuator"]
        RED["Redaction Processor<br/>Mascara CPF/Cartao/PII"]
        TAIL["Tail-Based Sampling<br/>100% Erros | 100% Latencia > 500ms<br/>5-10% Sucessos Rapidos"]
    end

    subgraph Governance["Visao Unificada & Auditoria"]
        DD[" Datadog Unified Dashboard<br/>Jornadas UC-01..UC-08 Multi-Cloud"]
        AUDIT[(" Tabela audit_log (PostgreSQL)<br/>Append-Only + FORCE RLS")]
        DLQ[[" Dead Letter Queue (.dlq)<br/>Payload Cifrado via KMS"]]
    end

    S1 & S2 & S3 -->|"OTLP/gRPC"| FILT --> RED --> TAIL -->|"OTLP HTTPS"| DD
    S1 -->|"Mesma Transacao ACID"| AUDIT
    S2 & S3 -.->|"Falha apos Retries"| DLQ
```

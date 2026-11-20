# Registro de Decisões Arquiteturais (ADRs V3)

Este documento consolida as **Architecture Decision Records (ADRs V3)** que governam a engenharia da plataforma **PFM Core Banking — Production-Ready FinOps & Multi-Cloud Architecture**. Todas as decisões seguem o formato padronizado de Michael Nygard estendido para ambientes regulados, orientados a FinOps e multicloud.

---

## Sumário Executivo de ADRs

| ID | Título da Decisão | Status | Versão | Escopo |
| :--- | :--- | :---: | :---: | :--- |
| **[ADR-001](#adr-001-poliglotismo-restrito-e-arquitetura-hexagonal)** | Poliglotismo Restrito & Arquitetura Hexagonal | Aprovado | V2 | Todos os Microsserviços & Apps |
| **[ADR-002](#adr-002-topologia-multi-repo-e-mapeamento-11-iac)** | Topologia Multi-Repo & Mapeamento 1:1 IaC | Aprovado | V2 | Governança de Código & CI/CD |
| **[ADR-003](#adr-003-comunicacao-hibrida-rest-http3-e-grpc)** | Comunicação Híbrida: REST HTTP/3 (Edge) & gRPC (East-West) | Aprovado | V2 | APIs, Contratos & Service Mesh |
| **[ADR-004](#adr-004-padroes-de-resiliencia-distribuida)** | Padrões de Resiliência Distribuída & Degradação Graciosa | Aprovado | V2 | Integrações Externas & Core |
| **[ADR-005](#adr-005-eventos-assincronos-com-kafka-e-transactional-outbox)** | Eventos Assíncronos com Apache Kafka & Transactional Outbox | Aprovado | V2 | Mensageria & Consistência Eventual |
| **[ADR-006](#adr-006-isolamento-multitenant-postgresql-rls-e-envelope-encryption)** | Isolamento Multitenant: PostgreSQL RLS & Envelope Encryption | Aprovado | V2 | Banco de Dados, Segurança & LGPD |
| **[ADR-007](#adr-007-arquitetura-multicloud-well-architected-awsazuregcp)** | Arquitetura Multicloud Well-Architected (AWS / Azure / GCP) | Aprovado | V2 | Infraestrutura, SRE & FinOps |
| **[ADR-008](#adr-008-compute-enxuto-de-producao-inicial-trilha-de-hiperescala-kubernetes)** | Compute Enxuto de Produção Inicial & Trilha de Hiperescala Kubernetes | Aprovado | **V3** | ECS Fargate Spot / ACA / Cloud Run $\rightarrow$ K8s |
| **[ADR-009](#adr-009-worker-ia-serverless-event-driven)** | Worker IA Serverless Event-Driven (AWS Lambda Arm64) | Aprovado | **V3** | `pfm-ai-worker-python`, Kafka & Hexagonal |
| **[ADR-010](#adr-010-observabilidade-multi-cloud-unificada-auditoria-imutavel)** | Observabilidade Multi-Cloud Unificada & Auditoria Imutável | Aprovado | **V3** | OTel Tail Sampling, Datadog, SonarCloud & RLS |

---

## ADR-001: Poliglotismo Restrito e Arquitetura Hexagonal

- **Status**: Aprovado (V2)
- **Contexto**: A plataforma PFM Core Banking possui requisitos heterogêneos que variam desde escrituração contábil ACID com regras estritas de arredondamento até scraping de notas fiscais (NFC-e), parsing de faturas PDF em memória (sem escrita em disco) e inferência de Machine Learning/LLM para categorização financeira. Uma única linguagem geraria compromissos severos de performance ou produtividade; por outro lado, poliglotismo irrestrito causaria fragmentação operacional.
- **Decisão**:
  1. Adotar **Poliglotismo Restrito** limitado a **5 stacks homologadas**:
     - **Java 25 LTS (Spring Boot 3.4+ com Virtual Threads)**: Core Ledger, Cartões, Orçamento, Conciliação e Notificações.
     - **Golang 1.24+**: Ingestão BFF, parsing de PDFs em memória RAM (`bytes.Reader`), Scraper SEFAZ NFC-e e Motor de Forecast.
     - **Python 3.12+ (FastAPI / Lambda Arm64 + ONNX/LLM)**: Pipeline inteligente de categorização em 3 camadas.
     - **Next.js 15 (TypeScript)**: Portal Web executivo, SaaS Admin e Central de Perfil/Família.
     - **Kotlin (Jetpack Compose + Room/SQLCipher)**: Aplicativo mobile Android com suporte nativo offline-first.
  2. Obrigar o padrão **Hexagonal Architecture (Ports & Adapters)** em todos os serviços de backend (`domain`, `application`, `adapters/inbound`, `adapters/outbound`), mantendo o núcleo de domínio 100% isento de dependências de frameworks.
- **Alternativas Consideradas**:
  - *Monocultura Java*: Descartada pelo overhead de memória no parsing massivo de PDFs/Scraping concorrente e menor fluidez nativa para pipelines ONNX/ML.
  - *Monocultura Node.js/TypeScript*: Descartada pela ausência de tipo decimal nativo de precisão arbitrária padrão na linguagem (`Number` IEEE 754 gera erros de ponto flutuante em centavos).
- **Consequências**:
  - **Positivas**: Cada workload opera em sua stack ótima; testes de domínio rodam em milissegundos sem subir containers; substituição de adaptadores sem impacto nas regras de negócio.
  - **Trade-offs**: Necessidade de templates padronizados de observabilidade (OpenTelemetry) e CI/CD para Java, Go e Python.

---

## ADR-002: Topologia Multi-Repo e Mapeamento 1:1 IaC

- **Status**: Aprovado (V2)
- **Contexto**: Em sistemas financeiros distribuídos, o acoplamento de múltiplos serviços em um único repositório sem ferramental pesado de build distribuído dificulta o controle de acesso granular (RBAC), aumenta o tempo de CI e mistura ciclos de release de contratos, infraestrutura e serviços de aplicação.
- **Decisão**:
  1. Estruturar a plataforma em **repositórios independentes** (Topologia Multi-Repo), onde cada unidade de deploy possui seu próprio repositório Git, pipeline de CI/CD, versionamento **SemVer 2.0.0** e histórico de auditoria.
  2. Centralizar esquemas de comunicação síncrona e assíncrona no repositório versionado `pfm-contracts` (OpenAPI 3.1, Protobuf v3, JSON Schema/Avro).
  3. Manter mapeamento **1:1 de repositórios de infraestrutura como código (`*-infra`)** além do `pfm-shared-infra` e `pfm-finops-manager-infra` (OpenTofu / Terraform + Helm), garantindo estado isolado (*isolated state file* no S3 + DynamoDB Lock) e permissões IAM de privilégio mínimo (*Least Privilege*).
- **Alternativas Consideradas**:
  - *Monorepo Único (Nx/Bazel)*: Descartado pela complexidade de manutenção de Bazel em ambiente poliglota (Java 25 + Go + Python + Kotlin + Next.js) e requisito de segregação de acesso entre equipes de Core Banking, IA e Infraestrutura.
- **Consequências**:
  - **Positivas**: Blast radius estritamente contido; pipelines de CI rápidos e específicos por stack; rollback automático independente por serviço.
  - **Trade-offs**: Atualizações de contrato exigem publicação de nova versão do `pfm-contracts` antes do consumo pelos serviços dependentes.

---

## ADR-003: Comunicação Híbrida REST HTTP/3 e gRPC

- **Status**: Aprovado (V2)
- **Contexto**: Clientes externos (navegadores Web e dispositivos móveis em redes móveis instáveis 4G/5G) necessitam de protocolos resilientes a perda de pacotes e amigáveis a firewalls/CDNs, enquanto a comunicação interna entre microsserviços exige baixa latência de serialização e tipagem estrita.
- **Decisão**:
  1. **Tráfego North-South (Cliente -> API Gateway)**: Expor APIs **RESTful sobre HTTP/3 (QUIC)** e HTTP/2 fallback, documentadas via **OpenAPI 3.1**, autenticadas com OAuth 2.1 / OIDC (JWT assinado via JWS RS256/ES256).
  2. **Tráfego East-West (Serviço -> Serviço Síncrono)**: Utilizar **gRPC sobre HTTP/2 com Protobuf v3** sobre Service Connect (`pfm.internal`) ou Service Mesh com mTLS, com tipos monetários representados explicitamente como estrutura decimal exata (`units` + `nanos` ou string canônica validada).
- **Alternativas Consideradas**:
  - *REST JSON Interno*: Descartado pelo maior custo de CPU em serialização/deserialização e ausência de contrato binário fortemente tipado entre Java, Go e Python.
  - *GraphQL no Gateway*: Descartado para operações de mutação contábil devido à complexidade de cache HTTP, rate-limiting por operação e auditoria de idempotência.
- **Consequências**:
  - **Positivas**: Redução de latência P99 nas chamadas internas em até 60%; multiplexação QUIC elimina *head-of-line blocking* no app mobile.
  - **Trade-offs**: O API Gateway realiza transcodificação ou roteamento estruturado para os serviços internos.

---

## ADR-004: Padrões de Resiliência Distribuída

- **Status**: Aprovado (V2)
- **Contexto**: A plataforma depende de sistemas externos altamente instáveis (portais estaduais da SEFAZ para consulta de NFC-e e provedores externos de LLM) e não pode permitir que lentidões externas degradem o Core Ledger ou bloqueiem o registro de transações do usuário.
- **Decisão**: Implementar defesa em profundidade com padrões explícitos de resiliência (Resilience4j no Java, middlewares nativos em Go/Python e políticas no Envoy/Service Mesh):
  1. **Idempotência Obrigatória**: Toda mutação exige cabeçalho `Idempotency-Key` (UUID v7), armazenado no Redis + PostgreSQL com TTL de 72h e validação de hash do payload.
  2. **Timeouts Estritos & Deadlines Propagados**: Propagação de `grpc-timeout` em toda a árvore de chamadas (máximo 2.000ms para chamadas síncronas internas).
  3. **Circuit Breaker**: Abertura do circuito quando a taxa de falha atingir $\ge 50\%$ em janela deslizante de 20 requisições (estado *Half-Open* após 30s).
  4. **Retry com Exponential Backoff + Full Jitter**: Máximo de 3 tentativas apenas para falhas transitórias de rede/5xx idempotentes (`base=200ms`, `factor=2.0`, `jitter=random`).
  5. **Bulkhead Isolation**: Pools de execução segregados para chamadas de IA (Camada 3 LLM) e SEFAZ Scraper, impedindo exaustão de conexões do Core Banking.
  6. **Rate Limiting**: Token Bucket por `tenant_id` no API Gateway.
- **Consequências**:
  - **Positivas**: Proteção contra falhas em cascata (*cascading failures*); degradação graciosa (se a SEFAZ ou o LLM cair, a transação é enfileirada ou categorizada como `NAO_CATEGORIZADO` sem erro para o cliente).
  - **Trade-offs**: Maior complexidade de testes de caos e calibração de limiares de observabilidade.

---

## ADR-005: Eventos Assíncronos com Kafka e Transactional Outbox

- **Status**: Aprovado (V2)
- **Contexto**: Quando um lançamento é registrado no Core Ledger ou uma fatura é processada, múltiplos sistemas precisam reagir (atualizar saldo de orçamento, disparar conciliação, categorizar via IA, enviar alertas). O problema de *Dual Write* (salvar no PostgreSQL e publicar no Kafka na mesma operação sem 2PC) pode gerar inconsistência de estado caso um dos dois falhe.
- **Decisão**:
  1. Adotar **Apache Kafka** (Upstash Serverless na fase inicial; MSK/Confluent/Strimzi em hiperescala) como backbone de eventos de domínio e integração, particionado obrigatoriamente por `tenant_id` para garantir ordenação estrita por cliente.
  2. Proibir publicação direta no broker dentro de transações de banco de dados. Utilizar o padrão **Transactional Outbox**: o serviço grava a entidade de domínio e o registro na tabela `outbox_events` na **mesma transação ACID local do PostgreSQL**.
  3. Capturar os eventos via relay assíncrono de baixa latência / CDC e publicar no Kafka com semântica *At-Least-Once* combinada a **Idempotent Consumers** (tabela `processed_events` com PK `event_id`).
  4. Configurar **Dead Letter Queues (DLQ)** padronizadas e cifradas (`<topic>.dlq`) após esgotamento de retentativas não-bloqueantes.
- **Consequências**:
  - **Positivas**: Eliminação matemática do problema de *Dual Write*; desacoplamento temporal entre serviços; capacidade de *replay* de eventos para reconstrução de projeções (CQRS).
  - **Trade-offs**: Consistência eventual entre escrita no Ledger e atualização do dashboard de orçamento (SLO de lag $< 2\text{s}$).

---

## ADR-006: Isolamento Multitenant PostgreSQL RLS e Envelope Encryption

- **Status**: Aprovado (V2)
- **Contexto**: Dados financeiros pessoais são altamente sensíveis (LGPD Art. 5º e diretrizes de segurança cibernética bancária). Um erro de programação em uma query SQL (esquecer `WHERE tenant_id = ?`) jamais pode expor transações de outro usuário. Além disso, faturas de cartão de crédito em PDF contêm dados pessoais sensíveis que não devem repousar em discos persistentes não-cifrados.
- **Decisão**:
  1. **PostgreSQL Row-Level Security (RLS) Obrigatório**: Todas as tabelas de domínio (incluindo `audit_log`) possuem coluna `tenant_id UUID NOT NULL` e política ativa `ENABLE ROW LEVEL SECURITY` + `FORCE ROW LEVEL SECURITY`. A política valida `tenant_id = current_setting('app.current_tenant_id')::uuid`, configurado pelo *Outbound Adapter* no início de cada transação a partir do claim verificado do token JWT/mTLS.
  2. **Envelope Encryption (KMS) & Crypto-Shredding**: Campos sensíveis (PII, identificadores fiscais, tokens de integração) são criptografados na camada de aplicação com **AES-256-GCM** utilizando *Data Encryption Keys (DEKs)* exclusivas por tenant, envelopadas por uma *Key Encryption Key (KEK)* gerenciada em HSM/KMS da nuvem (AWS KMS / Azure Key Vault / GCP Cloud KMS). O encerramento definitivo de conta destrói a DEK (*Crypto-Shredding*), tornando backups históricos matematicamente indecifráveis.
  3. **Zero-Disk PDF Parsing**: O serviço `pfm-ingestion-bff-go` processa faturas PDF exclusivamente em memória volátil (`bytes.Reader` em RAM com limite estrito de 15 MB por stream), zerando o buffer imediatamente após a extração das transações.
- **Consequências**:
  - **Positivas**: Isolamento criptográfico e lógico garantido pelo motor do banco de dados mesmo em caso de bug na query; superfície zero de vazamento de arquivos PDF em volumes de armazenamento.
  - **Trade-offs**: Overhead marginal de ~1-2ms na abertura de transação para `SET LOCAL app.current_tenant_id` e validação de RLS (mitigado por índices compostos iniciando por `(tenant_id, ...)`).

---

## ADR-007: Arquitetura Multicloud Well-Architected (AWS/Azure/GCP)

- **Status**: Aprovado (V2)
- **Contexto**: A plataforma deve poder operar em qualquer um dos três grandes provedores de nuvem pública (**AWS**, **Azure**, **GCP**) por exigências regulatórias de risco de concentração de terceiros (Resolução BCB nº 4.893) e otimização financeira (**FinOps**), sem reescrita de código de aplicação.
- **Decisão**:
  1. Utilizar containers **OCI imutáveis Distroless multi-arquitetura** (`linux/arm64` Graviton/Ampere e `linux/amd64`), portáveis entre compute serverless de entrada e Kubernetes certificado pela CNCF (EKS, AKS, GKE).
  2. Utilizar apenas protocolos abertos no código de aplicação: **PostgreSQL 16 Wire Protocol**, **Apache Kafka Protocol**, **Redis/Valkey Protocol**, **OpenTelemetry (OTLP)** e **S3-compatible Object Storage API**.
  3. Isolar integrações específicas de nuvem (como KMS e IAM Workload Identity) atrás de **Outbound Ports** da Arquitetura Hexagonal e módulos OpenTofu equivalentes por provedor.
  4. Adotar os 6 pilares do **Well-Architected Framework** (Excelência Operacional, Segurança, Confiabilidade, Eficiência de Performance, Otimização de Custos e Sustentabilidade) com SLO global de disponibilidade de **99,95%**, **RPO < 5 minutos** e **RTO < 30 minutos**.
- **Consequências**:
  - **Positivas**: Portabilidade comprovada entre AWS, Azure e GCP; aproveitamento de instâncias ARM64 e descontos de comprometimento (Savings Plans / Reserved Instances / CUDs).
  - **Trade-offs**: Proibição do uso direto de bancos proprietários sem protocolo aberto (ex.: DynamoDB ou CosmosDB Table API) no núcleo transacional.

---

## ADR-008: Compute Enxuto de Produção Inicial & Trilha de Hiperescala Kubernetes

- **Status**: Aprovado (**V3**)
- **Contexto**: Embora o Kubernetes gerenciado (EKS/AKS/GKE) seja o padrão-ouro para alta escala, o custo fixo de sustentação do Control Plane do Amazon EKS (**US$ 73,00/mês**) somado a nós de workers, ALBs dedicados e clusters Kafka/Redis gerenciados impõe um piso de **~US$ 114 a US$ 140/mês** mesmo com baixo tráfego. Na fase de produção inicial e primeiros milhares de usuários, esse custo fixo compromete a eficiência unitária (FinOps).
- **Decisão**:
  1. **Camada de Compute Enxuta Multi-Cloud para Produção Inicial (~US$ 12 a US$ 24/mês)**:
     - **AWS (Referência Primária)**: **Amazon ECS on Fargate Spot (`linux/arm64` Graviton)** com plano de controle gratuito (**US$ 0,00/mês**), tarefas enxutas (`0.25 vCPU / 0.5 GB RAM`) e **AWS Cloud Map / Service Connect (`pfm.internal`)** para descoberta gRPC/HTTP interna sem ALB interno.
     - **Equivalência Multi-Cloud**: **Azure Container Apps (ACA)** com consumo Serverless na Azure e **GCP Cloud Run (2ª Geração)** no Google Cloud.
  2. **Mensageria & Cache Serverless**:
     - **Upstash Kafka Serverless** e **Upstash Redis/Valkey Serverless** com cobrança estrita por requisição/mensagem (Free Tier inicial de 10.000 msgs/dia; US$ 0,00 a US$ 3,50/mês no piloto).
  3. **Persistência & Governança Noturna (`pfm-finops-manager`)**:
     - **Amazon RDS PostgreSQL 16 (`db.t4g.micro` Single-AZ)** integrado à Lambda `pfm-finops-manager` (park às 20h30 BRT / unpark às 06h00 BRT no piloto) e *circuit-breaker* de orçamento.
  4. **Trilha Explícita de Evolução para Hiperescala Kubernetes**:
     - Quando a plataforma atingir escala massiva (**milhares de tenants simultâneos / > 500 tenants ativos pagantes**, estimativa **~US$ 420/mês**), a infraestrutura é chaveada via OpenTofu (`compute_engine = "eks"`) para **Kubernetes (EKS / AKS / GKE) + Karpenter Spot + KEDA Autoscaling + Amazon Aurora / Cloud SQL HA + MSK/Confluent**.
     - A transição exige **zero alterações no código de aplicação**, pois 100% dos serviços empacotam imagens **Docker OCI Distroless (`linux/arm64`)**, utilizam protocolos abertos e mantêm os Helm Charts (`helm/`) versionados nos repositórios `*-infra`.
- **Alternativas Consideradas**:
  - *EKS desde o Dia 1*: Rejeitado pelo custo fixo ocioso de US$ 73/mês do Control Plane e maior complexidade operacional para a fase inicial.
  - *Monólito em EC2 única*: Rejeitado por violar o isolamento de deploy por domínio, escalabilidade independente e portabilidade OCI.
- **Consequências**:
  - **Positivas**: Redução de >80% no custo fixo inicial (**US$ 12–24/mês**); transição determinística e sem reescrita para Kubernetes quando o negócio escalar.
  - **Trade-offs**: Possibilidade de interrupções pontuais em tarefas Fargate Spot (mitigada por tasks idempotentes e fallback `FARGATE` On-Demand no Capacity Provider).

---

## ADR-009: Worker IA Serverless Event-Driven

- **Status**: Aprovado (**V3**)
- **Contexto**: O processamento de categorização semântica por IA (`pfm-ai-worker-python`), especialmente o fallback de camada L2 (ONNX) e L3 (Cloud LLM) durante importações em lote de faturas PDF e rajadas de cupons NFC-e, apresenta padrão de carga altamente intermitente (*bursty*). Manter containers Python com modelos ONNX carregados em memória 24x7 gera custo ocioso constante e exige dimensionamento para pico. Além disso, permitir que workers Python assíncronos abram conexões diretas ao PostgreSQL transacional pode esgotar o pool de conexões do Core Ledger durante rajadas.
- **Decisão**:
  1. **Execução Serverless Event-Driven (`AWS Lambda Arm64`)**:
     - Operar o `pfm-ai-worker-python` como função **AWS Lambda (`linux/arm64` Graviton2)** acionada por eventos (ou serviço ECS com `desired_count = 0` orientado a eventos Kafka/SQS), garantindo **custo US$ 0,00 em períodos ociosos** e escalabilidade horizontal instantânea em rajadas de importação.
  2. **Isolamento Estrito de Banco de Dados**:
     - O Worker IA é **estritamente proibido de abrir conexões diretas com o PostgreSQL** do Core Ledger (`pfm-core-ledger-java`).
     - Toda comunicação ocorre via **Arquitetura Hexagonal**: os adaptadores de entrada consomem eventos do **Kafka** (ou chamadas **gRPC** síncronas/assíncronas), executam o funil de 3 camadas (`L1 Cache Redis -> L2 ONNX Local -> L3 Cloud LLM Anonimizado`) e publicam o resultado categorizado de volta no **Kafka** / **gRPC** para persistência ACID e RLS pelo `pfm-core-ledger-java`.
- **Alternativas Consideradas**:
  - *Pod/Task Python 24x7 conectado diretamente ao PostgreSQL*: Descartado pelo custo contínuo de RAM ociosa e pelo risco de exaustão de conexões SQL e acoplamento de esquema.
- **Consequências**:
  - **Positivas**: Custo zero sem tráfego; proteção total do pool de conexões e das políticas RLS do PostgreSQL; desacoplamento limpo entre inferência de IA e escrituração contábil.
  - **Trade-offs**: Necessidade de empacotar o runtime ONNX enxuto na imagem/layer da Lambda Arm64 para manter *cold start* reduzido (< 800ms).

---

## ADR-010: Observabilidade Multi-Cloud Unificada & Auditoria Imutável

- **Status**: Aprovado (**V3**)
- **Contexto**: Em uma arquitetura distribuída, poliglota e multicloud (AWS ECS/Lambda, Azure Container Apps, GCP Cloud Run, Upstash Serverless), enviar 100% dos traces de sucesso e healthchecks para ferramentas SaaS de APM gera custos proibitivos de ingestão (explosão de cardinalidade e volume de spans). Paralelamente, requisitos regulatórios financeiros exigem trilha de auditoria imutável de toda operação sensível e rastreabilidade de mensagens falhadas sem expor PII.
- **Decisão**:
  1. **OpenTelemetry Collector com Tail-Based Sampling Inteligente**:
     - Todos os serviços instrumentam **OTLP/gRPC** nativo enviando para o **OpenTelemetry Collector**, que aplica:
       - *Filter Processor*: descarte de 100% do ruído de sondas (`/health`, `/healthz`, `/actuator/health`).
       - *Redaction Processor*: mascaramento automático de CPF, números de cartão, e-mails e tokens antes de qualquer exportação (`[REDACTED_PII]`).
       - *Tail-Based Sampling*: retenção de **100% dos traces com erro (`status=ERROR`) ou latência > 500ms**, e amostragem de apenas **5% a 10% dos traces de sucesso rápido**.
  2. **Visão Unificada Multi-Cloud (Datadog Unified Dashboard) & Qualidade (SonarCloud Portfolio)**:
     - Exportar métricas RED/USE, logs sanitizados e traces amostrados para o **Datadog Unified Dashboard**, correlacionando AWS, Azure e GCP em painéis por **jornada de negócio (`UC-01` a `UC-08`)** dentro do orçamento Free Tier / controlado.
     - Consolidar a governança de código estático, segurança (SAST) e cobertura de testes ($\ge 95\%$) no **SonarCloud Portfolio** em todos os repositórios.
  3. **Auditoria Imutável (`audit_log` + RLS) & DLQ Cifrada**:
     - Registrar todas as mutações críticas (alterações contábeis, trocas de plano SaaS, convites familiares, exportação LGPD e *Crypto-Shredding*) na tabela **`audit_log` estritamente append-only** (sem `UPDATE` ou `DELETE` permitidos para roles de aplicação), protegida por **PostgreSQL Row-Level Security (RLS)** e hash encadeado/timestamp imutável.
     - Persistir mensagens com falha definitiva em **Dead Letter Queues (DLQ) cifradas com KMS** (`<topic>.dlq`), mantendo payload protegido e passível de auditoria e *replay* seguro.
- **Consequências**:
  - **Positivas**: Redução de até 85% no custo de ingestão de APM sem perder visibilidade sobre 100% das falhas e gargalos (>500ms); conformidade auditável LGPD/BACEN.
  - **Trade-offs**: O OpenTelemetry Collector necessita de memória dedicada para manter a janela de decisão do *Tail-Based Sampling* (ex.: 10s de buffer de trace).

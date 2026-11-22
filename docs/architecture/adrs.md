# Registro de Decisoes Arquiteturais (ADRs V3)

Este documento consolida as **Architecture Decision Records (ADRs V3)** que governam a engenharia da plataforma **PFM Core Banking -- Production-Ready FinOps & Multi-Cloud Architecture**. Todas as decisoes seguem o formato padronizado de Michael Nygard estendido para ambientes regulados, orientados a FinOps e multicloud.

---

## Sumario Executivo de ADRs

| ID | Titulo da Decisao | Status | Versao | Escopo |
| :--- | :--- | :---: | :---: | :--- |
| **[ADR-001](#adr-001-poliglotismo-restrito-e-arquitetura-hexagonal)** | Poliglotismo Restrito & Arquitetura Hexagonal | Aprovado | V2 | Todos os Microsservicos & Apps |
| **[ADR-002](#adr-002-topologia-multi-repo-e-mapeamento-11-iac)** | Topologia Multi-Repo & Mapeamento 1:1 IaC | Aprovado | V2 | Governanca de Codigo & CI/CD |
| **[ADR-003](#adr-003-comunicacao-hibrida-rest-http3-e-grpc)** | Comunicacao Hibrida: REST HTTP/3 (Edge) & gRPC (East-West) | Aprovado | V2 | APIs, Contratos & Service Mesh |
| **[ADR-004](#adr-004-padroes-de-resiliencia-distribuida)** | Padroes de Resiliencia Distribuida & Degradacao Graciosa | Aprovado | V2 | Integracoes Externas & Core |
| **[ADR-005](#adr-005-eventos-assincronos-com-kafka-e-transactional-outbox)** | Eventos Assincronos com Apache Kafka & Transactional Outbox | Aprovado | V2 | Mensageria & Consistencia Eventual |
| **[ADR-006](#adr-006-isolamento-multitenant-postgresql-rls-e-envelope-encryption)** | Isolamento Multitenant: PostgreSQL RLS & Envelope Encryption | Aprovado | V2 | Banco de Dados, Seguranca & LGPD |
| **[ADR-007](#adr-007-arquitetura-multicloud-well-architected-awsazuregcp)** | Arquitetura Multicloud Well-Architected (AWS / Azure / GCP) | Aprovado | V2 | Infraestrutura, SRE & FinOps |
| **[ADR-008](#adr-008-compute-enxuto-de-producao-inicial-trilha-de-hiperescala-kubernetes)** | Compute Enxuto de Producao Inicial & Trilha de Hiperescala Kubernetes | Aprovado | **V3** | ECS Fargate Spot / ACA / Cloud Run $\rightarrow$ K8s |
| **[ADR-009](#adr-009-worker-ia-serverless-event-driven)** | Worker IA Serverless Event-Driven (AWS Lambda Arm64) | Aprovado | **V3** | `pfm-ai-worker-python`, Kafka & Hexagonal |
| **[ADR-010](#adr-010-observabilidade-multi-cloud-unificada-auditoria-imutavel)** | Observabilidade Multi-Cloud Unificada & Auditoria Imutavel | Aprovado | **V3** | OTel Tail Sampling, Datadog, SonarCloud & RLS |

---

## ADR-001: Poliglotismo Restrito e Arquitetura Hexagonal

- **Status**: Aprovado (V2)
- **Contexto**: A plataforma PFM Core Banking possui requisitos heterogeneos que variam desde escrituracao contabil ACID com regras estritas de arredondamento ate scraping de notas fiscais (NFC-e), parsing de faturas PDF em memoria (sem escrita em disco) e inferencia de Machine Learning/LLM para categorizacao financeira. Uma unica linguagem geraria compromissos severos de performance ou produtividade; por outro lado, poliglotismo irrestrito causaria fragmentacao operacional.
- **Decisao**:
  1. Adotar **Poliglotismo Restrito** limitado a **5 stacks homologadas**:
     - **Java 25 LTS (Spring Boot 3.4+ com Virtual Threads)**: Core Ledger, Cartoes, Orcamento, Conciliacao e Notificacoes.
     - **Golang 1.24+**: Ingestao BFF, parsing de PDFs em memoria RAM (`bytes.Reader`), Scraper SEFAZ NFC-e e Motor de Forecast.
     - **Python 3.12+ (FastAPI / Lambda Arm64 + ONNX/LLM)**: Pipeline inteligente de categorizacao em 3 camadas.
     - **Next.js 15 (TypeScript)**: Portal Web executivo, SaaS Admin e Central de Perfil/Familia.
     - **Kotlin (Jetpack Compose + Room/SQLCipher)**: Aplicativo mobile Android com suporte nativo offline-first.
  2. Obrigar o padrao **Hexagonal Architecture (Ports & Adapters)** em todos os servicos de backend (`domain`, `application`, `adapters/inbound`, `adapters/outbound`), mantendo o nucleo de dominio 100% isento de dependencias de frameworks.
- **Alternativas Consideradas**:
  - *Monocultura Java*: Descartada pelo overhead de memoria no parsing massivo de PDFs/Scraping concorrente e menor fluidez nativa para pipelines ONNX/ML.
  - *Monocultura Node.js/TypeScript*: Descartada pela ausencia de tipo decimal nativo de precisao arbitraria padrao na linguagem (`Number` IEEE 754 gera erros de ponto flutuante em centavos).
- **Consequencias**:
  - **Positivas**: Cada workload opera em sua stack otima; testes de dominio rodam em milissegundos sem subir containers; substituicao de adaptadores sem impacto nas regras de negocio.
  - **Trade-offs**: Necessidade de templates padronizados de observabilidade (OpenTelemetry) e CI/CD para Java, Go e Python.

---

## ADR-002: Topologia Multi-Repo e Mapeamento 1:1 IaC

- **Status**: Aprovado (V2)
- **Contexto**: Em sistemas financeiros distribuidos, o acoplamento de multiplos servicos em um unico repositorio sem ferramental pesado de build distribuido dificulta o controle de acesso granular (RBAC), aumenta o tempo de CI e mistura ciclos de release de contratos, infraestrutura e servicos de aplicacao.
- **Decisao**:
  1. Estruturar a plataforma em **repositorios independentes** (Topologia Multi-Repo), onde cada unidade de deploy possui seu proprio repositorio Git, pipeline de CI/CD, versionamento **SemVer 2.0.0** e historico de auditoria.
  2. Centralizar esquemas de comunicacao sincrona e assincrona no repositorio versionado `pfm-contracts` (OpenAPI 3.1, Protobuf v3, JSON Schema/Avro).
  3. Manter mapeamento **1:1 de repositorios de infraestrutura como codigo (`*-infra`)** alem do `pfm-shared-infra` e `pfm-finops-manager-infra` (OpenTofu / Terraform + Helm), garantindo estado isolado (*isolated state file* no S3 + DynamoDB Lock) e permissoes IAM de privilegio minimo (*Least Privilege*).
- **Alternativas Consideradas**:
  - *Monorepo Unico (Nx/Bazel)*: Descartado pela complexidade de manutencao de Bazel em ambiente poliglota (Java 25 + Go + Python + Kotlin + Next.js) e requisito de segregacao de acesso entre equipes de Core Banking, IA e Infraestrutura.
- **Consequencias**:
  - **Positivas**: Blast radius estritamente contido; pipelines de CI rapidos e especificos por stack; rollback automatico independente por servico.
  - **Trade-offs**: Atualizacoes de contrato exigem publicacao de nova versao do `pfm-contracts` antes do consumo pelos servicos dependentes.

---

## ADR-003: Comunicacao Hibrida REST HTTP/3 e gRPC

- **Status**: Aprovado (V2)
- **Contexto**: Clientes externos (navegadores Web e dispositivos moveis em redes moveis instaveis 4G/5G) necessitam de protocolos resilientes a perda de pacotes e amigaveis a firewalls/CDNs, enquanto a comunicacao interna entre microsservicos exige baixa latencia de serializacao e tipagem estrita.
- **Decisao**:
  1. **Trafego North-South (Cliente -> API Gateway)**: Expor APIs **RESTful sobre HTTP/3 (QUIC)** e HTTP/2 fallback, documentadas via **OpenAPI 3.1**, autenticadas com OAuth 2.1 / OIDC (JWT assinado via JWS RS256/ES256).
  2. **Trafego East-West (Servico -> Servico Sincrono)**: Utilizar **gRPC sobre HTTP/2 com Protobuf v3** sobre Service Connect (`pfm.internal`) ou Service Mesh com mTLS, com tipos monetarios representados explicitamente como estrutura decimal exata (`units` + `nanos` ou string canonica validada).
- **Alternativas Consideradas**:
  - *REST JSON Interno*: Descartado pelo maior custo de CPU em serializacao/deserializacao e ausencia de contrato binario fortemente tipado entre Java, Go e Python.
  - *GraphQL no Gateway*: Descartado para operacoes de mutacao contabil devido a complexidade de cache HTTP, rate-limiting por operacao e auditoria de idempotencia.
- **Consequencias**:
  - **Positivas**: Reducao de latencia P99 nas chamadas internas em ate 60%; multiplexacao QUIC elimina *head-of-line blocking* no app mobile.
  - **Trade-offs**: O API Gateway realiza transcodificacao ou roteamento estruturado para os servicos internos.

---

## ADR-004: Padroes de Resiliencia Distribuida

- **Status**: Aprovado (V2)
- **Contexto**: A plataforma depende de sistemas externos altamente instaveis (portais estaduais da SEFAZ para consulta de NFC-e e provedores externos de LLM) e nao pode permitir que lentidoes externas degradem o Core Ledger ou bloqueiem o registro de transacoes do usuario.
- **Decisao**: Implementar defesa em profundidade com padroes explicitos de resiliencia (Resilience4j no Java, middlewares nativos em Go/Python e politicas no Envoy/Service Mesh):
  1. **Idempotencia Obrigatoria**: Toda mutacao exige cabecalho `Idempotency-Key` (UUID v7), armazenado no Redis + PostgreSQL com TTL de 72h e validacao de hash do payload.
  2. **Timeouts Estritos & Deadlines Propagados**: Propagacao de `grpc-timeout` em toda a arvore de chamadas (maximo 2.000ms para chamadas sincronas internas).
  3. **Circuit Breaker**: Abertura do circuito quando a taxa de falha atingir $\ge 50\%$ em janela deslizante de 20 requisicoes (estado *Half-Open* apos 30s).
  4. **Retry com Exponential Backoff + Full Jitter**: Maximo de 3 tentativas apenas para falhas transitorias de rede/5xx idempotentes (`base=200ms`, `factor=2.0`, `jitter=random`).
  5. **Bulkhead Isolation**: Pools de execucao segregados para chamadas de IA (Camada 3 LLM) e SEFAZ Scraper, impedindo exaustao de conexoes do Core Banking.
  6. **Rate Limiting**: Token Bucket por `tenant_id` no API Gateway.
- **Consequencias**:
  - **Positivas**: Protecao contra falhas em cascata (*cascading failures*); degradacao graciosa (se a SEFAZ ou o LLM cair, a transacao e enfileirada ou categorizada como `NAO_CATEGORIZADO` sem erro para o cliente).
  - **Trade-offs**: Maior complexidade de testes de caos e calibracao de limiares de observabilidade.

---

## ADR-005: Eventos Assincronos com Kafka e Transactional Outbox

- **Status**: Aprovado (V2)
- **Contexto**: Quando um lancamento e registrado no Core Ledger ou uma fatura e processada, multiplos sistemas precisam reagir (atualizar saldo de orcamento, disparar conciliacao, categorizar via IA, enviar alertas). O problema de *Dual Write* (salvar no PostgreSQL e publicar no Kafka na mesma operacao sem 2PC) pode gerar inconsistencia de estado caso um dos dois falhe.
- **Decisao**:
  1. Adotar **Apache Kafka** (Upstash Serverless na fase inicial; MSK/Confluent/Strimzi em hiperescala) como backbone de eventos de dominio e integracao, particionado obrigatoriamente por `tenant_id` para garantir ordenacao estrita por cliente.
  2. Proibir publicacao direta no broker dentro de transacoes de banco de dados. Utilizar o padrao **Transactional Outbox**: o servico grava a entidade de dominio e o registro na tabela `outbox_events` na **mesma transacao ACID local do PostgreSQL**.
  3. Capturar os eventos via relay assincrono de baixa latencia / CDC e publicar no Kafka com semantica *At-Least-Once* combinada a **Idempotent Consumers** (tabela `processed_events` com PK `event_id`).
  4. Configurar **Dead Letter Queues (DLQ)** padronizadas e cifradas (`<topic>.dlq`) apos esgotamento de retentativas nao-bloqueantes.
- **Consequencias**:
  - **Positivas**: Eliminacao matematica do problema de *Dual Write*; desacoplamento temporal entre servicos; capacidade de *replay* de eventos para reconstrucao de projecoes (CQRS).
  - **Trade-offs**: Consistencia eventual entre escrita no Ledger e atualizacao do dashboard de orcamento (SLO de lag $< 2\text{s}$).

---

## ADR-006: Isolamento Multitenant PostgreSQL RLS e Envelope Encryption

- **Status**: Aprovado (V2)
- **Contexto**: Dados financeiros pessoais sao altamente sensiveis (LGPD Art. 5o e diretrizes de seguranca cibernetica bancaria). Um erro de programacao em uma query SQL (esquecer `WHERE tenant_id = ?`) jamais pode expor transacoes de outro usuario. Alem disso, faturas de cartao de credito em PDF contem dados pessoais sensiveis que nao devem repousar em discos persistentes nao-cifrados.
- **Decisao**:
  1. **PostgreSQL Row-Level Security (RLS) Obrigatorio**: Todas as tabelas de dominio (incluindo `audit_log`) possuem coluna `tenant_id UUID NOT NULL` e politica ativa `ENABLE ROW LEVEL SECURITY` + `FORCE ROW LEVEL SECURITY`. A politica valida `tenant_id = current_setting('app.current_tenant_id')::uuid`, configurado pelo *Outbound Adapter* no inicio de cada transacao a partir do claim verificado do token JWT/mTLS.
  2. **Envelope Encryption (KMS) & Crypto-Shredding**: Campos sensiveis (PII, identificadores fiscais, tokens de integracao) sao criptografados na camada de aplicacao com **AES-256-GCM** utilizando *Data Encryption Keys (DEKs)* exclusivas por tenant, envelopadas por uma *Key Encryption Key (KEK)* gerenciada em HSM/KMS da nuvem (AWS KMS / Azure Key Vault / GCP Cloud KMS). O encerramento definitivo de conta destroi a DEK (*Crypto-Shredding*), tornando backups historicos matematicamente indecifraveis.
  3. **Zero-Disk PDF Parsing**: O servico `pfm-ingestion-bff-go` processa faturas PDF exclusivamente em memoria volatil (`bytes.Reader` em RAM com limite estrito de 15 MB por stream), zerando o buffer imediatamente apos a extracao das transacoes.
- **Consequencias**:
  - **Positivas**: Isolamento criptografico e logico garantido pelo motor do banco de dados mesmo em caso de bug na query; superficie zero de vazamento de arquivos PDF em volumes de armazenamento.
  - **Trade-offs**: Overhead marginal de ~1-2ms na abertura de transacao para `SET LOCAL app.current_tenant_id` e validacao de RLS (mitigado por indices compostos iniciando por `(tenant_id, ...)`).

---

## ADR-007: Arquitetura Multicloud Well-Architected (AWS/Azure/GCP)

- **Status**: Aprovado (V2)
- **Contexto**: A plataforma deve poder operar em qualquer um dos tres grandes provedores de nuvem publica (**AWS**, **Azure**, **GCP**) por exigencias regulatorias de risco de concentracao de terceiros (Resolucao BCB no 4.893) e otimizacao financeira (**FinOps**), sem reescrita de codigo de aplicacao.
- **Decisao**:
  1. Utilizar containers **OCI imutaveis Distroless multi-arquitetura** (`linux/arm64` Graviton/Ampere e `linux/amd64`), portaveis entre compute serverless de entrada e Kubernetes certificado pela CNCF (EKS, AKS, GKE).
  2. Utilizar apenas protocolos abertos no codigo de aplicacao: **PostgreSQL 16 Wire Protocol**, **Apache Kafka Protocol**, **Redis/Valkey Protocol**, **OpenTelemetry (OTLP)** e **S3-compatible Object Storage API**.
  3. Isolar integracoes especificas de nuvem (como KMS e IAM Workload Identity) atras de **Outbound Ports** da Arquitetura Hexagonal e modulos OpenTofu equivalentes por provedor.
  4. Adotar os 6 pilares do **Well-Architected Framework** (Excelencia Operacional, Seguranca, Confiabilidade, Eficiencia de Performance, Otimizacao de Custos e Sustentabilidade) com SLO global de disponibilidade de **99,95%**, **RPO < 5 minutos** e **RTO < 30 minutos**.
- **Consequencias**:
  - **Positivas**: Portabilidade comprovada entre AWS, Azure e GCP; aproveitamento de instancias ARM64 e descontos de comprometimento (Savings Plans / Reserved Instances / CUDs).
  - **Trade-offs**: Proibicao do uso direto de bancos proprietarios sem protocolo aberto (ex.: DynamoDB ou CosmosDB Table API) no nucleo transacional.

---

## ADR-008: Compute Enxuto de Producao Inicial & Trilha de Hiperescala Kubernetes

- **Status**: Aprovado (**V3**)
- **Contexto**: Embora o Kubernetes gerenciado (EKS/AKS/GKE) seja o padrao-ouro para alta escala, o custo fixo de sustentacao do Control Plane do Amazon EKS (**US$ 73,00/mes**) somado a nos de workers, ALBs dedicados e clusters Kafka/Redis gerenciados impoe um piso de **~US$ 114 a US$ 140/mes** mesmo com baixo trafego. Na fase de producao inicial e primeiros milhares de usuarios, esse custo fixo compromete a eficiencia unitaria (FinOps).
- **Decisao**:
  1. **Camada de Compute Enxuta Multi-Cloud para Producao Inicial (~US$ 12 a US$ 24/mes)**:
     - **AWS (Referencia Primaria)**: **Amazon ECS on Fargate Spot (`linux/arm64` Graviton)** com plano de controle gratuito (**US$ 0,00/mes**), tarefas enxutas (`0.25 vCPU / 0.5 GB RAM`) e **AWS Cloud Map / Service Connect (`pfm.internal`)** para descoberta gRPC/HTTP interna sem ALB interno.
     - **Equivalencia Multi-Cloud**: **Azure Container Apps (ACA)** com consumo Serverless na Azure e **GCP Cloud Run (2a Geracao)** no Google Cloud.
  2. **Mensageria & Cache Serverless**:
     - **Upstash Kafka Serverless** e **Upstash Redis/Valkey Serverless** com cobranca estrita por requisicao/mensagem (Free Tier inicial de 10.000 msgs/dia; US$ 0,00 a US$ 3,50/mes no piloto).
  3. **Persistencia & Governanca Noturna (`pfm-finops-manager`)**:
     - **Amazon RDS PostgreSQL 16 (`db.t4g.micro` Single-AZ)** integrado a Lambda `pfm-finops-manager` (park as 20h30 BRT / unpark as 06h00 BRT no piloto) e *circuit-breaker* de orcamento.
  4. **Trilha Explicita de Evolucao para Hiperescala Kubernetes**:
     - Quando a plataforma atingir escala massiva (**milhares de tenants simultaneos / > 500 tenants ativos pagantes**, estimativa **~US$ 420/mes**), a infraestrutura e chaveada via OpenTofu (`compute_engine = "eks"`) para **Kubernetes (EKS / AKS / GKE) + Karpenter Spot + KEDA Autoscaling + Amazon Aurora / Cloud SQL HA + MSK/Confluent**.
     - A transicao exige **zero alteracoes no codigo de aplicacao**, pois 100% dos servicos empacotam imagens **Docker OCI Distroless (`linux/arm64`)**, utilizam protocolos abertos e mantem os Helm Charts (`helm/`) versionados nos repositorios `*-infra`.
- **Alternativas Consideradas**:
  - *EKS desde o Dia 1*: Rejeitado pelo custo fixo ocioso de US$ 73/mes do Control Plane e maior complexidade operacional para a fase inicial.
  - *Monolito em EC2 unica*: Rejeitado por violar o isolamento de deploy por dominio, escalabilidade independente e portabilidade OCI.
- **Consequencias**:
  - **Positivas**: Reducao de >80% no custo fixo inicial (**US$ 12--24/mes**); transicao deterministica e sem reescrita para Kubernetes quando o negocio escalar.
  - **Trade-offs**: Possibilidade de interrupcoes pontuais em tarefas Fargate Spot (mitigada por tasks idempotentes e fallback `FARGATE` On-Demand no Capacity Provider).

---

## ADR-009: Worker IA Serverless Event-Driven

- **Status**: Aprovado (**V3**)
- **Contexto**: O processamento de categorizacao semantica por IA (`pfm-ai-worker-python`), especialmente o fallback de camada L2 (ONNX) e L3 (Cloud LLM) durante importacoes em lote de faturas PDF e rajadas de cupons NFC-e, apresenta padrao de carga altamente intermitente (*bursty*). Manter containers Python com modelos ONNX carregados em memoria 24x7 gera custo ocioso constante e exige dimensionamento para pico. Alem disso, permitir que workers Python assincronos abram conexoes diretas ao PostgreSQL transacional pode esgotar o pool de conexoes do Core Ledger durante rajadas.
- **Decisao**:
  1. **Execucao Serverless Event-Driven (`AWS Lambda Arm64`)**:
     - Operar o `pfm-ai-worker-python` como funcao **AWS Lambda (`linux/arm64` Graviton2)** acionada por eventos (ou servico ECS com `desired_count = 0` orientado a eventos Kafka/SQS), garantindo **custo US$ 0,00 em periodos ociosos** e escalabilidade horizontal instantanea em rajadas de importacao.
  2. **Isolamento Estrito de Banco de Dados**:
     - O Worker IA e **estritamente proibido de abrir conexoes diretas com o PostgreSQL** do Core Ledger (`pfm-core-ledger-java`).
     - Toda comunicacao ocorre via **Arquitetura Hexagonal**: os adaptadores de entrada consomem eventos do **Kafka** (ou chamadas **gRPC** sincronas/assincronas), executam o funil de 3 camadas (`L1 Cache Redis -> L2 ONNX Local -> L3 Cloud LLM Anonimizado`) e publicam o resultado categorizado de volta no **Kafka** / **gRPC** para persistencia ACID e RLS pelo `pfm-core-ledger-java`.
- **Alternativas Consideradas**:
  - *Pod/Task Python 24x7 conectado diretamente ao PostgreSQL*: Descartado pelo custo continuo de RAM ociosa e pelo risco de exaustao de conexoes SQL e acoplamento de esquema.
- **Consequencias**:
  - **Positivas**: Custo zero sem trafego; protecao total do pool de conexoes e das politicas RLS do PostgreSQL; desacoplamento limpo entre inferencia de IA e escrituracao contabil.
  - **Trade-offs**: Necessidade de empacotar o runtime ONNX enxuto na imagem/layer da Lambda Arm64 para manter *cold start* reduzido (< 800ms).

---

## ADR-010: Observabilidade Multi-Cloud Unificada & Auditoria Imutavel

- **Status**: Aprovado (**V3**)
- **Contexto**: Em uma arquitetura distribuida, poliglota e multicloud (AWS ECS/Lambda, Azure Container Apps, GCP Cloud Run, Upstash Serverless), enviar 100% dos traces de sucesso e healthchecks para ferramentas SaaS de APM gera custos proibitivos de ingestao (explosao de cardinalidade e volume de spans). Paralelamente, requisitos regulatorios financeiros exigem trilha de auditoria imutavel de toda operacao sensivel e rastreabilidade de mensagens falhadas sem expor PII.
- **Decisao**:
  1. **OpenTelemetry Collector com Tail-Based Sampling Inteligente**:
     - Todos os servicos instrumentam **OTLP/gRPC** nativo enviando para o **OpenTelemetry Collector**, que aplica:
       - *Filter Processor*: descarte de 100% do ruido de sondas (`/health`, `/healthz`, `/actuator/health`).
       - *Redaction Processor*: mascaramento automatico de CPF, numeros de cartao, e-mails e tokens antes de qualquer exportacao (`[REDACTED_PII]`).
       - *Tail-Based Sampling*: retencao de **100% dos traces com erro (`status=ERROR`) ou latencia > 500ms**, e amostragem de apenas **5% a 10% dos traces de sucesso rapido**.
  2. **Visao Unificada Multi-Cloud (Datadog Unified Dashboard) & Qualidade (SonarCloud Portfolio)**:
     - Exportar metricas RED/USE, logs sanitizados e traces amostrados para o **Datadog Unified Dashboard**, correlacionando AWS, Azure e GCP em paineis por **jornada de negocio (`UC-01` a `UC-08`)** dentro do orcamento Free Tier / controlado.
     - Consolidar a governanca de codigo estatico, seguranca (SAST) e cobertura de testes ($\ge 95\%$) no **SonarCloud Portfolio** em todos os repositorios.
  3. **Auditoria Imutavel (`audit_log` + RLS) & DLQ Cifrada**:
     - Registrar todas as mutacoes criticas (alteracoes contabeis, trocas de plano SaaS, convites familiares, exportacao LGPD e *Crypto-Shredding*) na tabela **`audit_log` estritamente append-only** (sem `UPDATE` ou `DELETE` permitidos para roles de aplicacao), protegida por **PostgreSQL Row-Level Security (RLS)** e hash encadeado/timestamp imutavel.
     - Persistir mensagens com falha definitiva em **Dead Letter Queues (DLQ) cifradas com KMS** (`<topic>.dlq`), mantendo payload protegido e passivel de auditoria e *replay* seguro.
- **Consequencias**:
  - **Positivas**: Reducao de ate 85% no custo de ingestao de APM sem perder visibilidade sobre 100% das falhas e gargalos (>500ms); conformidade auditavel LGPD/BACEN.
  - **Trade-offs**: O OpenTelemetry Collector necessita de memoria dedicada para manter a janela de decisao do *Tail-Based Sampling* (ex.: 10s de buffer de trace).

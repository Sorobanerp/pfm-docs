# Registro de Decisões Arquiteturais (ADRs V2)

Este documento consolida as **Architecture Decision Records (ADRs V2)** que governam a engenharia da plataforma **PFM Core Banking**. Todas as decisões seguem o formato padronizado de Michael Nygard estendido para ambientes regulados e multicloud.

---

## Sumário Executivo de ADRs

| ID | Título da Decisão | Status | Data | Escopo |
| :--- | :--- | :---: | :---: | :--- |
| **[ADR-001](#adr-001-poliglotismo-restrito-e-arquitetura-hexagonal)** | Poliglotismo Restrito & Arquitetura Hexagonal | Aprovado | 2026-11 | Todos os Microsserviços & Apps |
| **[ADR-002](#adr-002-topologia-multi-repo-e-mapeamento-11-iac)** | Topologia Multi-Repo & Mapeamento 1:1 IaC | Aprovado | 2026-11 | Governança de Código & CI/CD |
| **[ADR-003](#adr-003-comunicacao-hibrida-rest-http3-e-grpc)** | Comunicação Híbrida: REST HTTP/3 (Edge) & gRPC (East-West) | Aprovado | 2026-11 | APIs, Contratos & Service Mesh |
| **[ADR-004](#adr-004-padroes-de-resiliencia-distribuida)** | Padrões de Resiliência Distribuída & Degradação Graciosa | Aprovado | 2026-11 | Integrações Externas & Core |
| **[ADR-005](#adr-005-eventos-assincronos-com-kafka-e-transactional-outbox)** | Eventos Assíncronos com Apache Kafka & Transactional Outbox | Aprovado | 2026-11 | Mensageria & Consistência Eventual |
| **[ADR-006](#adr-006-isolamento-multitenant-postgresql-rls-e-envelope-encryption)** | Isolamento Multitenant: PostgreSQL RLS & Envelope Encryption | Aprovado | 2026-11 | Banco de Dados, Segurança & LGPD |
| **[ADR-007](#adr-007-arquitetura-multicloud-well-architected-awsazuregcp)** | Arquitetura Multicloud Well-Architected (AWS / Azure / GCP) | Aprovado | 2026-11 | Infraestrutura, SRE & FinOps |

---

## ADR-001: Poliglotismo Restrito e Arquitetura Hexagonal

- **Status**: Aprovado (V2)
- **Contexto**: A plataforma PFM Core Banking possui requisitos heterogêneos que variam desde escrituração contábil ACID com regras estritas de arredondamento até scraping de notas fiscais (NFC-e), parsing de faturas PDF em memória (sem escrita em disco) e inferência de Machine Learning/LLM para categorização financeira. Uma única linguagem geraria compromissos severos de performance ou produtividade; por outro lado, poliglotismo irrestrito causaria fragmentação operacional.
- **Decisão**:
  1. Adotar **Poliglotismo Restrito** limitado a **5 stacks homologadas**:
     - **Java 25 LTS (Spring Boot 3.4+ com Virtual Threads)**: Core Ledger, Cartões, Orçamento, Conciliação e Notificações.
     - **Golang 1.24+**: Ingestão e parsing de PDFs em memória RAM (`tmpfs`/`bytes.Buffer`) e Scraper SEFAZ NFC-e de alta concorrência.
     - **Python 3.12+ (FastAPI + ONNX/LLM)**: Pipeline inteligente de categorização em 3 camadas.
     - **Next.js 15 (TypeScript)**: Portal Web executivo e analítico.
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
  1. Estruturar a plataforma em **14 repositórios independentes** (Topologia Multi-Repo), onde cada unidade de deploy possui seu próprio repositório Git, pipeline de CI/CD, versionamento SemVer e histórico de auditoria.
  2. Centralizar esquemas de comunicação síncrona e assíncrona no repositório versionado `pfm-contracts` (OpenAPI 3.1, Protobuf v3, JSON Schema/Avro).
  3. Manter mapeamento **1:1 de módulos de infraestrutura como código** no repositório `pfm-infra-iac` (Terraform / OpenTofu + Helm), garantindo que cada microsserviço possua estado isolado (*isolated state file*) e permissões IAM de privilégio mínimo (*Least Privilege*).
- **Alternativas Consideradas**:
  - *Monorepo Único (Nx/Bazel)*: Descartado pela complexidade de manutenção de Bazel em ambiente poliglota (Java 25 + Go + Python + Kotlin + Next.js) e requisito de segregação de acesso entre equipes de Core Banking, IA e Infraestrutura.
- **Consequências**:
  - **Positivas**: Blast radius estritamente contido; pipelines de CI rápidos e específicos por stack; auditoria de mudanças simplificada para compliance.
  - **Trade-offs**: Atualizações de contrato exigem publicação de nova versão do `pfm-contracts` antes do consumo pelos serviços dependentes.

---

## ADR-003: Comunicação Híbrida REST HTTP/3 e gRPC

- **Status**: Aprovado (V2)
- **Contexto**: Clientes externos (navegadores Web e dispositivos móveis em redes móveis instáveis 4G/5G) necessitam de protocolos resilientes a perda de pacotes e amigáveis a firewalls/CDNs, enquanto a comunicação interna entre microsserviços (ex.: Ledger consultando Categorizer ou Reconcile consultando Cards) exige baixa latência de serialização e tipagem estrita.
- **Decisão**:
  1. **Tráfego North-South (Cliente -> API Gateway)**: Expor APIs **RESTful sobre HTTP/3 (QUIC)** e HTTP/2 fallback, documentadas via **OpenAPI 3.1**, autenticadas com OAuth 2.1 / OIDC (JWT assinado via JWS RS256/ES256).
  2. **Tráfego East-West (Serviço -> Serviço Síncrono)**: Utilizar **gRPC sobre HTTP/2 com Protobuf v3** e autenticação mútua **mTLS** gerenciada via Service Mesh (Istio / Linkerd), com tipos monetários representados explicitamente como estrutura decimal exata (`units` + `nanos` ou string canônica validada).
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
- **Contexto**: Quando um lançamento é registrado no `pfm-ledger-service` ou uma fatura é processada, múltiplos sistemas precisam reagir (atualizar saldo de orçamento no `pfm-budget-service`, disparar conciliação no `pfm-reconcile-service`, enviar alertas no `pfm-notification-service`). O problema de *Dual Write* (salvar no PostgreSQL e publicar no Kafka na mesma operação sem 2PC) pode gerar inconsistência de estado caso um dos dois falhe.
- **Decisão**:
  1. Adotar **Apache Kafka** como backbone de eventos de domínio e integração, particionado obrigatoriamente por `tenant_id` para garantir ordenação estrita por cliente.
  2. Proibir publicação direta no broker dentro de transações de banco de dados. Utilizar o padrão **Transactional Outbox**: o serviço grava a entidade de domínio e o registro na tabela `outbox_events` na **mesma transação ACID local do PostgreSQL**.
  3. Capturar os eventos via **CDC (Debezium)** ou relay assíncrono de baixa latência a partir do WAL do PostgreSQL e publicar no Kafka com semântica *At-Least-Once* combinada a **Idempotent Consumers** (tabela `processed_events` com PK `event_id`).
  4. Configurar **Dead Letter Queues (DLQ)** padronizadas (`<topic>.dlq`) após esgotamento de retentativas não-bloqueantes.
- **Consequências**:
  - **Positivas**: Eliminação matemática do problema de *Dual Write*; desacoplamento temporal entre serviços; capacidade de *replay* de eventos para reconstrução de projeções (CQRS).
  - **Trade-offs**: Consistência eventual entre escrita no Ledger e atualização do dashboard de orçamento (SLO de lag $< 1\text{s}$).

---

## ADR-006: Isolamento Multitenant PostgreSQL RLS e Envelope Encryption

- **Status**: Aprovado (V2)
- **Contexto**: Dados financeiros pessoais são altamente sensíveis (LGPD Art. 5º e diretrizes de segurança cibernética bancária). Um erro de programação em uma query SQL (esquecer `WHERE tenant_id = ?`) jamais pode expor transações de outro usuário. Além disso, faturas de cartão de crédito em PDF contêm dados pessoais sensíveis que não devem repousar em discos persistentes.
- **Decisão**:
  1. **PostgreSQL Row-Level Security (RLS) Obrigatório**: Todas as tabelas de domínio possuem coluna `tenant_id UUID NOT NULL` e política ativa `ENABLE ROW LEVEL SECURITY` + `FORCE ROW LEVEL SECURITY`. A política valida `tenant_id = current_setting('app.current_tenant_id')::uuid`, configurado pelo *Outbound Adapter* no início de cada transação a partir do claim verificado do token JWT/mTLS.
  2. **Envelope Encryption (KMS)**: Campos sensíveis (PII, identificadores fiscais, tokens de integração) são criptografados na camada de aplicação com **AES-256-GCM** utilizando *Data Encryption Keys (DEKs)* exclusivas por tenant, envelopadas por uma *Key Encryption Key (KEK)* gerenciada em HSM/KMS da nuvem (AWS KMS / Azure Key Vault / GCP Cloud KMS).
  3. **Zero-Disk PDF Parsing**: O serviço `pfm-ingestion-pdf-service` processa faturas PDF exclusivamente em memória volátil (`bytes.Reader` / `tmpfs` em RAM com limite estrito de 15 MB por stream), zerando o buffer imediatamente após a extração das transações.
- **Consequências**:
  - **Positivas**: Isolamento criptográfico e lógico garantido pelo motor do banco de dados mesmo em caso de bug na query; superfície zero de vazamento de arquivos PDF em volumes de armazenamento.
  - **Trade-offs**: Overhead marginal de ~1-2ms na abertura de transação para `SET LOCAL app.current_tenant_id` e validação de RLS (mitigado por índices compostos iniciando por `(tenant_id, ...)`).

---

## ADR-007: Arquitetura Multicloud Well-Architected (AWS/Azure/GCP)

- **Status**: Aprovado (V2)
- **Contexto**: A plataforma deve poder operar em qualquer um dos três grandes provedores de nuvem pública (**AWS**, **Azure**, **GCP**) por exigências regulatórias de risco de concentração de terceiros (Resolução BCB nº 4.893) e otimização financeira (**FinOps**), sem reescrita de código de aplicação.
- **Decisão**:
  1. Padronizar a camada de computação em **Kubernetes certificado pela CNCF** (EKS, AKS, GKE) utilizando containers OCI imutáveis multi-arquitetura (`linux/arm64` Graviton/Ampere e `linux/amd64`).
  2. Utilizar apenas protocolos abertos no código de aplicação: **PostgreSQL 16 Wire Protocol**, **Apache Kafka Protocol**, **Redis/Valkey Protocol**, **OpenTelemetry (OTLP)** e **S3-compatible Object Storage API**.
  3. Isolar integrações específicas de nuvem (como KMS e IAM Workload Identity) atrás de **Outbound Ports** da Arquitetura Hexagonal e módulos Terraform equivalentes por provedor no repositório `pfm-infra-iac`.
  4. Adotar os 6 pilares do **Well-Architected Framework** (Excelência Operacional, Segurança, Confiabilidade, Eficiência de Performance, Otimização de Custos e Sustentabilidade) com SLO global de disponibilidade de **99,95%**, **RPO < 5 minutos** e **RTO < 30 minutos**.
- **Consequências**:
  - **Positivas**: Portabilidade comprovada entre AWS, Azure e GCP; aproveitamento de instâncias ARM64 e descontos de comprometimento (Savings Plans / Reserved Instances / CUDs).
  - **Trade-offs**: Proibição do uso direto de bancos proprietários sem protocolo aberto (ex.: DynamoDB ou CosmosDB Table API) no núcleo transacional.

---

## ADR-008: ECS Fargate Spot (Arm64) + Upstash Kafka/Redis Serverless para Piloto de 3 Meses

- **Status**: Aprovado (Piloto V2.1)
- **Contexto**: A arquitetura enterprise da plataforma foi concebida sobre Kubernetes certificado (Amazon EKS) com nós Graviton Arm64 (`t4g.medium`). No entanto, o custo fixo de sustentação do plano de controle do EKS (US$ 73,00/mês a US$ 0,10/h) somado a nós EC2 Spot, Application Load Balancers dedicados, EBS e componentes auxiliares resulta em um piso orçamentário de **~US$ 114 a US$ 140 / mês**. Para o Piloto de 3 Meses com público familiar inicial (5 a 20 usuários), esse valor representa um overhead desnecessário de capacidade ociosa. Além disso, a manutenção de clusters Apache Kafka dedicados (MSK/Strimzi) e clusters ElastiCache Valkey/Redis impõe custos mínimos mesmo durante a madrugada sem transações ativas.
- **Decisão**:
  1. **Substituição Temporária do EKS por AWS ECS Fargate Spot (Arm64)**:
     - Adotar o **Amazon Elastic Container Service (ECS)** com o provedor de capacidade **Fargate Spot (`linux/arm64`)** para todos os microsserviços (`pfm-ingestion-bff-go`, `pfm-core-ledger-java`, `pfm-forecast-engine-go`, `pfm-ai-worker-python` e `pfm-web-nextjs`).
     - O plano de controle do ECS é gratuito (**US$ 0,00/mês**), eliminando integralmente os US$ 73/mês do EKS.
     - Tarefas dimensionadas com perfis enxutos (0.25 vCPU e 0.5 GB de RAM para Go/Python/Next.js; 0.5 vCPU e 1.0 GB de RAM para Java 25), usufruindo do desconto de ~70% do Fargate Spot.
     - Estimativa de computação ECS Fargate Spot: **US$ 3,50 a US$ 8,00 / mês**.
  2. **Backbone de Mensageria Serverless com Upstash Kafka**:
     - Utilizar instâncias **Upstash Serverless Kafka** com criptografia TLS e SASL/SCRAM.
     - O plano Free Tier contempla até 10.000 mensagens/dia sem custo fixo de instâncias; consumo excedente faturado sob demanda (US$ 0,60 por 100.000 mensagens).
     - Custo mensal estimado para o tráfego do piloto: **US$ 0,00 a US$ 2,00 / mês**.
  3. **Cache L1 & Lock de Idempotência com Upstash Redis/Valkey**:
     - Utilizar **Upstash Serverless Redis** com suporte total ao protocolo RESP3.
     - Free Tier de até 10.000 comandos/dia com latência submilisegundo e persistência automática.
     - Custo mensal estimado para o piloto: **US$ 0,00 a US$ 1,50 / mês**.
  4. **Persistência Relacional: Amazon RDS PostgreSQL (`db.t4g.micro`) com Parada Noturna**:
     - PostgreSQL 16 Single-AZ com 20 GB gp3 em `us-east-2`.
     - Integração com a Lambda `pfm-finops-manager` que suspende o banco automaticamente entre 20h30 e 06h00 BRT (economizando ~40% do custo de horas de computação).
     - Custo mensal estimado: **US$ 7,50 a US$ 12,00 / mês**.
  5. **Borda & Roteamento Unificado**:
     - Uso de um único **Application Load Balancer (ALB)** enxuto compartilhado com regras de path-routing (`/api/v1/*` para o BFF, `/` para o Next.js) ou integração direta com API Gateway HTTP API.
     - Custo mensal estimado: **US$ 1,50 a US$ 3,50 / mês**.
  6. **Custo Total Consolidado do Piloto de 3 Meses**:
     - **US$ 11,50 a US$ 24,00 / mês** (redução orçamentária superior a **80%** em relação ao piso do EKS).
  7. **Preservação de Padrões e Portabilidade para Kubernetes**:
     - 100% das imagens de container continuam construídas sobre bases **Google Container Tools Distroless** (`nonroot`), multi-arquitetura (`linux/arm64` nativo para Graviton).
     - Todos os Helm Charts (`helm/`) e módulos OpenTofu para EKS permanecem versionados nos repositórios `*-infra`, permitindo chavear a infraestrutura de volta para EKS via pipeline sem tocar em nenhuma linha de código da aplicação quando a base de clientes ultrapassar o volume de piloto.
- **Consequências**:
  - **Positivas**: Custo operacional compatível com bootstrapping e validação de produto; eliminação de ociosidade noturna; retenção integral dos padrões de segurança (Distroless, Non-Root, RLS, KMS).
  - **Trade-offs**: Possibilidade de *cold start* pontual em tarefas Fargate Spot reiniciadas; necessidade de acesso de saída seguro para o Upstash Serverless; desligamento do RDS durante a janela noturna de economia.


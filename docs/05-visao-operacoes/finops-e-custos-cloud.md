# 5.3. FinOps & Custos Cloud -- Centro Unico de Custos (USD + Estimativa BRL)

<span class="badge-green">Artefato 06 - Centro Unico de Custos Cloud</span>
<span class="badge-glow">Moeda de Faturamento: USD (US$) + Estimativa BRL (R$)</span>
<span class="badge-peach">Cambio de Referencia: 1 USD = R$ 5,80</span>

Este documento constitui o **Centro Unico de Custos de Infraestrutura Cloud** da plataforma **PFM Core Banking**. Conforme a governanca editorial do portal **Pulse Docs**, todas as tabelas abaixo apresentam os valores de faturamento em **Dolar Americano (`US$` / `USD`)** lado a lado com a **Estimativa em Real Brasileiro (`R$` / `BRL`)** considerando a taxa de cambio de referencia **`1 USD = R$ 5,80`**.

---

## 1. Arquitetura Enxuta de Producao Inicial na AWS (`us-east-2a/b`)

A Onda 1 (`pfm-shared-infra`) e a Onda 2 (`5 *-infra` + `pfm-finops-manager-infra`) foram provisionadas na regiao **AWS `us-east-2` (Ohio)** distribuindo as sub-redes em **2 Zonas de Disponibilidade (`us-east-2a` e `us-east-2b`)** com **0 clusters EKS** e **0 NAT Gateways**, eliminando custos ociosos de plano de controle e processamento de rede.

### Tabela Consolidada de Custos Mensais -- Estagio 1 (Producao Inicial / Piloto Enxuto)

| Recurso AWS / Serverless (`us-east-2`) | Especificacao Provisionada | Custo Mensal (USD) | Estimativa Mensal (BRL @ R$ 5,80) | Alavanca FinOps Aplicada |
| :--- | :--- | :---: | :---: | :--- |
| **VPC Multi-AZ (2 AZs `us-east-2a/b`)** | `vpc-0df15af468b702893`, 2 subnets publicas + 2 privadas, 0 NAT Gateways | **US$ 0,00** | **R$ 0,00** | Economia de `US$ 32,85/mes` (`R$ 190,53/mes`) ao eliminar NAT Gateway fixo |
| **Control Plane Orquestrador** | Cluster Amazon ECS `pfm-ecs-pilot` (substituindo EKS Control Plane) | **US$ 0,00** | **R$ 0,00** | Economia de `US$ 73,00/mes` (`R$ 423,40/mes`) vs. Amazon EKS (`DenyAllEKS` ativo) |
| **Service Discovery Interno gRPC** | AWS Cloud Map Private DNS Namespace `pfm.internal` | **US$ 0,50** | **R$ 2,90** | Substitui ALB interno pago (`US$ 16,40/mes` / `R$ 95,12/mes`) |
| **Compute Microsservicos (4 Servicos ECS)** | `FARGATE_SPOT` Arm64 (`0.25 vCPU / 0.5 GB`) com parada noturna (`pfm-finops-manager`) | **US$ 8,80 -- US$ 14,50** | **R$ 51,04 -- R$ 84,10** | Desconto de ~70% do Fargate Spot Arm64 + ~40% de reducao com parada noturna |
| **Worker IA (`pfm-ai-worker-python-prod`)** | AWS Lambda Arm64 (`python3.12`) + SQS DLQ | **US$ 0,00** | **R$ 0,00** | Coberto pelo AWS Lambda Free Tier (1M reqs/mes; custo zero ocioso) |
| **Banco de Dados (`pfm-core-ledger-prod`)** | Amazon RDS PostgreSQL 16 `db.t4g.micro` (Single-AZ + KMS + RLS) com parada noturna | **US$ 7,20 -- US$ 12,00** | **R$ 41,76 -- R$ 69,60** | Instancia Graviton2 `t4g.micro` pausada no periodo noturno (`20:30 -- 06:00 BRT`) |
| **Mensageria, Cache, KMS & S3** | Upstash Kafka/Redis Serverless + 1 Chave KMS (`alias/pfm-master-key`) + S3 | **US$ 1,50** | **R$ 8,70** | Chave KMS unica compartilhada (`US$ 1,00`) + S3/Upstash Pay-per-use |
| **TOTAL MENSAL (COM PARADA NOTURNA)** | **Operacao Diurna Completa + Shutdown Noturno** | **US$ 18,00 / mes** | **R$ 104,40 / mes** | **Meta `< US$ 24,00/mes` (`< R$ 139,20/mes`) cumprida com folga** |
| **TOTAL MENSAL (24x7 CONTINUO)** | **4 Tasks ECS Spot + RDS `db.t4g.micro` 24x7** | **US$ 23,50 -- US$ 33,60 / mes** | **R$ 136,30 -- R$ 194,88 / mes** | Sem necessidade de parada noturna para cargas continuas |

---

## 2. Trilha Evolutiva de Custos: Piloto Enxuto vs. Hiperescala Kubernetes (`ADR-008`)

A arquitetura evolui em 3 estagios sem reescrita de codigo de aplicacao, mantendo imagens OCI Distroless Arm64 e Helm Charts prontos para quando a receita SaaS justificar a mudanca de patamar:

| Estagio de Maturidade | Capacidade Alvo | Arquitetura de Compute & Dados | Custo Mensal (USD) | Estimativa Mensal (BRL @ R$ 5,80) | Custo Unitario por Tenant (USD / BRL) |
| :--- | :---: | :--- | :---: | :---: | :---: |
| **Estagio 1: Producao Inicial (Atual)** | Ate 50 familias / tenants | ECS Fargate Spot Arm64 (`pfm-ecs-pilot`) + Lambda IA + RDS `db.t4g.micro` + Cloud Map | **US$ 18,00 -- US$ 24,00 / mes** | **R$ 104,40 -- R$ 139,20 / mes** | **~US$ 0,48 (`~R$ 2,78`) / tenant** |
| **Estagio 2: Escala Comercial** | 100 a 500 familias / tenants | ECS Fargate Spot 24x7 Multi-Task + Lambda IA + RDS PostgreSQL 16 Multi-AZ (`db.t4g.small`) | **~US$ 115,00 / mes** | **~R$ 667,00 / mes** | **~US$ 0,23 (`~R$ 1,33`) / tenant** |
| **Estagio 3: Hiperescala Kubernetes** | 1.000 a 10.000+ familias / tenants | Kubernetes (EKS / AKS / GKE) + Karpenter Spot Arm64 + KEDA + Aurora PostgreSQL Multi-AZ + MSK | **~US$ 420,00 / mes** | **~R$ 2.436,00 / mes** | **< US$ 0,05 (`< R$ 0,29`) / tenant** |

---

## 3. Comparativo Multicloud em Hiperescala Corporativa (100.000 Tenants Ativos)

Para cenarios enterprise de alta escala (100.000 tenants ativos, 15 milhoes de transacoes/mes, Multi-AZ + Reserva DR Warm Standby com 1-Year Savings Plan / CUD):

|Provedor Cloud | Compute K8s Arm64 + DB Multi-AZ + Kafka + Cache + KMS/DR (USD) | Estimativa Mensal (BRL @ R$ 5,80) | Custo Unitario por Tenant (USD / BRL) |
| :--- | :---: | :---: | :---: |
| **Amazon Web Services (AWS)** | **US$ 2.180,00 / mes** | **R$ 12.644,00 / mes** | **US$ 0,0218 (`R$ 0,126`) / tenant** |
| **Microsoft Azure** | **US$ 2.190,00 / mes** | **R$ 12.702,00 / mes** | **US$ 0,0219 (`R$ 0,127`) / tenant** |
| **Google Cloud Platform (GCP)** | **US$ 2.040,00 / mes** | **R$ 11.832,00 / mes** | **US$ 0,0204 (`R$ 0,118`) / tenant** |

---

## 4. Operacao Automatizada da Lambda `pfm-finops-manager` (`v0.4.0`)

A funcao AWS Lambda `pfm-finops-manager` (`arn:aws:lambda:us-east-2:366476833548:function:pfm-finops-manager`, Python 3.12 Arm64) governa o ciclo de custo zero noturno e audita em tempo real os recursos da conta `366476833548` (`us-east-2`):

1. **`{"action": "stop"}` (Desligamento Noturno -- 20:30 BRT):**
   - Escala todos os 4 servicos do cluster `pfm-ecs-pilot` (`pfm-core-ledger-java`, `pfm-ingestion-bff-go`, `pfm-forecast-engine-go`, `pfm-web-nextjs`) para `desiredCount = 0`;
   - Executa `rds.stop_db_instance(DBInstanceIdentifier="pfm-core-ledger-prod")`;
   - Mantem o run-rate noturno de compute em **US$ 0,00/hora (`R$ 0,00/hora`)**.
2. **`{"action": "start"}` (Religamento Matinal -- 06:00 BRT):**
   - Executa `rds.start_db_instance(DBInstanceIdentifier="pfm-core-ledger-prod")`;
   - Restaura `desiredCount = 1` nos 4 servicos ECS e libera a concorrencia da Lambda `pfm-ai-worker-python-prod`.
3. **`{"action": "audit"}` (Raio-X FinOps & Guardrails Zero-EKS / Zero-NAT):**
   - Retorna a contagem exata de recursos ativos/parados, o run-rate mensal projetado e o bloco `cost_guardrails`, disparando `CRITICAL_COST_ALERT` caso qualquer cluster EKS ou NAT Gateway ativo seja detectado na regiao.
4. **Scale-to-Zero Bootstrap (`ADR-009` -- `desired=0, min=0, max=0` em `dev` e `prod`):**
   - Durante a fase de provisionamento estrutural de infraestrutura (`FEAT-01B`), todos os servicos ECS nos ambientes `dev` (`pfm-shared/dev/terraform.tfstate`) e `prod` (`pfm-shared/prod/terraform.tfstate`) sao inicializados com `desired_count = 0`, `min_capacity = 0` e `max_capacity = 0`, garantindo **custo US$ 0,00 (`R$ 0,00`)** de compute e zero falhas de `CannotPullContainerError` ate a publicacao das imagens no ECR (`FEAT-02`/`FEAT-03`).

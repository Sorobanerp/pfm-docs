# Auditoria Tecnica de Repositorios: Inventario, Diagnostico de Cascas & Candidatos a Delecao

**Data/Hora do Diagnostico:** `2026-11-17T08:55:00-03:00`
**Auditor Responsavel:** Principal DevOps & FinOps Auditor
**Escopo Auditado:** Diretorio local `/home/dantas/workspace/pfm-platform/` e Organizacao GitHub [`Sorobanerp`](https://github.com/Sorobanerp) / Conta [`fcd007`](https://github.com/fcd007)

---

## 1. Sumario Executivo

Uma analise aprofundada comparou a topologia local real com os repositorios remotos no GitHub e os requisitos arquiteturais da **Plataforma PFM V2**:

1. **Ambiente Local (`/home/dantas/workspace/pfm-platform/`):**
   - **14 Repositorios ATIVOS e 100% IMPLEMENTADOS**: Todos possuem codigo-fonte real, testes unitarios/integrados aprovados, manifestos IaC (Terraform/Helm) ou documentacao viva.
   - **0 Repositorios Locais Vazios/Cascas**: Nenhuma pasta `pfm-*` local e casca vazia.
   - **1 Diretorio Residual de Ferramenta Local (`.github/modernize/`)**: Arquivo de hook residual de ferramenta de extensao de migracao Java gerado no workspace raiz (candidato a remocao para manter a raiz limpa).

2. **Ambiente Remoto GitHub ([`Sorobanerp`](https://github.com/Sorobanerp)):**
   - **4 Repositorios Ativos e Sincronizados**: `pfm-contracts`, `pfm-docs`, `pfm-mobile-android`, `pfm-shared-infra`.
   - **11 Repositorios CASCA / VAZIOS / OBSOLETOS (Criados em 16/11/2026 com 1 unico commit e 0 linhas de codigo)**: Contem apenas `.gitignore`, `README.md` e `.gitkeep`. Foram concebidos no desenho inicial V1 e foram consolidados/substituidos na arquitetura V2 real.
   - **10 Repositorios Locais V2 Aguardando Criacao/Vinculacao Remota**: Os novos servicos V2 consolidados (`pfm-core-ledger-java`, `pfm-ingestion-bff-go`, `pfm-forecast-engine-go`, `pfm-ai-worker-python`, `pfm-web-nextjs` e seus respectivos `*-infra`) estao prontos localmente, mas nao possuem seus remotos correspondentes no GitHub.

---

## 2. Inventario Completo dos 14 Repositorios Locais (Workspace)

Criterio de contagem: arquivos reais de codigo (`.go`, `.java`, `.py`, `.ts`, `.tsx`, `.kt`, `.proto`, `.sql`, `.sh`) e configuracao (`.yaml`, `.tf`, `.json`, `.toml`), **excluindo** `.git`, `node_modules`, `.venv`, `target`, `site` e arquivos vazios `.gitkeep`.

| # | Repositorio Local | Categoria | Arquivos Reais | Codigo Fonte | Config / IaC | Status Tecnico | Descricao & Escopo Real V2 |
| :-: | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **01** | `pfm-contracts` | Contratos | **66** | 59 | 2 | **ATIVO / IMPLEMENTADO** | SSoT Protobuf v3 (`ledger_events.proto`, `core_ledger_service.proto`, `forecast_service.proto`) + stubs Go/Java/Python. |
| **02** | `pfm-docs` | Governanca | **19** | 0 | 1 | **ATIVO / IMPLEMENTADO** | Portal MkDocs Material estrito, ADRs V2, Modelo C4, SRE, FinOps, BDD e Relatorios de Auditoria. |
| **03** | `pfm-shared-infra` | Infra Base | **19** | 9 | 9 | **ATIVO / IMPLEMENTADO** | LocalStack S3/KMS, 2x PG16 RLS, Kafka KRaft, Valkey, Envoy Gateway, k6 load test, E2E suite. |
| **04** | `pfm-core-ledger-java` | Core Banking | **42** | 36 | 3 | **ATIVO / IMPLEMENTADO** | Java 25 LTS, Spring Boot 3.5, Virtual Threads, Partidas Dobradas, Limite!=Orcamento, Flyway, PG16 RLS. |
| **05** | `pfm-core-ledger-infra` | IaC 1:1 | **14** | 0 | 13 | **ATIVO / IMPLEMENTADO** | OpenTofu/Terraform Multi-Cloud, Helm Chart HA, NetworkPolicy Zero-Trust, Alertas Prometheus. |
| **06** | `pfm-ingestion-bff-go` | Ingestao / Edge | **20** | 16 | 0 | **ATIVO / IMPLEMENTADO** | Golang 1.24, Zero-Disk RAM PDF Unlock, Checksum SHA-256, Scraper SEFAZ, Rate Limiter, gRPC client. |
| **07** | `pfm-ingestion-bff-infra` | IaC 1:1 | **13** | 0 | 12 | **ATIVO / IMPLEMENTADO** | OpenTofu Multi-Cloud, Helm Chart, NetworkPolicy, Probes HTTP, Alertas Prometheus. |
| **08** | `pfm-forecast-engine-go`| Projecao / Math | **14** | 10 | 0 | **ATIVO / IMPLEMENTADO** | Golang 1.24, Simulador Imutavel SAC/Price/Consorcio, Run-rate Preditivo, gRPC, Valkey `< 25ms`. |
| **09** | `pfm-forecast-engine-infra`| IaC 1:1 | **13** | 0 | 12 | **ATIVO / IMPLEMENTADO** | OpenTofu Multi-Cloud, Helm Chart, Probes gRPC, Alertas Prometheus de latencia P99 `< 25ms`. |
| **10** | `pfm-ai-worker-python` | Inteligencia | **33** | 25 | 1 | **ATIVO / IMPLEMENTADO** | Python 3.12, Pipeline 3 Camadas (L1 PGVector/RLS, L2 Normalizador Regex, L3 Gemini Fallback). |
| **11** | `pfm-ai-worker-infra` | IaC 1:1 | **9** | 0 | 8 | **ATIVO / IMPLEMENTADO** | OpenTofu Multi-Cloud, Helm Chart KEDA Scale-to-Zero, DevSecOps Trivy/Semgrep. |
| **12** | `pfm-web-nextjs` | Frontend Web | **20** | 11 | 3 | **ATIVO / IMPLEMENTADO** | Next.js 15 SSR, TypeScript estrito, Tailwind, Matriz Multi-Cartoes, Simulador, Playwright E2E. |
| **13** | `pfm-web-infra` | IaC 1:1 | **12** | 0 | 11 | **ATIVO / IMPLEMENTADO** | OpenTofu Multi-Cloud, Helm Chart SSR, NetworkPolicy, Probes HTTP. |
| **14** | `pfm-mobile-android` | Frontend Mobile| **11** | 9 | 1 | **ATIVO / IMPLEMENTADO** | Kotlin, Jetpack Compose, Room/SQLCipher, WorkManager Sync Fila Criptografada Offline-First. |

---

## 3. Inventario dos Repositorios Remotos no GitHub (`Sorobanerp`)

Auditoria realizada via GitHub CLI (`gh api`) inspecionando arvores de arquivos (*tree recursive*) e historico de commits:

| Repositorio Remoto GitHub | Commits | Codigo Real | Status / Diagnostico | Justificativa Tecnica & Acao Recomendada |
| :--- | :---: | :---: | :---: | :--- |
| `Sorobanerp/pfm-shared-infra` | 5 | 19 arquivos | **ATIVO (MANTER)** | Repositorio oficial de Landing Zone e simulacao local de nuvem. |
| `Sorobanerp/pfm-contracts` | 2 | 66 arquivos | **ATIVO (MANTER)** | Repositorio oficial de schemas Protobuf v3 e Buf CLI. |
| `Sorobanerp/pfm-docs` | 3 | 19 arquivos | **ATIVO (MANTER)** | Repositorio oficial de governanca, arquitetura e documentacao viva. |
| `Sorobanerp/pfm-mobile-android` | 2 | 11 arquivos | **ATIVO (MANTER)** | Repositorio oficial do app Android nativo offline-first. |
| `Sorobanerp/pfm-api-gateway` | 1 | **0 arquivos** | **CASCA VAZIA (DELECAO)** | Apenas `.gitkeep`. Substituido pelo Envoy Gateway em `pfm-shared-infra` e BFF em `pfm-ingestion-bff-go`. |
| `Sorobanerp/pfm-ledger-service` | 1 | **0 arquivos** | **CASCA VAZIA (DELECAO)** | Apenas `.gitkeep`. Substituido pelo `pfm-core-ledger-java`. |
| `Sorobanerp/pfm-cards-service` | 1 | **0 arquivos** | **CASCA VAZIA (DELECAO)** | Apenas `.gitkeep`. Regras de cartoes consolidadas no aggregate do `pfm-core-ledger-java`. |
| `Sorobanerp/pfm-budget-service` | 1 | **0 arquivos** | **CASCA VAZIA (DELECAO)** | Apenas `.gitkeep`. Orcamento de 2 niveis incorporado no `pfm-core-ledger-java`. |
| `Sorobanerp/pfm-reconcile-service` | 1 | **0 arquivos** | **CASCA VAZIA (DELECAO)** | Apenas `.gitkeep`. Motor de conciliacao NFC-e/Fatura incorporado no `pfm-core-ledger-java`. |
| `Sorobanerp/pfm-ingestion-pdf-service`| 1 | **0 arquivos** | **CASCA VAZIA (DELECAO)** | Apenas `.gitkeep`. Ingestao em RAM incorporada no `pfm-ingestion-bff-go` (Zero-Disk ADR-006). |
| `Sorobanerp/pfm-nfce-scraper-service` | 1 | **0 arquivos** | **CASCA VAZIA (DELECAO)** | Apenas `.gitkeep`. Scraper SEFAZ incorporado como adaptador em `pfm-ingestion-bff-go`. |
| `Sorobanerp/pfm-ai-categorizer-service`| 1 | **0 arquivos** | **CASCA VAZIA (DELECAO)** | Apenas `.gitkeep`. Substituido pelo repositorio implementado `pfm-ai-worker-python`. |
| `Sorobanerp/pfm-notification-service` | 1 | **0 arquivos** | **CASCA VAZIA (DELECAO)** | Apenas `.gitkeep`. Nao implementado no MVP (previsto no Backlog para Release 2.1). |
| `Sorobanerp/pfm-web-portal` | 1 | **0 arquivos** | **CASCA VAZIA (DELECAO)** | Apenas `.gitkeep`. Substituido pelo portal executivo Next.js `pfm-web-nextjs`. |
| `Sorobanerp/pfm-infra-iac` | 1 | **0 arquivos** | **CASCA VAZIA (DELECAO)** | Apenas `.gitkeep`. Monolito IaC V1 substituido pelos 5 repositorios 1:1 `*-infra` + `pfm-shared-infra`. |
| `Sorobanerp/Sorobanerp` | >1 | Profile | **INSTITUCIONAL (MANTER)**| README de perfil da organizacao GitHub Sorobanerp. |
| `Sorobanerp/sorobanerp-landpage` | >1 | Site estatico | **INSTITUCIONAL (MANTER)**| Landing page comercial da organizacao Soroban ERP. |

---

## 4. Repositorios da Conta Pessoal GitHub (`fcd007`) Relacionados

| Repositorio | Visibilidade | Ultimo Update | Diagnostico & Recomendacao |
| :--- | :---: | :---: | :--- |
| `fcd007/fastapi-categorize-service-api` | Privado | Fev/2026 | **OBSOLETO / ARQUIVAR:** Prototipo inicial de categorizacao FastAPI construido no inicio do ano. Todo o codigo funcional moderno com 3 camadas, taxonomia oficial e PGVector esta em `pfm-ai-worker-python`. Recomendacao: Arquivar (*Archive*) ou excluir caso nao deseje manter historico. |

---

## 5. Lista Explicita de Repositorios Candidatos a Delecao

Os 11 repositorios remotos abaixo sao **100% cascas vazias** criadas em lote no dia 16/11/2026 contendo apenas arquivos de placeholder `.gitkeep` e zero implementacao. Sua exclusao e recomendada para:
1. Eliminar confusao conceitual entre a arquitetura legada V1 e a arquitetura V2 implementada.
2. Liberar o namespace para a publicacao dos repositorios reais V2 (`pfm-core-ledger-java`, `pfm-ingestion-bff-go`, `pfm-forecast-engine-go`, etc.).
3. Reduzir ruido de governanca e auditoria em ferramentas de CI/CD e seguranca (Dependabot, CodeQL).

### Candidatos Remotos no GitHub (`Sorobanerp`):
1. `Sorobanerp/pfm-api-gateway`
2. `Sorobanerp/pfm-ledger-service`
3. `Sorobanerp/pfm-cards-service`
4. `Sorobanerp/pfm-budget-service`
5. `Sorobanerp/pfm-reconcile-service`
6. `Sorobanerp/pfm-ingestion-pdf-service`
7. `Sorobanerp/pfm-nfce-scraper-service`
8. `Sorobanerp/pfm-ai-categorizer-service`
9. `Sorobanerp/pfm-notification-service`
10. `Sorobanerp/pfm-web-portal`
11. `Sorobanerp/pfm-infra-iac`

### Candidato Local no Workspace (Diretorio Residual de IDE):
1. `/home/dantas/workspace/pfm-platform/.github/modernize/` (residuo de ferramenta de modernizacao Java, nao pertence ao repositorio).

---

## 6. Comandos Prontos para Execucao da Limpeza (Comentados por Seguranca)

> [!CAUTION]
> **Atencao:** Os comandos abaixo realizam delecoes definitivas. Eles estao intencionalmente comentados (`#`). Execute-os somente apos sua conferencia e validacao explicita.

### Passo A -- Limpeza Local de Residuos (Workspace)

```bash
# Remover pasta residual de ferramenta de modernizacao na raiz do workspace
# rm -rf /home/dantas/workspace/pfm-platform/.github/modernize
```

### Passo B -- Delecao dos 11 Repositorios Cascas no GitHub (`Sorobanerp`)

```bash
# Executar delecao segura das cascas vazias remotas (requer permissao de admin na org Sorobanerp)
# gh repo delete Sorobanerp/pfm-api-gateway --yes
# gh repo delete Sorobanerp/pfm-ledger-service --yes
# gh repo delete Sorobanerp/pfm-cards-service --yes
# gh repo delete Sorobanerp/pfm-budget-service --yes
# gh repo delete Sorobanerp/pfm-reconcile-service --yes
# gh repo delete Sorobanerp/pfm-ingestion-pdf-service --yes
# gh repo delete Sorobanerp/pfm-nfce-scraper-service --yes
# gh repo delete Sorobanerp/pfm-ai-categorizer-service --yes
# gh repo delete Sorobanerp/pfm-notification-service --yes
# gh repo delete Sorobanerp/pfm-web-portal --yes
# gh repo delete Sorobanerp/pfm-infra-iac --yes
```

### Passo C (Recomendado Pos-Delecao) -- Criar e Publicar os 10 Repositorios Locais V2 no GitHub

Apos a limpeza das cascas, criar os repositorios remotos corretos na organizacao `Sorobanerp` e enviar o codigo real comitado:

```bash
# Lista dos 10 repositorios locais reais para criacao e push na organizacao Sorobanerp:
# 1. gh repo create Sorobanerp/pfm-core-ledger-java --private --source=/home/dantas/workspace/pfm-platform/pfm-core-ledger-java --push
# 2. gh repo create Sorobanerp/pfm-core-ledger-infra --private --source=/home/dantas/workspace/pfm-platform/pfm-core-ledger-infra --push
# 3. gh repo create Sorobanerp/pfm-ingestion-bff-go --private --source=/home/dantas/workspace/pfm-platform/pfm-ingestion-bff-go --push
# 4. gh repo create Sorobanerp/pfm-ingestion-bff-infra --private --source=/home/dantas/workspace/pfm-platform/pfm-ingestion-bff-infra --push
# 5. gh repo create Sorobanerp/pfm-forecast-engine-go --private --source=/home/dantas/workspace/pfm-platform/pfm-forecast-engine-go --push
# 6. gh repo create Sorobanerp/pfm-forecast-engine-infra --private --source=/home/dantas/workspace/pfm-platform/pfm-forecast-engine-infra --push
# 7. gh repo create Sorobanerp/pfm-ai-worker-python --private --source=/home/dantas/workspace/pfm-platform/pfm-ai-worker-python --push
# 8. gh repo create Sorobanerp/pfm-ai-worker-infra --private --source=/home/dantas/workspace/pfm-platform/pfm-ai-worker-infra --push
# 9. gh repo create Sorobanerp/pfm-web-nextjs --private --source=/home/dantas/workspace/pfm-platform/pfm-web-nextjs --push
# 10. gh repo create Sorobanerp/pfm-web-infra --private --source=/home/dantas/workspace/pfm-platform/pfm-web-infra --push
```

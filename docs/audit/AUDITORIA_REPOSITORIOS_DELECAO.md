# Auditoria Técnica de Repositórios: Inventário, Diagnóstico de Cascas & Candidatos à Deleção

**Data/Hora do Diagnóstico:** `2026-11-17T08:55:00-03:00`  
**Auditor Responsável:** Principal DevOps & FinOps Auditor  
**Escopo Auditado:** Diretório local `/home/dantas/workspace/pfm-platform/` e Organização GitHub [`Sorobanerp`](https://github.com/Sorobanerp) / Conta [`fcd007`](https://github.com/fcd007)

---

## 1. Sumário Executivo

Uma análise aprofundada comparou a topologia local real com os repositórios remotos no GitHub e os requisitos arquiteturais da **Plataforma PFM V2**:

1. **Ambiente Local (`/home/dantas/workspace/pfm-platform/`):**
   - **14 Repositórios ATIVOS e 100% IMPLEMENTADOS**: Todos possuem código-fonte real, testes unitários/integrados aprovados, manifestos IaC (Terraform/Helm) ou documentação viva.
   - **0 Repositórios Locais Vazios/Cascas**: Nenhuma pasta `pfm-*` local é casca vazia.
   - **1 Diretório Residual de Ferramenta Local (`.github/modernize/`)**: Arquivo de hook residual de ferramenta de extensão de migração Java gerado no workspace raiz (candidato a remoção para manter a raiz limpa).

2. **Ambiente Remoto GitHub ([`Sorobanerp`](https://github.com/Sorobanerp)):**
   - **4 Repositórios Ativos e Sincronizados**: `pfm-contracts`, `pfm-docs`, `pfm-mobile-android`, `pfm-shared-infra`.
   - **11 Repositórios CASCA / VAZIOS / OBSOLETOS (Criados em 16/11/2026 com 1 único commit e 0 linhas de código)**: Contêm apenas `.gitignore`, `README.md` e `.gitkeep`. Foram concebidos no desenho inicial V1 e foram consolidados/substituídos na arquitetura V2 real.
   - **10 Repositórios Locais V2 Aguardando Criação/Vinculação Remota**: Os novos serviços V2 consolidados (`pfm-core-ledger-java`, `pfm-ingestion-bff-go`, `pfm-forecast-engine-go`, `pfm-ai-worker-python`, `pfm-web-nextjs` e seus respectivos `*-infra`) estão prontos localmente, mas não possuem seus remotos correspondentes no GitHub.

---

## 2. Inventário Completo dos 14 Repositórios Locais (Workspace)

Critério de contagem: arquivos reais de código (`.go`, `.java`, `.py`, `.ts`, `.tsx`, `.kt`, `.proto`, `.sql`, `.sh`) e configuração (`.yaml`, `.tf`, `.json`, `.toml`), **excluindo** `.git`, `node_modules`, `.venv`, `target`, `site` e arquivos vazios `.gitkeep`.

| # | Repositório Local | Categoria | Arquivos Reais | Código Fonte | Config / IaC | Status Técnico | Descrição & Escopo Real V2 |
| :-: | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **01** | `pfm-contracts` | Contratos | **66** | 59 | 2 | **ATIVO / IMPLEMENTADO** | SSoT Protobuf v3 (`ledger_events.proto`, `core_ledger_service.proto`, `forecast_service.proto`) + stubs Go/Java/Python. |
| **02** | `pfm-docs` | Governança | **19** | 0 | 1 | **ATIVO / IMPLEMENTADO** | Portal MkDocs Material estrito, ADRs V2, Modelo C4, SRE, FinOps, BDD e Relatórios de Auditoria. |
| **03** | `pfm-shared-infra` | Infra Base | **19** | 9 | 9 | **ATIVO / IMPLEMENTADO** | LocalStack S3/KMS, 2x PG16 RLS, Kafka KRaft, Valkey, Envoy Gateway, k6 load test, E2E suite. |
| **04** | `pfm-core-ledger-java` | Core Banking | **42** | 36 | 3 | **ATIVO / IMPLEMENTADO** | Java 25 LTS, Spring Boot 3.5, Virtual Threads, Partidas Dobradas, Limite≠Orçamento, Flyway, PG16 RLS. |
| **05** | `pfm-core-ledger-infra` | IaC 1:1 | **14** | 0 | 13 | **ATIVO / IMPLEMENTADO** | OpenTofu/Terraform Multi-Cloud, Helm Chart HA, NetworkPolicy Zero-Trust, Alertas Prometheus. |
| **06** | `pfm-ingestion-bff-go` | Ingestão / Edge | **20** | 16 | 0 | **ATIVO / IMPLEMENTADO** | Golang 1.24, Zero-Disk RAM PDF Unlock, Checksum SHA-256, Scraper SEFAZ, Rate Limiter, gRPC client. |
| **07** | `pfm-ingestion-bff-infra` | IaC 1:1 | **13** | 0 | 12 | **ATIVO / IMPLEMENTADO** | OpenTofu Multi-Cloud, Helm Chart, NetworkPolicy, Probes HTTP, Alertas Prometheus. |
| **08** | `pfm-forecast-engine-go`| Projeção / Math | **14** | 10 | 0 | **ATIVO / IMPLEMENTADO** | Golang 1.24, Simulador Imutável SAC/Price/Consórcio, Run-rate Preditivo, gRPC, Valkey `< 25ms`. |
| **09** | `pfm-forecast-engine-infra`| IaC 1:1 | **13** | 0 | 12 | **ATIVO / IMPLEMENTADO** | OpenTofu Multi-Cloud, Helm Chart, Probes gRPC, Alertas Prometheus de latência P99 `< 25ms`. |
| **10** | `pfm-ai-worker-python` | Inteligência | **33** | 25 | 1 | **ATIVO / IMPLEMENTADO** | Python 3.12, Pipeline 3 Camadas (L1 PGVector/RLS, L2 Normalizador Regex, L3 Gemini Fallback). |
| **11** | `pfm-ai-worker-infra` | IaC 1:1 | **9** | 0 | 8 | **ATIVO / IMPLEMENTADO** | OpenTofu Multi-Cloud, Helm Chart KEDA Scale-to-Zero, DevSecOps Trivy/Semgrep. |
| **12** | `pfm-web-nextjs` | Frontend Web | **20** | 11 | 3 | **ATIVO / IMPLEMENTADO** | Next.js 15 SSR, TypeScript estrito, Tailwind, Matriz Multi-Cartões, Simulador, Playwright E2E. |
| **13** | `pfm-web-infra` | IaC 1:1 | **12** | 0 | 11 | **ATIVO / IMPLEMENTADO** | OpenTofu Multi-Cloud, Helm Chart SSR, NetworkPolicy, Probes HTTP. |
| **14** | `pfm-mobile-android` | Frontend Mobile| **11** | 9 | 1 | **ATIVO / IMPLEMENTADO** | Kotlin, Jetpack Compose, Room/SQLCipher, WorkManager Sync Fila Criptografada Offline-First. |

---

## 3. Inventário dos Repositórios Remotos no GitHub (`Sorobanerp`)

Auditoria realizada via GitHub CLI (`gh api`) inspecionando árvores de arquivos (*tree recursive*) e histórico de commits:

| Repositório Remoto GitHub | Commits | Código Real | Status / Diagnóstico | Justificativa Técnica & Ação Recomendada |
| :--- | :---: | :---: | :---: | :--- |
| `Sorobanerp/pfm-shared-infra` | 5 | 19 arquivos | **ATIVO (MANTER)** | Repositório oficial de Landing Zone e simulação local de nuvem. |
| `Sorobanerp/pfm-contracts` | 2 | 66 arquivos | **ATIVO (MANTER)** | Repositório oficial de schemas Protobuf v3 e Buf CLI. |
| `Sorobanerp/pfm-docs` | 3 | 19 arquivos | **ATIVO (MANTER)** | Repositório oficial de governança, arquitetura e documentação viva. |
| `Sorobanerp/pfm-mobile-android` | 2 | 11 arquivos | **ATIVO (MANTER)** | Repositório oficial do app Android nativo offline-first. |
| `Sorobanerp/pfm-api-gateway` | 1 | **0 arquivos** | **CASCA VAZIA (DELEÇÃO)** | Apenas `.gitkeep`. Substituído pelo Envoy Gateway em `pfm-shared-infra` e BFF em `pfm-ingestion-bff-go`. |
| `Sorobanerp/pfm-ledger-service` | 1 | **0 arquivos** | **CASCA VAZIA (DELEÇÃO)** | Apenas `.gitkeep`. Substituído pelo `pfm-core-ledger-java`. |
| `Sorobanerp/pfm-cards-service` | 1 | **0 arquivos** | **CASCA VAZIA (DELEÇÃO)** | Apenas `.gitkeep`. Regras de cartões consolidadas no aggregate do `pfm-core-ledger-java`. |
| `Sorobanerp/pfm-budget-service` | 1 | **0 arquivos** | **CASCA VAZIA (DELEÇÃO)** | Apenas `.gitkeep`. Orçamento de 2 níveis incorporado no `pfm-core-ledger-java`. |
| `Sorobanerp/pfm-reconcile-service` | 1 | **0 arquivos** | **CASCA VAZIA (DELEÇÃO)** | Apenas `.gitkeep`. Motor de conciliação NFC-e/Fatura incorporado no `pfm-core-ledger-java`. |
| `Sorobanerp/pfm-ingestion-pdf-service`| 1 | **0 arquivos** | **CASCA VAZIA (DELEÇÃO)** | Apenas `.gitkeep`. Ingestão em RAM incorporada no `pfm-ingestion-bff-go` (Zero-Disk ADR-006). |
| `Sorobanerp/pfm-nfce-scraper-service` | 1 | **0 arquivos** | **CASCA VAZIA (DELEÇÃO)** | Apenas `.gitkeep`. Scraper SEFAZ incorporado como adaptador em `pfm-ingestion-bff-go`. |
| `Sorobanerp/pfm-ai-categorizer-service`| 1 | **0 arquivos** | **CASCA VAZIA (DELEÇÃO)** | Apenas `.gitkeep`. Substituído pelo repositório implementado `pfm-ai-worker-python`. |
| `Sorobanerp/pfm-notification-service` | 1 | **0 arquivos** | **CASCA VAZIA (DELEÇÃO)** | Apenas `.gitkeep`. Não implementado no MVP (previsto no Backlog para Release 2.1). |
| `Sorobanerp/pfm-web-portal` | 1 | **0 arquivos** | **CASCA VAZIA (DELEÇÃO)** | Apenas `.gitkeep`. Substituído pelo portal executivo Next.js `pfm-web-nextjs`. |
| `Sorobanerp/pfm-infra-iac` | 1 | **0 arquivos** | **CASCA VAZIA (DELEÇÃO)** | Apenas `.gitkeep`. Monólito IaC V1 substituído pelos 5 repositórios 1:1 `*-infra` + `pfm-shared-infra`. |
| `Sorobanerp/Sorobanerp` | >1 | Profile | **INSTITUCIONAL (MANTER)**| README de perfil da organização GitHub Sorobanerp. |
| `Sorobanerp/sorobanerp-landpage` | >1 | Site estático | **INSTITUCIONAL (MANTER)**| Landing page comercial da organização Soroban ERP. |

---

## 4. Repositórios da Conta Pessoal GitHub (`fcd007`) Relacionados

| Repositório | Visibilidade | Último Update | Diagnóstico & Recomendação |
| :--- | :---: | :---: | :--- |
| `fcd007/fastapi-categorize-service-api` | Privado | Fev/2026 | **OBSOLETO / ARQUIVAR:** Protótipo inicial de categorização FastAPI construído no início do ano. Todo o código funcional moderno com 3 camadas, taxonomia oficial e PGVector está em `pfm-ai-worker-python`. Recomendação: Arquivar (*Archive*) ou excluir caso não deseje manter histórico. |

---

## 5. Lista Explícita de Repositórios Candidatos à Deleção

Os 11 repositórios remotos abaixo são **100% cascas vazias** criadas em lote no dia 16/11/2026 contendo apenas arquivos de placeholder `.gitkeep` e zero implementação. Sua exclusão é recomendada para:
1. Eliminar confusão conceitual entre a arquitetura legada V1 e a arquitetura V2 implementada.
2. Liberar o namespace para a publicação dos repositórios reais V2 (`pfm-core-ledger-java`, `pfm-ingestion-bff-go`, `pfm-forecast-engine-go`, etc.).
3. Reduzir ruído de governança e auditoria em ferramentas de CI/CD e segurança (Dependabot, CodeQL).

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

### Candidato Local no Workspace (Diretório Residual de IDE):
1. `/home/dantas/workspace/pfm-platform/.github/modernize/` (resíduo de ferramenta de modernização Java, não pertence ao repositório).

---

## 6. Comandos Prontos para Execução da Limpeza (Comentados por Segurança)

> [!CAUTION]
> **Atenção:** Os comandos abaixo realizam deleções definitivas. Eles estão intencionalmente comentados (`#`). Execute-os somente após sua conferência e validação explícita.

### Passo A — Limpeza Local de Resíduos (Workspace)

```bash
# Remover pasta residual de ferramenta de modernização na raiz do workspace
# rm -rf /home/dantas/workspace/pfm-platform/.github/modernize
```

### Passo B — Deleção dos 11 Repositórios Cascas no GitHub (`Sorobanerp`)

```bash
# Executar deleção segura das cascas vazias remotas (requer permissão de admin na org Sorobanerp)
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

### Passo C (Recomendado Pós-Deleção) — Criar e Publicar os 10 Repositórios Locais V2 no GitHub

Após a limpeza das cascas, criar os repositórios remotos corretos na organização `Sorobanerp` e enviar o código real comitado:

```bash
# Lista dos 10 repositórios locais reais para criação e push na organização Sorobanerp:
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

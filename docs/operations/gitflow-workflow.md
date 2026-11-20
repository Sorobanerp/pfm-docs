# Fluxo Oficial Gitflow (Padrão Atlassian) — PFM Core Banking V3.0

Este documento define o modelo oficial de ramificação, versionamento e governança de mudanças aplicado a **todos os 15 repositórios** da organização `Sorobanerp`.

---

## 1. Visão Geral das Branches (Modelo Atlassian Gitflow)

```mermaid
gitGraph
   commit id: "v0.1.0"
   branch develop
   checkout develop
   commit id: "init develop"
   branch feature/us-12-tenant-admin
   checkout feature/us-12-tenant-admin
   commit id: "feat: tenant admin"
   checkout develop
   merge feature/us-12-tenant-admin
   branch release/v0.2.0
   checkout release/v0.2.0
   commit id: "chore: bump v0.2.0"
   checkout main
   merge release/v0.2.0 tag: "v0.2.0"
   checkout develop
   merge release/v0.2.0
   checkout main
   branch hotfix/v0.2.1
   checkout hotfix/v0.2.1
   commit id: "fix: rls policy"
   checkout main
   merge hotfix/v0.2.1 tag: "v0.2.1"
   checkout develop
   merge hotfix/v0.2.1
```

### Branches Permanentes (Protegidas com `enforce_admins: true`)
| Branch | Propósito | Quem pode mesclar | Proteção Ativa |
| :--- | :--- | :--- | :--- |
| **`main`** | Produção oficial e tags de release (`vX.Y.Z`) | Apenas PRs vindos de `release/*` ou `hotfix/*` | PR obrigatório, CI verde, `enforce_admins: true`, sem force-push/delete |
| **`develop`** | Linha de integração contínua (Staging/Piloto) | Apenas PRs vindos de `feature/*`, `fix/*`, `docs/*`, `chore/*`, `refactor/*`, `release/*`, `hotfix/*` | PR obrigatório, CI verde, `enforce_admins: true`, sem force-push/delete |

### Branches Temporárias
| Prefixo | Origem | Destino | Propósito |
| :--- | :--- | :--- | :--- |
| `feature/*` | `develop` | `develop` | Novas funcionalidades e histórias (`US-*` / `UC-*`) |
| `fix/*` | `develop` | `develop` | Correções de bugs encontrados em integração |
| `docs/*` | `develop` | `develop` | Atualizações de documentação e ADRs |
| `chore/*` | `develop` | `develop` | Manutenção de dependências, CI/CD e governança |
| `refactor/*` | `develop` | `develop` | Refatorações sem alteração de contrato externo |
| `release/vX.Y.Z` | `develop` | `main` **e** `develop` | Congelamento de escopo, bump de `CHANGELOG.md` e geração de release |
| `hotfix/vX.Y.Z+1` | `main` | `main` **e** `develop` | Correção emergencial em produção |

---

## 2. Regras Obrigatórias de Governança

1. **Proibição de Push Direto:** Tanto `main` quanto `develop` possuem **GitHub Branch Protection** com `enforce_admins: true`, `allow_force_pushes: false`, `allow_deletions: false` e `required_status_checks.strict: true`.
2. **Branch Source Guard (`.github/workflows/gitflow-branch-guard.yml`):**
   - PRs para `main` são **bloqueados** automaticamente se `github.head_ref` não iniciar com `release/` ou `hotfix/`.
   - PRs para `develop` são **bloqueados** automaticamente se `github.head_ref` não iniciar com `feature/`, `fix/`, `docs/`, `chore/`, `refactor/`, `release/` ou `hotfix/`.
3. **Conventional Commits & SemVer 2.0.0:**
   - Todos os commits e títulos de PR devem seguir o padrão `<tipo>(<escopo>): <descrição>` (`feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `ci`, `build`).
   - Breaking changes usam `!` ou rodapé `BREAKING CHANGE:` (incremento `MAJOR`).

---

## 3. Exemplos Práticos de Comandos Git

### 3.1 Ciclo de Feature (`feature/*` → `develop`)
```bash
git checkout develop && git pull origin develop
git checkout -b feature/us-13-family-rbac
# ... implementar código e testes (>= 95% cobertura) ...
git add -A
git commit -m "feat(ledger): add family RBAC role enforcement"
git push -u origin feature/us-13-family-rbac
gh pr create --base develop --title "feat(ledger): add family RBAC role enforcement"
```

### 3.2 Ciclo de Release (`develop` → `release/vX.Y.Z` → `main` + `develop`)
```bash
git checkout develop && git pull origin develop
git checkout -b release/v3.0.0
# Atualizar CHANGELOG.md e versão
git commit -am "chore(release): prepare v3.0.0"
git push -u origin release/v3.0.0
gh pr create --base main --title "release(v3.0.0): promote pilot release to production"
# Após merge em main, sincronizar tag e back-merge em develop:
gh pr create --base develop --head release/v3.0.0 --title "chore(release): back-merge v3.0.0 into develop"
```

### 3.3 Ciclo de Hotfix (`main` → `hotfix/vX.Y.Z+1` → `main` + `develop`)
```bash
git checkout main && git pull origin main
git checkout -b hotfix/v3.0.1
# Corrigir incidente crítico e adicionar teste de regressão
git commit -am "fix(security): harden tenant RLS check on audit endpoint"
git push -u origin hotfix/v3.0.1
gh pr create --base main --title "fix(security): hotfix v3.0.1"
gh pr create --base develop --head hotfix/v3.0.1 --title "fix(security): back-merge hotfix v3.0.1 into develop"
```

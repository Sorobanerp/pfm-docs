# Artefato 06 — FinOps, ROI & Governança de Custos Cloud (V2 — Ambientes `dev` e `prod`)

Referência canônica sincronizada com [5.3. FinOps & Custos Cloud](finops-e-custos-cloud.md) e [ADR-009](../02-arquitetura-adrs/ADR-009-ambientes-dev-prod-e-estrutura-modular-opentofu.md).

## 1. Resumo Executivo FinOps (`FEAT-01A` Concluída | `FEAT-01B` Modularização `dev`/`prod`)
- **Scale-to-Zero Bootstrap (`0 / 0 / 0`):** Todos os 7 repositórios `*-infra` operam com `desired_count = 0`, `min_capacity = 0` e `max_capacity = 0` em `terraform/environments/dev` e `terraform/environments/prod` durante o bootstrap de infraestrutura, garantindo **US$ 0,00/hora (`R$ 0,00/hora`)** de compute ECS Fargate até o rollout das imagens das aplicações (`FEAT-02` e `FEAT-03`).
- **Meta de Run-Rate Produtivo (Estágio 1 — `us-east-2`):** `< US$ 24,00/mês` (`< R$ 139,20/mês` @ `1 USD = R$ 5,80`) com parada noturna via Lambda `pfm-finops-manager` (`20:30 -- 06:00 BRT`, schedules `DISABLED` por padrão até ativação manual).

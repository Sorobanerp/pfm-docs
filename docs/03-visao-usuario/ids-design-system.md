# 3. Visao do Usuario (UX/UI) -- IDS Design System "PFM Pulse" (Web & Android)

<span class="badge-glow">Artefato 10 - US-14 Design System</span>
<span class="badge-green">Filosofia: 10 Segundos por Dia</span>
<span class="badge-peach">100% em Real Brasileiro (R$)</span>

O **IDS "PFM Pulse"** (*Organic Financial Pulse*) governa toda a experiencia do usuario nos canais **Web Responsivo (`pfm-web-nextjs`)** e **Mobile Android (`pfm-mobile-android`)**, combinando a filosofia **Big Numbers First + Progressive Disclosure** com acessibilidade **WCAG 2.2 AA/AAA**.

---

## 1. Filosofia de Design Thinking: "10 Segundos por Dia"

1. **Big Numbers First:** O topo da tela exibe imediatamente o valor **Livre para Gastar** em `R$` (ex.: `R$ 7.080,00` no mes / `R$ 1.652,00` na semana / `R$ 236,00` hoje) e o status de fechamento previsto.
2. **Progressive Disclosure (Revelacao Progressiva):** Tabelas detalhadas de parcelas e itens fiscais de NFC-e permanecem recolhidas em cards limpos ate que o usuario deseje auditar uma categoria ou fatura especifica.
3. **Zero Ruido Visual:** Graficos vetoriais exibem apenas duas curvas essenciais -- **Regime de Competencia** vs. **Regime de Caixa** em `R$`.

---

## 2. Paleta Cromatica Oficial & Regras de Contraste WCAG

| Token Semantico | Hexadecimal | Texto Obrigatorio | Contraste WCAG | Aplicacao na Interface |
| :--- | :---: | :---: | :---: | :--- |
| `pulse.primary` | `#8CBA51` | `#141D14` / `#FFFFFF` | `7.4:1` (AAA) | CTAs primarios, barras de progresso saudaveis (`< 80%` do teto em `R$`) |
| `pulse.limeGlow` | `#DEFF8B` | **`#141D14`** (Proibido texto branco) | `13.8:1` (AAA) | Card de Saldo Livre Projetado (`R$ 7.080,00`), badges de alta confianca IA |
| `pulse.warmPeach` | `#FBCEB5` | **`#3D1E10`** (Proibido texto claro) | `10.9:1` (AAA) | Alerta preventivo de orcamento (`80% a 99%` do teto em `R$`), Inbox pendente |
| `pulse.coralCritical` | `#FF5D6C` | `#FFFFFF` / `#141D14` | `5.2:1` (AA+) | Estouro de teto (`>= 100%`), divergencia de checksum PDF (`409 Conflict`) |
| `pulse.canvas.light` | `#F7F9F5` | `#141D14` | `15.1:1` (AAA) | Canvas global em modo claro |
| `pulse.surface.light` | `#FFFFFF` | `#141D14` | `16.4:1` (AAA) | Cards Bento Grid com borda `1px solid #E2E9DC` (`#E6ECE2`) |
| `pulse.canvas.dark` | `#111711` | `#F7F9F5` | `15.3:1` (AAA) | Canvas global em modo escuro |

---

## 3. Tipografia e Alinhamento Monetario Tabular (`R$`)

- **Fonte Editorial & UI:** `Plus Jakarta Sans` (pesos `400`, `500`, `600`, `700`, `800`).
- **Fonte Monoespacada & Contratos:** `JetBrains Mono`.
- **Numeros Tabulares Obrigatorios (`tabular-nums`):** Todos os valores em `R$` aplicam `font-variant-numeric: tabular-nums` no CSS Web e `fontFeatureSettings = "tnum"` no Jetpack Compose Android.

---

## 4. Arquitetura das 6 Telas Web (`pfm-web-nextjs`) e 4 Telas Android (`pfm-mobile-android`)

### 4.1. As 6 Jornadas Web Responsivas (Full-Viewport Bento Grid)

| Tela Web | Rota / Escopo | Elementos Principais e Exemplo em BRL (`R$`) |
| :--- | :--- | :--- |
| **1. Pulse Executive Dashboard** | `/` (`UC-03`, `UC-05`) | Seletor `Hoje / Semana / Mes`, Card `Livre para Gastar: R$ 7.080,00`, curva 30/60/90d Competencia vs. Caixa e filtro Familiar (`Todos / Titular / Conjuge`). |
| **2. Auditoria de Faturas PDF (RAM)** | `/statements` (`UC-01`) | Dropzone PDF Zero-Persistence com badge instantaneo de Checksum (`Total Declarado: R$ 6.890,45 == Soma dos Itens: R$ 6.890,45`). |
| **3. Inbox de Conciliacao & IA** | `/inbox` (`UC-04`, `UC-06`) | Fila de revisao em 1 clique para itens com score intermediario (ex.: `IFD*IFOOD BR - R$ 84,90 -> ALIMENTACAO :: DELIVERY_APLICATIVOS`). |
| **4. Simulador de Contratos** | `/contracts` (`UC-05`) | Simulador interativo SAC, Tabela Price e Consorcio (ex.: Saldo `R$ 240.000,00` + Aporte `R$ 20.000,00` -> Economia de `R$ 24.850,40` e `-12 parcelas`). |
| **5. Central de Perfil, Familia & LGPD** | `/profile` (`UC-08` / `US-13`) | Gestao de membros (`OWNER`, `MEMBER`, `VIEWER`), tetos por categoria (ex.: Supermercado `R$ 2.500,00`), cofre KMS de senha PDF, Exportacao JSON/CSV e Crypto-Shredding. |
| **6. Painel SaaS Admin** | `/admin` (`UC-07` / `US-12`) | Visao global de tenants e planos (`FREE`, `INDIVIDUAL_PRO R$ 29,90`, `FAMILY_PLUS R$ 49,90`) com bloqueio Zero-Trust de PII. |

### 4.2. As 4 Telas Nativas do App Android (Jetpack Compose Material 3)

| Tela Android | Componente Compose | Funcao Principal em Mobilidade |
| :--- | :--- | :--- |
| **1. Pulse Home & Ritmo Diario** | `PulseDashboardScreen` | Exibe a quota diaria segura (`R$ 236,00 / dia`) e alertas preventivos de orcamento em `#FBCEB5`. |
| **2. Scanner NFC-e Offline-First** | `NfceScannerScreen` | Captura instantanea do QR Code SEFAZ com persistencia local em Room/SQLCipher e sincronizacao via WorkManager. |
| **3. Swipe-to-Confirm Inbox** | `ReconciliationInboxScreen` | Aprovacao tatil rapida de categorizacoes sugeridas pela IA e conciliacao de comprovantes em `R$`. |
| **4. Cofre Familiar & Privacidade LGPD** | `ProfileAndPrivacyScreen` | Consulta de alca familiar em `R$`, exportacao de dados e controle soberano de privacidade. |

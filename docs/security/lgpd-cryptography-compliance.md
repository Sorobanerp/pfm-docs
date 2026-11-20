# Conformidade LGPD Brasil (Lei 13.709/2018) & Arquitetura Criptográfica Fintech

Este documento especifica os controles técnicos, criptográficos e de isolamento multitenant implementados no **PFM Core Banking V3.0** em aderência à **Lei Geral de Proteção de Dados (Lei nº 13.709/2018 — LGPD)**.

---

## 1. Matriz de Controles LGPD x Implementação Técnica

| Artigo / Princípio LGPD | Requisito Regulatório | Controle Implementado no PFM Core Banking |
| :--- | :--- | :--- |
| **Art. 6º, III (Necessidade)** | Minimização de dados pessoais e ausência de PII em telemetria | Mascaramento automático (`MaskSensitivePII`) em logs/traces OpenTelemetry; métricas Datadog proibidas de conter `tenant_id` ou CPF. |
| **Art. 6º, VII (Segurança)** | Proteção contra acessos não autorizados e vazamentos | **Envelope Encryption (KEK/DEK)** com `AES-256-GCM`, **PostgreSQL `FORCE ROW LEVEL SECURITY`**, **OIDC Zero-Trust** e **mTLS/Service Connect**. |
| **Art. 18, V (Portabilidade)** | Exportação estruturada dos dados do titular | Endpoint `/api/v1/profile/export` gerando pacote JSON/CSV assinado por tenant. |
| **Art. 18, VI (Eliminação)** | Exclusão definitiva e irrecuperável mediante solicitação | Fluxo de **Crypto-Shredding**: destruição da DEK do tenant no KMS + marcação `CRYPTO_SHREDDED` em `lgpd_erasure_requests`. |
| **Art. 46 (Segurança & Sigilo)** | Medidas técnicas aptas a proteger dados pessoais e financeiros | Processamento de faturas PDF **estritamente em RAM** com zeramento explícito (`clear(buf)`) via `defer`. |

---

## 2. Arquitetura Criptográfica Fintech

### 2.1 Envelope Encryption (KEK / DEK por Tenant)
- **KEK (Key Encryption Key):** Chave mestra gerenciada pelo Cloud KMS (AWS KMS / Azure Key Vault / GCP Cloud KMS), nunca exportada em texto claro.
- **DEK (Data Encryption Key):** Chave simétrica `AES-256` exclusiva de cada `tenant_id`, derivada/envelopada via KMS.
- **Cifra Autenticada (`AES-256-GCM`):**
  - IV aleatório de 12 bytes (`SecureRandom`) por operação;
  - Tag de autenticação de 128 bits;
  - **AAD (Additional Authenticated Data):** `tenant_id` em UTF-8 vinculado criptograficamente ao ciphertext (impede *cross-tenant ciphertext replay*).

### 2.2 Cifragem de PII & Índice Cego (`HMAC-SHA256`)
No `pfm-core-ledger-java` (`SensitiveDataCipherPort` / `AesGcmEnvelopeEncryptionKmsAdapter`):
- Dados sensíveis (CPF, documentos, senhas de PDF de cartões) são cifrados com `AES-256-GCM` antes da persistência.
- Consultas por identificador sensível (ex.: busca por CPF sem expor texto claro no banco) utilizam **Índice Cego determinístico (`HMAC-SHA256`)** com chave dedicada e normalização canônica.

### 2.3 Processamento de PDFs em RAM com Zeroing (`pfm-ingestion-bff-go`)
- Nenhuma fatura PDF ou senha é gravada em disco temporário (`/tmp`) ou bucket S3 sem cifragem.
- `ZeroPersistencePDFParser.ParseStatementInRAM` aloca buffers voláteis em `[]byte` na RAM e garante limpeza imediata via `defer`:
  ```go
  defer func() {
      clear(pdfBytes)
      clear(ramBuffer)
      if len(decryptedRAMBuffer) > 0 {
          clear(decryptedRAMBuffer)
      }
  }()
  ```

### 2.4 Isolamento Multitenant em Banco (`PostgreSQL FORCE RLS`)
Todas as tabelas de negócio (`tenants`, `tenant_members`, `financial_accounts`, `credit_cards`, `ledger_entries`, `subscriptions`, `category_budgets`, `card_pdf_passwords`, `lgpd_erasure_requests`, `audit_log`) aplicam:
```sql
ALTER TABLE <tabela> ENABLE ROW LEVEL SECURITY;
ALTER TABLE <tabela> FORCE ROW LEVEL SECURITY;
```
O comando `FORCE ROW LEVEL SECURITY` assegura que até mesmo o usuário proprietário da tabela (`table owner`) respeite as políticas `current_setting('app.current_tenant_id', true)::uuid`.

---

## 3. Fluxo de Crypto-Shredding (Art. 18 LGPD)

1. O usuário `OWNER` confirma a exclusão definitiva digitando `EXCLUIR_DEFINITIVAMENTE_MINHA_CONTA` na Jornada 5 (`/profile`).
2. O `UserProfileService` registra a solicitação em `lgpd_erasure_requests` e invoca a revogação/destruição da DEK do tenant no KMS.
3. Sem a DEK, todos os registros cifrados (`AES-256-GCM`) em snapshots, backups imutáveis (`audit_log`) e armazenamento tornam-se matematicamente irrecuperáveis, preservando a integridade referencial e contábil sem retenção de PII.

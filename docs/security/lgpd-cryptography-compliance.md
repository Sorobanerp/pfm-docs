# Conformidade LGPD Brasil (Lei 13.709/2018) & Arquitetura Criptografica Fintech

Este documento especifica os controles tecnicos, criptograficos e de isolamento multitenant implementados no **PFM Core Banking V3.0** em aderencia a **Lei Geral de Protecao de Dados (Lei no 13.709/2018 -- LGPD)**.

---

## 1. Matriz de Controles LGPD x Implementacao Tecnica

| Artigo / Principio LGPD | Requisito Regulatorio | Controle Implementado no PFM Core Banking |
| :--- | :--- | :--- |
| **Art. 6o, III (Necessidade)** | Minimizacao de dados pessoais e ausencia de PII em telemetria | Mascaramento automatico (`MaskSensitivePII`) em logs/traces OpenTelemetry; metricas Datadog proibidas de conter `tenant_id` ou CPF. |
| **Art. 6o, VII (Seguranca)** | Protecao contra acessos nao autorizados e vazamentos | **Envelope Encryption (KEK/DEK)** com `AES-256-GCM`, **PostgreSQL `FORCE ROW LEVEL SECURITY`**, **OIDC Zero-Trust** e **mTLS/Service Connect**. |
| **Art. 18, V (Portabilidade)** | Exportacao estruturada dos dados do titular | Endpoint `/api/v1/profile/export` gerando pacote JSON/CSV assinado por tenant. |
| **Art. 18, VI (Eliminacao)** | Exclusao definitiva e irrecuperavel mediante solicitacao | Fluxo de **Crypto-Shredding**: destruicao da DEK do tenant no KMS + marcacao `CRYPTO_SHREDDED` em `lgpd_erasure_requests`. |
| **Art. 46 (Seguranca & Sigilo)** | Medidas tecnicas aptas a proteger dados pessoais e financeiros | Processamento de faturas PDF **estritamente em RAM** com zeramento explicito (`clear(buf)`) via `defer`. |

---

## 2. Arquitetura Criptografica Fintech

### 2.1 Envelope Encryption (KEK / DEK por Tenant)
- **KEK (Key Encryption Key):** Chave mestra gerenciada pelo Cloud KMS (AWS KMS / Azure Key Vault / GCP Cloud KMS), nunca exportada em texto claro.
- **DEK (Data Encryption Key):** Chave simetrica `AES-256` exclusiva de cada `tenant_id`, derivada/envelopada via KMS.
- **Cifra Autenticada (`AES-256-GCM`):**
  - IV aleatorio de 12 bytes (`SecureRandom`) por operacao;
  - Tag de autenticacao de 128 bits;
  - **AAD (Additional Authenticated Data):** `tenant_id` em UTF-8 vinculado criptograficamente ao ciphertext (impede *cross-tenant ciphertext replay*).

### 2.2 Cifragem de PII & Indice Cego (`HMAC-SHA256`)
No `pfm-core-ledger-java` (`SensitiveDataCipherPort` / `AesGcmEnvelopeEncryptionKmsAdapter`):
- Dados sensiveis (CPF, documentos, senhas de PDF de cartoes) sao cifrados com `AES-256-GCM` antes da persistencia.
- Consultas por identificador sensivel (ex.: busca por CPF sem expor texto claro no banco) utilizam **Indice Cego deterministico (`HMAC-SHA256`)** com chave dedicada e normalizacao canonica.

### 2.3 Processamento de PDFs em RAM com Zeroing (`pfm-ingestion-bff-go`)
- Nenhuma fatura PDF ou senha e gravada em disco temporario (`/tmp`) ou bucket S3 sem cifragem.
- `ZeroPersistencePDFParser.ParseStatementInRAM` aloca buffers volateis em `[]byte` na RAM e garante limpeza imediata via `defer`:
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
Todas as tabelas de negocio (`tenants`, `tenant_members`, `financial_accounts`, `credit_cards`, `ledger_entries`, `subscriptions`, `category_budgets`, `card_pdf_passwords`, `lgpd_erasure_requests`, `audit_log`) aplicam:
```sql
ALTER TABLE <tabela> ENABLE ROW LEVEL SECURITY;
ALTER TABLE <tabela> FORCE ROW LEVEL SECURITY;
```
O comando `FORCE ROW LEVEL SECURITY` assegura que ate mesmo o usuario proprietario da tabela (`table owner`) respeite as politicas `current_setting('app.current_tenant_id', true)::uuid`.

---

## 3. Fluxo de Crypto-Shredding (Art. 18 LGPD)

1. O usuario `OWNER` confirma a exclusao definitiva digitando `EXCLUIR_DEFINITIVAMENTE_MINHA_CONTA` na Jornada 5 (`/profile`).
2. O `UserProfileService` registra a solicitacao em `lgpd_erasure_requests` e invoca a revogacao/destruicao da DEK do tenant no KMS.
3. Sem a DEK, todos os registros cifrados (`AES-256-GCM`) em snapshots, backups imutaveis (`audit_log`) e armazenamento tornam-se matematicamente irrecuperaveis, preservando a integridade referencial e contabil sem retencao de PII.

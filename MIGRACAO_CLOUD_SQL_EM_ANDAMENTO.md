# 🔄 Migração para Cloud SQL PostgreSQL - EM ANDAMENTO

**Data:** 15 de Dezembro de 2025  
**Status:** ⚠️ **EM PROGRESSO**

---

## ✅ O QUE JÁ FOI FEITO

1. ✅ **API Cloud SQL habilitada** no projeto ifrs16-app
2. ✅ **Instância Cloud SQL criada:**
   - Nome: `ifrs16-database`
   - Versão: PostgreSQL 15
   - Tier: `db-f1-micro` (free tier)
   - Região: `us-central1`
   - IP Público: `136.112.221.225`
   - Connection Name: `ifrs16-app:us-central1:ifrs16-database`

3. ✅ **Database criado:**
   - Nome: `ifrs16_licenses`

4. ✅ **Usuário criado:**
   - Username: `ifrs16_user`
   - Senha: `<CLOUD_SQL_PASSWORD>` *(obtenha via Cloud Console)*

5. ✅ **Cloud Run configurado:**
   - Cloud SQL connection adicionada via Unix socket
   - DATABASE_URL atualizado no Cloud Run

6. ✅ **Código atualizado:**
   - `database.py` ajustado para Cloud SQL (SSL require)
   - Parâmetro inválido `connect_timeout` removido

---

## ⏳ O QUE ESTÁ SENDO FEITO AGORA

1. ⏳ **Build da nova imagem Docker** (em progresso)
2. ⏳ **Deploy da nova imagem** no Cloud Run
3. ⏳ **Executar migrations** para criar tabelas
4. ⏳ **Migrar dados** do Render para Cloud SQL (se necessário)

---

## 📋 PRÓXIMOS PASSOS

### 1. Aguardar Build Completar

O build está rodando em background. Após completar:

```powershell
gcloud run deploy ifrs16-backend --image gcr.io/ifrs16-app/ifrs16-backend --platform managed --region us-central1 --project ifrs16-app --allow-unauthenticated
```

### 2. Executar Migrations

As migrations serão executadas automaticamente no startup (via `init_db()`), mas se necessário, pode executar manualmente:

```powershell
# Via Cloud Run (executar dentro do container)
gcloud run jobs create run-migrations --image gcr.io/ifrs16-app/ifrs16-backend --region us-central1 --project ifrs16-app
```

### 3. Migrar Dados do Render (Opcional)

Se houver dados importantes no Render que precisam ser migrados:

```powershell
# Exportar do Render
$renderUrl = "<RENDER_DATABASE_URL>"
pg_dump $renderUrl > backup_render.sql

# Importar no Cloud SQL (via IP público temporário)
$cloudSqlUrl = "<CLOUD_SQL_DATABASE_URL>"
psql $cloudSqlUrl < backup_render.sql
```

### 4. Testar Login

Após o deploy, testar:

```powershell
$body = @{ email = "<ADMIN_EMAIL>"; password = "<ADMIN_PASSWORD>" } | ConvertTo-Json
Invoke-RestMethod -Uri "https://ifrs16-backend-1051753255664.us-central1.run.app/api/auth/admin/login" -Method Post -ContentType "application/json" -Body $body
```

---

## 🔐 CREDENCIAIS CLOUD SQL

| Campo | Valor |
|-------|-------|
| **Connection Name** | `ifrs16-app:us-central1:ifrs16-database` |
| **IP Público** | `136.112.221.225` |
| **Database** | `ifrs16_licenses` |
| **User** | `ifrs16_user` |
| **Password** | `<CLOUD_SQL_PASSWORD>` *(obtenha via Cloud Console)* |

### DATABASE_URL para Cloud Run (Unix Socket)

```
postgresql://ifrs16_user:<CLOUD_SQL_PASSWORD>@/ifrs16_licenses?host=/cloudsql/ifrs16-app:us-central1:ifrs16-database
```

### DATABASE_URL para Conexão Direta (IP)

```
postgresql://ifrs16_user:<CLOUD_SQL_PASSWORD>@<CLOUD_SQL_IP>:5432/ifrs16_licenses
```

---

## ⚠️ IMPORTANTE

1. **Senha salva em:** `CLOUD_SQL_PASSWORD_NEW.txt` (NÃO commitar no git!)
2. **Arquivo com credenciais:** `cloud_run_env_cloudsql.yaml` (NÃO commitar!)
3. **IP autorizado:** `187.56.249.116` (seu IP atual - pode remover após migração)

---

## 🔗 Links Úteis

- **Cloud SQL Console:** https://console.cloud.google.com/sql/instances?project=ifrs16-app
- **Cloud Run Console:** https://console.cloud.google.com/run?project=ifrs16-app
- **Cloud Build:** https://console.cloud.google.com/cloud-build/builds?project=ifrs16-app

---

**Status:** ⏳ **AGUARDANDO BUILD E DEPLOY**  
**Próxima ação:** Aguardar build completar e fazer deploy

# 🚀 Deploy via MCP - Status

## ⚠️ Limitação Atual

**Não há ferramentas MCP específicas para Google Cloud Run.**

As ferramentas MCP disponíveis são principalmente para:
- Render (mcp_render_*)
- Git/GitHub (mcp_GitKraken_*)
- Stripe (mcp_stripe_*)

## ✅ Solução: Deploy via Terminal

Como não há MCP para Google Cloud Run, o deploy precisa ser feito via comandos `gcloud` no terminal.

### Pré-requisitos

1. **Google Cloud SDK instalado:**
   - Download: https://cloud.google.com/sdk/docs/install
   - Ou via PowerShell: `(New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:TEMP\gcloud-installer.exe"); Start-Process "$env:TEMP\gcloud-installer.exe"`

2. **Autenticação:**
   ```powershell
   gcloud auth login
   gcloud config set project ifrs16-app
   ```

3. **APIs habilitadas:**
   ```powershell
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable run.googleapis.com
   gcloud services enable sqladmin.googleapis.com
   ```

### Comandos de Deploy

#### 1. Build da Imagem Docker

```powershell
cd "c:\Projetos\IFRS 16"
gcloud builds submit --tag gcr.io/ifrs16-app/ifrs16-backend --project ifrs16-app backend/
```

**Tempo estimado:** 5-10 minutos

#### 2. Deploy no Cloud Run

```powershell
gcloud run deploy ifrs16-backend `
    --image gcr.io/ifrs16-app/ifrs16-backend `
    --platform managed `
    --region us-central1 `
    --allow-unauthenticated `
    --project ifrs16-app `
    --set-env-vars "ENVIRONMENT=production,DEBUG=false"
```

**Tempo estimado:** 2-5 minutos

#### 3. Verificar Deploy

```powershell
# Obter URL do serviço
gcloud run services describe ifrs16-backend --region us-central1 --project ifrs16-app --format="value(status.url)"

# Ver logs
gcloud run services logs read ifrs16-backend --region us-central1 --project ifrs16-app --limit 50
```

### Migration Automática

A migration `20250115_0003_add_contracts_table.py` será executada **automaticamente** quando o backend iniciar, através da função `init_db()` no `main.py`.

Se precisar executar manualmente:

```powershell
# Via Cloud Run Job
gcloud run jobs create run-migration-contracts `
    --image gcr.io/ifrs16-app/ifrs16-backend `
    --region us-central1 `
    --project ifrs16-app `
    --command "alembic" `
    --args "upgrade,head" `
    --max-retries 1

gcloud run jobs execute run-migration-contracts --region us-central1 --project ifrs16-app --wait
```

### Script Automatizado

Use o script `deploy_firebase.ps1` que já está configurado:

```powershell
cd "c:\Projetos\IFRS 16"
.\deploy_firebase.ps1
```

## 🔄 Alternativa: Usar Render MCP (Não Recomendado)

Se você quiser migrar para Render, há ferramentas MCP disponíveis:

```python
# Exemplo de uso do Render MCP (não implementado no projeto atual)
mcp_render_deploy_service({
    "serviceId": "seu-service-id",
    "clearCache": False
})
```

**Mas o projeto está configurado para Firebase/Google Cloud, não Render.**

## 📋 Checklist de Deploy

- [ ] Google Cloud SDK instalado e no PATH
- [ ] Autenticado no gcloud (`gcloud auth login`)
- [ ] Projeto configurado (`gcloud config set project ifrs16-app`)
- [ ] APIs habilitadas
- [ ] Build da imagem executado
- [ ] Deploy no Cloud Run executado
- [ ] Migration executada (automática ou manual)
- [ ] Variáveis de ambiente configuradas no Cloud Run
- [ ] Endpoints testados

## 🎯 Próximos Passos

1. **Instalar/configurar gcloud CLI** (se ainda não tiver)
2. **Executar deploy** usando os comandos acima ou o script `deploy_firebase.ps1`
3. **Verificar migration** foi executada
4. **Testar endpoints** de contratos

---

**Status:** ⚠️ **Aguardando gcloud CLI configurado para executar deploy**

**Nota:** O código está 100% implementado e pronto. Apenas falta executar o deploy via gcloud CLI.

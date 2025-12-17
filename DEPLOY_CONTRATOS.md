# 🚀 Deploy da Funcionalidade de Contratos

## ✅ O QUE FOI IMPLEMENTADO

A funcionalidade de persistência de contratos foi **completamente implementada**:

1. ✅ **Modelo de Dados**
   - Enum `ContractStatus` (DRAFT, ACTIVE, TERMINATED)
   - Modelo `Contract` com todos os campos
   - Relacionamento com `User`
   - Limites atualizados no modelo `License` (5, 50, 500, -1)

2. ✅ **Schemas Pydantic**
   - `ContractCreate`, `ContractUpdate`, `ContractOut`, `ContractListOut`

3. ✅ **Repository Pattern**
   - `ContractRepository` com métodos CRUD completos

4. ✅ **Service Layer**
   - `ContractService` com validação de limites por licença

5. ✅ **API Endpoints**
   - `POST /api/contracts` - Criar contrato
   - `GET /api/contracts` - Listar contratos
   - `GET /api/contracts/{id}` - Obter contrato
   - `PUT /api/contracts/{id}` - Atualizar contrato
   - `DELETE /api/contracts/{id}` - Deletar contrato (soft delete)

6. ✅ **Migration Alembic**
   - Migration `20250115_0003_add_contracts_table.py` criada

7. ✅ **Testes**
   - Testes completos em `test_contracts_api.py`

---

## 📋 PRÓXIMOS PASSOS PARA DEPLOY

### 1. Build e Deploy do Backend

Execute os seguintes comandos no PowerShell (com gcloud CLI instalado e configurado):

```powershell
# Navegar para o diretório do projeto
cd "c:\Projetos\IFRS 16"

# Build da imagem Docker
gcloud builds submit --tag gcr.io/ifrs16-app/ifrs16-backend --project ifrs16-app backend/

# Deploy no Cloud Run
gcloud run deploy ifrs16-backend `
    --image gcr.io/ifrs16-app/ifrs16-backend `
    --platform managed `
    --region us-central1 `
    --allow-unauthenticated `
    --project ifrs16-app `
    --set-env-vars "ENVIRONMENT=production,DEBUG=false"
```

**Ou use o script automatizado:**

```powershell
.\deploy_firebase.ps1
```

### 2. Executar Migration

A migration será executada **automaticamente** quando o backend iniciar (via `init_db()`), mas você pode executar manualmente se necessário:

#### Opção A: Via Cloud Run (Recomendado)

A migration já está configurada para executar automaticamente no startup do backend.

#### Opção B: Via Cloud SQL Proxy (Local)

```powershell
# 1. Instalar Cloud SQL Proxy (se ainda não tiver)
# Download: https://cloud.google.com/sql/docs/postgres/sql-proxy

# 2. Iniciar proxy
cloud_sql_proxy -instances=ifrs16-app:us-central1:ifrs16-database=tcp:5432

# 3. Em outro terminal, executar migration
cd backend
alembic upgrade head
```

#### Opção C: Verificar se a tabela já existe

```powershell
# Conectar ao banco
gcloud sql connect ifrs16-database --user=ifrs16_user --database=ifrs16_licenses --project=ifrs16-app

# No PostgreSQL, verificar se a tabela existe:
\dt contracts

# Ver estrutura:
\d contracts
```

### 3. Verificar Deploy

Após o deploy, verifique:

1. **Backend está rodando:**
   ```powershell
   gcloud run services describe ifrs16-backend --region us-central1 --project ifrs16-app
   ```

2. **Testar endpoint de contratos:**
   ```powershell
   # Obter URL do backend
   $backendUrl = (gcloud run services describe ifrs16-backend --region us-central1 --project ifrs16-app --format="value(status.url)")

   # Testar endpoint (requer autenticação)
   curl -X GET "$backendUrl/api/contracts" -H "Authorization: Bearer [SEU_TOKEN]"
   ```

3. **Verificar logs:**
   ```powershell
   gcloud run services logs read ifrs16-backend --region us-central1 --project ifrs16-app --limit 50
   ```

---

## 🔍 VERIFICAÇÕES PÓS-DEPLOY

### 1. Verificar se a Migration foi Executada

```sql
-- Conectar ao banco
gcloud sql connect ifrs16-database --user=ifrs16_user --database=ifrs16_licenses --project=ifrs16-app

-- Verificar tabela
SELECT * FROM information_schema.tables WHERE table_name = 'contracts';

-- Ver estrutura
\d contracts

-- Verificar enum
SELECT * FROM pg_type WHERE typname = 'contractstatus';
```

### 2. Testar Endpoints

Use o Postman, Insomnia ou curl para testar:

```bash
# 1. Fazer login para obter token
POST https://[BACKEND_URL]/api/auth/login
{
  "email": "seu@email.com",
  "password": "sua_senha"
}

# 2. Criar contrato
POST https://[BACKEND_URL]/api/contracts
Authorization: Bearer [TOKEN]
{
  "name": "Contrato Teste",
  "description": "Descrição do contrato",
  "contract_code": "CT-001",
  "status": "draft"
}

# 3. Listar contratos
GET https://[BACKEND_URL]/api/contracts
Authorization: Bearer [TOKEN]
```

### 3. Verificar Limites por Plano

- **Trial**: Máximo 5 contratos
- **Basic**: Máximo 50 contratos
- **Pro**: Máximo 500 contratos
- **Enterprise**: Ilimitado (-1)

---

## 📝 NOTAS IMPORTANTES

1. **Migration Automática**: A migration será executada automaticamente quando o backend iniciar, através da função `init_db()` no `main.py`.

2. **Variáveis de Ambiente**: Certifique-se de que todas as variáveis de ambiente estão configuradas no Cloud Run, especialmente:
   - `DATABASE_URL`
   - `JWT_SECRET_KEY`
   - `STRIPE_SECRET_KEY`

3. **CORS**: Os endpoints de contratos já estão incluídos na configuração CORS do backend.

4. **Autenticação**: Todos os endpoints de contratos requerem autenticação JWT via `get_current_user`.

---

## 🐛 TROUBLESHOOTING

### Problema: Migration não executou

**Solução:**
```powershell
# Executar migration manualmente via Cloud Run
gcloud run jobs create run-migration `
    --image gcr.io/ifrs16-app/ifrs16-backend `
    --region us-central1 `
    --project ifrs16-app `
    --command "alembic" `
    --args "upgrade,head"
```

### Problema: Erro "Tabela não existe"

**Solução:**
1. Verificar se a migration foi executada
2. Verificar logs do backend para erros
3. Executar migration manualmente

### Problema: Erro de conexão com banco

**Solução:**
1. Verificar `DATABASE_URL` no Cloud Run
2. Verificar se Cloud SQL connection está configurada
3. Verificar se o Cloud Run tem permissão para acessar Cloud SQL

---

## ✅ CHECKLIST DE DEPLOY

- [ ] Build da imagem Docker executado com sucesso
- [ ] Deploy no Cloud Run executado com sucesso
- [ ] Migration executada (tabela `contracts` existe)
- [ ] Endpoints de contratos respondendo corretamente
- [ ] Autenticação funcionando
- [ ] Limites por plano funcionando
- [ ] Testes passando

---

**Status:** ✅ **Código implementado e pronto para deploy**

**Próximo passo:** Execute o deploy conforme instruções acima.

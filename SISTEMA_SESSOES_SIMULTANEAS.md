# Sistema de Controle de Sessões Simultâneas

## 📋 Resumo

Implementado sistema completo para prevenir compartilhamento de conta através do controle de sessões simultâneas. O sistema rastreia dispositivos ativos e limita o número de sessões baseado no plano de assinatura do usuário.

## ✅ O Que Foi Implementado

### Backend

#### 1. Modelo de Dados (`backend/app/models.py`)
- **Tabela `user_sessions`**: Rastreia todas as sessões ativas de usuários
- **Campos**:
  - `id`: UUID único da sessão
  - `user_id`: Referência ao usuário (FK com CASCADE DELETE)
  - `session_token`: Token único da sessão (UUID)
  - `device_fingerprint`: Fingerprint do dispositivo (user-agent + IP)
  - `ip_address`: Endereço IP do dispositivo
  - `user_agent`: String completa do user-agent
  - `device_name`: Nome amigável do dispositivo (Windows PC, Mac, iOS, etc.)
  - `last_activity`: Timestamp da última atividade
  - `created_at`: Data de criação da sessão
  - `expires_at`: Data de expiração (24 horas após criação)
  - `is_active`: Flag booleana de sessão ativa

- **Índices** para performance:
  - `idx_user_sessions_user_id` em `user_id`
  - `idx_user_sessions_token` em `session_token`
  - `idx_user_sessions_active` em `(user_id, is_active)`
  - `idx_user_sessions_expires` em `expires_at`

#### 2. Endpoints de Gerenciamento (`backend/app/routers/auth.py`)

**POST `/api/auth/sessions/register`**
- Registra nova sessão de usuário
- Valida limite de sessões baseado no plano
- Invalida sessão mais antiga se limite atingido
- Retorna `session_token` para o cliente

**POST `/api/auth/sessions/heartbeat?session_token={token}`**
- Atualiza timestamp de `last_activity`
- Valida se sessão ainda está ativa e não expirou
- Retorna erro 401 se sessão expirada

**POST `/api/auth/sessions/terminate?session_token={token}`**
- Encerra uma sessão específica (logout)
- Marca `is_active` como `False`

**GET `/api/auth/sessions/active`**
- Lista todas as sessões ativas do usuário
- Útil para dashboard mostrar dispositivos conectados

#### 3. Integração com Login
- Login (`POST /api/auth/login`) agora:
  1. Valida credenciais
  2. Busca plano de assinatura do usuário
  3. Conta sessões ativas
  4. Invalida sessão mais antiga se limite atingido
  5. Cria nova sessão automaticamente
  6. Retorna `session_token` junto com `access_token`

#### 4. Limites por Plano
```python
SESSION_LIMITS = {
    "basic_monthly": 1,    # 1 dispositivo
    "basic_yearly": 1,     # 1 dispositivo
    "pro_monthly": 2,      # 2 dispositivos
    "pro_yearly": 2,       # 2 dispositivos
    "enterprise_monthly": 5,  # 5 dispositivos
    "enterprise_yearly": 5,   # 5 dispositivos
}
```

#### 5. Task de Limpeza (`backend/app/tasks/cleanup_sessions.py`)
- Script Python para limpar sessões expiradas
- Remove automaticamente sessões onde `expires_at < now`
- Pode ser executado manualmente:
  ```bash
  python -m backend.app.tasks.cleanup_sessions
  ```
- Ou configurado como Cron Job no Google Cloud

### Frontend

#### 1. Session Manager (`assets/js/session-manager.js`)
- **Classe `SessionManager`**:
  - `startHeartbeat()`: Inicia envio periódico de heartbeat (5 minutos)
  - `sendHeartbeat()`: Envia POST para `/api/auth/sessions/heartbeat`
  - `stopHeartbeat()`: Para o intervalo de heartbeat
  - `handleSessionExpired()`: Redireciona para login quando sessão expira
  - `terminateSession()`: Encerra sessão (logout)
  - `listActiveSessions()`: Lista dispositivos conectados

- **Auto-inicialização**: Se houver `session_token` no localStorage, inicia heartbeat automaticamente

#### 2. Integração no Login (`login.html`)
- Salva `session_token` retornado pelo backend no `localStorage`
- Session token é usado pelo SessionManager para heartbeat

#### 3. Integração no Dashboard (`dashboard.html`)
- Script `session-manager.js` carregado automaticamente
- Heartbeat mantém sessão ativa enquanto usuário navega
- Se sessão expirar ou for invalidada (login em outro dispositivo), usuário é redirecionado para login

### Migração do Banco de Dados

#### Arquivo de Migração
**`backend/alembic/versions/add_user_sessions_table.py`**

Cria a tabela `user_sessions` com todos os campos e índices.

## 🚀 Deploy Realizado

### Backend
- ✅ Código commitado e pushed para GitHub (branch: `Ajustes`)
- ⚠️  Deploy do backend falhou devido a variáveis de ambiente do Stripe faltando
- ✅ Revisão anterior (00092) ainda está ativa e funcional
- ⏳ **PENDENTE**: Re-deploy do backend após configurar variáveis de ambiente

### Frontend
- ✅ Deployado no Firebase Hosting
- ✅ URL: https://ifrs16-app.web.app
- ✅ Session Manager está ativo

### Banco de Dados
- ⏳ **PENDENTE**: Executar migração SQL no PostgreSQL

## 📝 Próximos Passos

### 1. Executar Migração do Banco de Dados

Conecte-se ao PostgreSQL no Google Cloud e execute:

```sql
-- Criar tabela user_sessions
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(500) NOT NULL UNIQUE,
    device_fingerprint VARCHAR(255),
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    device_name VARCHAR(255),
    last_activity TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at);

-- Verificar
SELECT table_name FROM information_schema.tables WHERE table_name='user_sessions';
```

**Opções para executar**:
- Via Cloud SQL Studio no Console do Google Cloud
- Via psql local conectando ao Cloud SQL Proxy
- Via Cloud Run Job com Alembic

### 2. Re-Deploy do Backend

Após executar a migração, fazer novo deploy:

```bash
cd backend
gcloud run deploy ifrs16-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="ENVIRONMENT=production"
```

### 3. Configurar Cloud Scheduler (Opcional)

Para limpeza automática de sessões expiradas:

```bash
# Criar Cloud Run Job para cleanup
gcloud run jobs create cleanup-sessions \
  --image=gcr.io/ifrs16-app/backend \
  --region=us-central1 \
  --command="python" \
  --args="-m,backend.app.tasks.cleanup_sessions"

# Configurar Cloud Scheduler para executar diariamente à meia-noite
gcloud scheduler jobs create http cleanup-sessions-daily \
  --location=us-central1 \
  --schedule="0 0 * * *" \
  --uri="https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/ifrs16-app/jobs/cleanup-sessions:run" \
  --http-method=POST \
  --oauth-service-account-email=PROJECT_ID@appspot.gserviceaccount.com
```

## 🔒 Segurança e Funcionamento

### Como Funciona

1. **Login**:
   - Usuário faz login
   - Backend cria nova sessão e retorna `session_token`
   - Frontend salva token no localStorage
   - SessionManager inicia heartbeat automático

2. **Navegação**:
   - A cada 5 minutos, frontend envia heartbeat
   - Backend atualiza `last_activity` da sessão
   - Sessão permanece ativa

3. **Novo Login em Outro Dispositivo**:
   - Se usuário já tem sessões = limite do plano:
     - Backend invalida sessão mais antiga
     - Dispositivo antigo recebe erro 401 no próximo heartbeat
     - Dispositivo antigo é redirecionado para login
   - Nova sessão é criada para novo dispositivo

4. **Expiração**:
   - Sessões expiram após 24 horas de inatividade
   - Heartbeat estende a expiração
   - Se sessão expirar, próximo heartbeat retorna 401
   - Usuário é redirecionado para login

### Cenários de Teste

**Cenário 1: Usuário Basic tenta usar em 2 dispositivos**
- Login no PC → Sessão 1 criada
- Login no celular → Sessão 1 invalidada, Sessão 2 criada
- PC recebe 401 no próximo heartbeat e é desconectado

**Cenário 2: Usuário Pro usa em 2 dispositivos**
- Login no PC → Sessão 1 criada
- Login no celular → Sessão 2 criada (limite: 2)
- Ambos funcionam normalmente
- Login no tablet → Sessão 1 invalidada, Sessão 3 criada
- PC é desconectado

**Cenário 3: Sessão expira por inatividade**
- Usuário deixa aba aberta mas computador dorme
- Heartbeat para de funcionar
- Após 24h, sessão expira
- Ao retornar, heartbeat falha e redireciona para login

## 📊 Monitoramento

### Verificar Sessões Ativas

```sql
-- Ver todas as sessões ativas
SELECT
    u.email,
    s.device_name,
    s.ip_address,
    s.created_at,
    s.last_activity,
    s.expires_at
FROM user_sessions s
JOIN users u ON s.user_id = u.id
WHERE s.is_active = TRUE
ORDER BY s.last_activity DESC;

-- Contar sessões por usuário
SELECT
    u.email,
    COUNT(*) as active_sessions
FROM user_sessions s
JOIN users u ON s.user_id = u.id
WHERE s.is_active = TRUE
  AND s.expires_at > NOW()
GROUP BY u.email
ORDER BY active_sessions DESC;
```

### Logs Importantes

**Backend**:
- `[OK] Login bem-sucedido: {email} (device: {device}, IP: {ip})`
- `[INFO] Sessão antiga invalidada para {email} (device: {device})`

**Frontend**:
- `[SessionManager] Iniciando heartbeat da sessão...`
- `[SessionManager] Heartbeat enviado com sucesso`
- `[SessionManager] Sessão inválida: {erro}`

## 🎯 Benefícios

1. **Previne Compartilhamento**: Usuários não podem compartilhar conta entre múltiplos dispositivos além do limite do plano
2. **Monetização**: Incentiva upgrade para planos superiores para mais dispositivos
3. **Segurança**: Sessões expiram automaticamente após inatividade
4. **Auditoria**: Histórico completo de acessos por dispositivo e IP
5. **UX**: Usuário não precisa fazer nada, tudo funciona automaticamente

## 📁 Arquivos Modificados/Criados

### Backend
- ✅ `backend/app/models.py` - Modelo UserSession
- ✅ `backend/app/routers/auth.py` - Endpoints de sessão + integração no login
- ✅ `backend/app/schemas.py` - Campo session_token em TokenResponse
- ✅ `backend/alembic/versions/add_user_sessions_table.py` - Migração
- ✅ `backend/app/tasks/__init__.py` - Módulo de tasks
- ✅ `backend/app/tasks/cleanup_sessions.py` - Script de limpeza

### Frontend
- ✅ `assets/js/session-manager.js` - Gerenciador de sessão (NOVO)
- ✅ `login.html` - Salva session_token
- ✅ `dashboard.html` - Carrega session-manager.js

### Documentação
- ✅ `SISTEMA_SESSOES_SIMULTANEAS.md` - Este arquivo

## 🔗 Commit

```
Implementado sistema de controle de sessões simultâneas

Backend:
- Criado modelo UserSession para rastrear sessões ativas
- Migração Alembic para tabela user_sessions
- Endpoints de gerenciamento de sessão
- Integrado registro automático de sessão no login
- Validação de limite de sessões por plano
- Tracking de device, IP, user-agent e fingerprint

Frontend:
- Criado SessionManager JavaScript para heartbeat automático
- Heartbeat a cada 5 minutos mantém sessão ativa
- Session token salvo no localStorage durante login
- Auto-detecção de sessão expirada

Tasks:
- Script de limpeza automática de sessões expiradas

Segurança:
- Previne compartilhamento de conta
- Sessões expiram em 24 horas
- Limite baseado no plano de assinatura
```

---

**Data de Implementação**: 31 de Dezembro de 2025
**Status**: ✅ Código completo e deployado
**Pendências**: Migração do banco de dados + Re-deploy backend

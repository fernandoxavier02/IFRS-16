# Acesso Rápido - IFRS 16 API

## 🌐 URLs do Sistema (Localhost)

### API Backend
- **Base URL:** http://localhost:8000
- **Health Check:** http://localhost:8000/health
- **Swagger Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Frontend (quando disponível)
- **Dashboard:** http://localhost:5500/dashboard.html
- **Pricing:** http://localhost:5500/pricing.html
- **Register:** http://localhost:5500/register.html
- **Login:** http://localhost:5500/login.html

---

## 🔑 Endpoints de Teste

### 1. Registrar Novo Usuário
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "teste@example.com",
    "name": "Teste User",
    "password": "senha123",
    "company_name": "Empresa Teste"
  }'
```

### 2. Fazer Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "teste@example.com",
    "password": "senha123"
  }'
```

### 3. Listar Planos
```bash
curl http://localhost:8000/api/payments/prices
```

### 4. Validar Licença
```bash
curl -X POST http://localhost:8000/api/validate-license \
  -H "Content-Type: application/json" \
  -d '{
    "key": "FX20250130-IFRS16-ABC123",
    "machine_id": "my-computer-001"
  }'
```

### 5. Obter Dados do Usuário (requer token)
```bash
TOKEN="seu_token_aqui"
curl http://localhost:8000/api/user/me \
  -H "Authorization: Bearer $TOKEN"
```

### 6. Verificar Assinatura (requer token)
```bash
TOKEN="seu_token_aqui"
curl http://localhost:8000/api/user/subscription \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🛠️ Comandos Úteis

### Iniciar Backend
```bash
cd "c:\Projetos\IFRS 16 (do replit para o Cursor)\IFRS 16-20251217T150830Z-1-001\IFRS 16\backend"
source venv/Scripts/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Parar Servidor
```
Ctrl + C
```

### Ver Logs do Servidor
```bash
# Logs em tempo real no terminal
```

### Executar Testes
```bash
cd backend
source venv/Scripts/activate
pytest tests/ -v
```

### Aplicar Migrations
```bash
cd backend
source venv/Scripts/activate
alembic upgrade head
```

### Ver Migrations Aplicadas
```bash
cd backend
source venv/Scripts/activate
alembic current
```

---

## 📊 Monitoramento

### Verificar se API está Online
```bash
curl http://localhost:8000/health
```
**Resposta esperada:**
```json
{"status": "healthy", "environment": "development"}
```

### Ver Versão da API
```bash
curl http://localhost:8000/
```
**Resposta esperada:**
```json
{
  "name": "IFRS 16 License API",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs",
  "redoc": "/redoc"
}
```

---

## 🔐 Credenciais de Teste

### Admin
- **Email:** (criar via script create_admin.py)
- **Token:** (ver em ADMIN_TOKEN no .env)

### Usuário de Teste
- **Email:** teste@example.com
- **Senha:** senha123
- **Company:** Empresa Teste

---

## 🗄️ Banco de Dados

### Ver Usuários
```bash
cd backend
python ver_usuarios.py
```

### Consultas Rápidas
```bash
# Ver estrutura completa
python ver_usuarios.py

# Ver licenças (criar script se necessário)
python ver_licencas.py

# Ver assinaturas (criar script se necessário)
python ver_assinaturas.py
```

**Mais detalhes:** [COMANDOS_BANCO_DADOS.md](COMANDOS_BANCO_DADOS.md)

---

## 📚 Documentação

### Arquivos de Referência
- [FLUXO_REGISTRO_E_ASSINATURA.md](FLUXO_REGISTRO_E_ASSINATURA.md) - Fluxo completo de registro e assinatura
- [FLUXO_EMAILS_ASSINATURA.md](FLUXO_EMAILS_ASSINATURA.md) - Fluxo de envio de emails de confirmação
- [CORRECOES_EMAILS_APLICADAS.md](CORRECOES_EMAILS_APLICADAS.md) - Correções aplicadas no fluxo de emails
- [RESUMO_IMPLEMENTACAO_REGISTRO_ASSINATURA.md](RESUMO_IMPLEMENTACAO_REGISTRO_ASSINATURA.md) - Resumo executivo da implementação
- [BUILD_E_DEPLOY_CONCLUIDO.md](BUILD_E_DEPLOY_CONCLUIDO.md) - Status do build e deploy
- [CONFIGURACAO_PLANOS_ATUALIZADA.md](CONFIGURACAO_PLANOS_ATUALIZADA.md) - Configuração dos planos
- [COMANDOS_BANCO_DADOS.md](COMANDOS_BANCO_DADOS.md) - Como visualizar o banco de dados

### Código
- [backend/app/main.py](backend/app/main.py) - Arquivo principal da API
- [backend/app/routers/auth.py](backend/app/routers/auth.py) - Endpoints de autenticação
- [backend/app/routers/payments.py](backend/app/routers/payments.py) - Endpoints de pagamento
- [backend/app/models.py](backend/app/models.py) - Modelos do banco de dados
- [backend/app/config.py](backend/app/config.py) - Configuração de planos e limites

---

## 🚀 Quick Start

1. **Abrir Terminal no Backend:**
   ```bash
   cd "c:\Projetos\IFRS 16 (do replit para o Cursor)\IFRS 16-20251217T150830Z-1-001\IFRS 16\backend"
   ```

2. **Ativar Ambiente Virtual:**
   ```bash
   source venv/Scripts/activate
   ```

3. **Iniciar Servidor:**
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Abrir Documentação:**
   - Navegador: http://localhost:8000/docs

5. **Testar Endpoint:**
   ```bash
   curl http://localhost:8000/health
   ```

---

**Sistema pronto para uso! 🎉**

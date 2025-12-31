# Guia de Testes - Sistema de Sessões Simultâneas

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Testes Backend](#testes-backend)
3. [Testes Frontend](#testes-frontend)
4. [Testes Manuais](#testes-manuais)
5. [Testes de Carga](#testes-de-carga)
6. [Métricas de Sucesso](#métricas-de-sucesso)

---

## Visão Geral

O sistema de sessões simultâneas possui **3 suítes de testes**:

1. **Testes Unitários Backend** (`test_sessions.py`) - 25 testes
2. **Testes E2E Backend** (`test_sessions_e2e.py`) - 7 cenários completos
3. **Testes Frontend** (`session-manager.test.js`) - 30 testes

**Total**: **62 testes automatizados**

---

## Testes Backend

### Configuração

```bash
cd backend

# Instalar dependências de teste
pip install pytest pytest-asyncio httpx

# Executar todos os testes
pytest tests/test_sessions.py tests/test_sessions_e2e.py -v

# Executar apenas testes de sessão
pytest tests/test_sessions.py -v

# Executar com coverage
pytest tests/test_sessions.py --cov=app.routers.auth --cov=app.models --cov-report=html
```

### Testes Unitários (`test_sessions.py`)

**25 testes cobrindo:**

#### 1. Login e Criação de Sessão
- ✅ Login cria sessão automaticamente
- ✅ Login registra informações do dispositivo
- ✅ Device detection (Windows, Mac, iOS, Android, Linux)

#### 2. Limites de Sessões por Plano
- ✅ Usuário Basic limitado a 1 sessão
- ✅ Usuário Pro pode ter 2 sessões
- ✅ 3º login de Pro invalida sessão mais antiga
- ✅ Usuário Enterprise pode ter 5 sessões
- ✅ Usuário sem assinatura limitado a 1 sessão

#### 3. Heartbeat
- ✅ Heartbeat atualiza `last_activity`
- ✅ Heartbeat falha com token inválido
- ✅ Heartbeat falha para sessão expirada
- ✅ Heartbeat falha para sessão inativa
- ✅ Heartbeat não pode acessar sessão de outro usuário

#### 4. Encerramento de Sessão
- ✅ Terminate marca sessão como inativa
- ✅ Não pode encerrar sessão de outro usuário

#### 5. Listagem de Sessões
- ✅ Lista sessões ativas do usuário
- ✅ Exclui sessões inativas da listagem

#### 6. Expiração
- ✅ Sessão expira após 24 horas

#### 7. Cleanup
- ✅ Cleanup remove sessões expiradas
- ✅ Cleanup preserva sessões ativas

#### 8. Concorrência
- ✅ Logins concorrentes tratados corretamente

### Testes E2E (`test_sessions_e2e.py`)

**7 cenários de uso real:**

#### Cenário 1: Tentativa de Compartilhamento
```
História: Família tenta compartilhar conta Basic

1. Pai faz login no PC
2. Mãe faz login no Mac → Pai é desconectado
3. Filho faz login no iPhone → Mãe é desconectada
4. Pai tenta heartbeat → Erro 404

✅ Testa: Limite de 1 sessão, invalidação automática
```

#### Cenário 2: Uso Legítimo com Pro
```
História: Empresa usa plano Pro corretamente

1. Login no desktop do escritório
2. Login no notebook (home office)
3. Ambos coexistem (Pro permite 2)
4. Heartbeat funciona em ambos
5. 3º login invalida desktop

✅ Testa: Limite de 2 sessões, coexistência
```

#### Cenário 3: Sessão Expirada por Inatividade
```
História: Usuário deixou aba aberta mas PC dormiu

1. Login
2. Sessão expira após 24h de inatividade
3. Heartbeat retorna 401
4. Frontend redireciona para login

✅ Testa: Expiração por inatividade
```

#### Cenário 4: Upgrade de Plano
```
História: Upgrade de Basic para Pro

1. Basic: 1 dispositivo
2. Tenta 2º → 1º desconectado
3. Faz upgrade para Pro
4. Agora pode usar 2 dispositivos

✅ Testa: Mudança de limites após upgrade
```

#### Cenário 5: Detecção de Compartilhamento Suspeito
```
História: Login em locais diferentes

1. Login em São Paulo (IP BR)
2. Login em NY (IP US) 5 min depois
3. Sistema registra histórico completo
4. Admin pode auditar comportamento

✅ Testa: Auditoria e histórico
```

#### Cenário 6: Logout Explícito
```
História: Usuário faz logout

1. Login
2. Clica em "Sair"
3. Sessão encerrada
4. Heartbeat falha
5. Novo login funciona

✅ Testa: Encerramento manual
```

#### Cenário 7: Performance com Múltiplos Usuários
```
História: 50 usuários fazem login simultâneo

1. Criar 50 usuários
2. Todos fazem login ao mesmo tempo
3. Sistema não trava
4. 50 sessões criadas

✅ Testa: Escalabilidade e concorrência
```

### Executar Teste Específico

```bash
# Apenas teste de compartilhamento
pytest tests/test_sessions_e2e.py::test_cenario_familia_compartilhando -v

# Apenas teste de upgrade
pytest tests/test_sessions_e2e.py::test_cenario_upgrade_de_plano -v
```

---

## Testes Frontend

### Configuração

```bash
cd tests

# Instalar dependências
npm install

# Executar testes
npm test

# Executar com watch mode
npm run test:watch

# Gerar coverage
npm run test:coverage
```

### Testes do SessionManager (`session-manager.test.js`)

**30 testes cobrindo:**

#### 1. Inicialização
- ✅ Cria instância com propriedades corretas
- ✅ Retorna URL correta para produção
- ✅ Retorna URL local para desenvolvimento

#### 2. startHeartbeat()
- ✅ Não inicia sem session_token
- ✅ Inicia corretamente com token
- ✅ Limpa intervalo anterior

#### 3. sendHeartbeat()
- ✅ Envia requisição POST correta
- ✅ Loga sucesso
- ✅ Para heartbeat em erro 401
- ✅ Para heartbeat em erro 404
- ✅ Loga erro de conexão
- ✅ Não envia sem tokens

#### 4. stopHeartbeat()
- ✅ Limpa intervalo
- ✅ Não dá erro se não houver intervalo
- ✅ Loga interrupção

#### 5. handleSessionExpired()
- ✅ Mostra alerta ao usuário
- ✅ Limpa localStorage
- ✅ Redireciona para login após 2s

#### 6. terminateSession()
- ✅ Envia requisição terminate
- ✅ Para heartbeat após encerrar
- ✅ Loga sucesso
- ✅ Para heartbeat mesmo em erro

#### 7. listActiveSessions()
- ✅ Retorna lista de sessões
- ✅ Retorna array vazio em erro
- ✅ Retorna array vazio sem token

#### 8. Fluxo Completo
- ✅ Gerencia ciclo de vida completo

---

## Testes Manuais

### Checklist de Testes Manuais

#### 1. Login e Registro de Sessão
- [ ] Fazer login e verificar que `session_token` é salvo no localStorage
- [ ] Verificar no banco que sessão foi criada
- [ ] Confirmar que device_name está correto

#### 2. Heartbeat Automático
- [ ] Abrir DevTools → Network
- [ ] Aguardar 5 minutos
- [ ] Verificar requisição POST para `/api/auth/sessions/heartbeat`
- [ ] Verificar que retorna 200 OK

#### 3. Limite de Sessões - Basic
- [ ] Login em Chrome (PC)
- [ ] Login em Firefox (mesmo PC)
- [ ] Chrome deve ser desconectado automaticamente
- [ ] Tentar heartbeat no Chrome → erro 404

#### 4. Limite de Sessões - Pro
- [ ] Login em 2 dispositivos diferentes
- [ ] Ambos devem funcionar
- [ ] Login em 3º dispositivo
- [ ] 1º dispositivo deve ser desconectado

#### 5. Sessão Expirada
- [ ] Fazer login
- [ ] Manualmente expirar sessão no banco: `UPDATE user_sessions SET expires_at = NOW() - INTERVAL '1 hour'`
- [ ] Aguardar próximo heartbeat (max 5 min)
- [ ] Verificar alerta e redirecionamento para login

#### 6. Logout
- [ ] Fazer login
- [ ] Clicar em "Sair"
- [ ] Verificar redirecionamento para login
- [ ] Verificar que localStorage foi limpo

#### 7. Listar Sessões Ativas
- [ ] Fazer login em 2 dispositivos (usuário Pro)
- [ ] Chamar endpoint `/api/auth/sessions/active`
- [ ] Verificar que retorna 2 sessões
- [ ] Verificar dados de cada sessão (device, IP, timestamps)

---

## Testes de Carga

### Setup

```bash
# Instalar locust
pip install locust
```

### Script de Teste de Carga

Criar `locustfile.py`:

```python
from locust import HttpUser, task, between
import uuid

class SessionUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Executado quando usuário inicia"""
        # Criar usuário único
        self.email = f"load-test-{uuid.uuid4()}@test.com"
        self.password = "Test123!"

        # Registrar
        self.client.post("/api/auth/register", json={
            "email": self.email,
            "name": "Load Test User",
            "password": self.password
        })

        # Fazer login
        response = self.client.post("/api/auth/login", json={
            "email": self.email,
            "password": self.password
        })
        data = response.json()
        self.auth_token = data["access_token"]
        self.session_token = data["session_token"]

    @task(10)
    def heartbeat(self):
        """Enviar heartbeat (peso 10 - mais frequente)"""
        self.client.post(
            f"/api/auth/sessions/heartbeat?session_token={self.session_token}",
            headers={"Authorization": f"Bearer {self.auth_token}"}
        )

    @task(1)
    def list_sessions(self):
        """Listar sessões (peso 1 - menos frequente)"""
        self.client.get(
            "/api/auth/sessions/active",
            headers={"Authorization": f"Bearer {self.auth_token}"}
        )
```

### Executar Teste de Carga

```bash
# Teste local
locust -f locustfile.py --host=http://localhost:8000

# Teste produção
locust -f locustfile.py --host=https://ifrs16-backend-1051753255664.us-central1.run.app

# Abrir http://localhost:8089
# Configurar:
# - Number of users: 100
# - Spawn rate: 10 users/second
```

### Métricas Esperadas

- **Heartbeat**: < 200ms (p95)
- **List sessions**: < 500ms (p95)
- **Taxa de erro**: < 1%
- **Throughput**: > 1000 req/s

---

## Métricas de Sucesso

### Coverage Backend
```bash
pytest --cov=app --cov-report=html
```

**Meta**: > 85% coverage

### Coverage Frontend
```bash
npm run test:coverage
```

**Meta**: > 80% coverage

### Resultados Esperados

#### Backend (35 testes)
- ✅ 25 testes unitários
- ✅ 7 testes E2E
- ✅ 3 testes de edge cases
- ⏱️  Tempo: < 30 segundos

#### Frontend (30 tests)
- ✅ 3 testes de inicialização
- ✅ 6 testes de heartbeat
- ✅ 4 testes de stop
- ✅ 3 testes de sessão expirada
- ✅ 4 testes de terminate
- ✅ 3 testes de listagem
- ✅ 7 testes diversos
- ⏱️  Tempo: < 10 segundos

### Comandos Rápidos

```bash
# Executar TODOS os testes
cd backend && pytest tests/test_sessions*.py -v && cd ../tests && npm test

# Apenas backend
cd backend && pytest tests/test_sessions*.py -v

# Apenas frontend
cd tests && npm test

# Coverage completo
cd backend && pytest tests/test_sessions*.py --cov=app --cov-report=html
cd ../tests && npm run test:coverage
```

---

## Troubleshooting

### Problema: Testes falhando por timeout
**Solução**: Aumentar timeout no pytest
```bash
pytest tests/test_sessions.py --timeout=30
```

### Problema: Database locked no SQLite
**Solução**: Usar NullPool (já configurado no conftest.py)

### Problema: Testes frontend não encontram arquivo
**Solução**: Verificar path no `session-manager.test.js`:
```javascript
const sessionManagerCode = fs.readFileSync(
    path.join(__dirname, '..', 'assets', 'js', 'session-manager.js'),
    'utf8'
);
```

---

## Relatório de Testes

Após executar, gerar relatório:

```bash
# Backend
pytest tests/test_sessions*.py --html=report.html --self-contained-html

# Frontend
npm test -- --coverage --coverageReporters=html
```

Arquivos gerados:
- `backend/report.html` - Relatório backend
- `tests/coverage/index.html` - Coverage frontend

---

## Integração Contínua (CI/CD)

### GitHub Actions

Criar `.github/workflows/test-sessions.yml`:

```yaml
name: Testes de Sessões

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio httpx pytest-cov
      - name: Run tests
        run: |
          cd backend
          pytest tests/test_sessions*.py --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: 18
      - name: Install dependencies
        run: |
          cd tests
          npm install
      - name: Run tests
        run: |
          cd tests
          npm test -- --coverage
```

---

**Total de Testes**: 62
**Tempo Estimado**: < 1 minuto
**Coverage Esperado**: > 85%

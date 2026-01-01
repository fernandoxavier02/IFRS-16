# 📋 Plano de Implementação de Melhorias - IFRS 16

**Data de Criação:** 2026-01-01  
**Última Atualização:** 2026-01-01  
**Status:** 📝 Documentação Inicial

---

## 📊 Visão Geral

Este documento detalha o plano de implementação das melhorias identificadas após análise de mercado e comparação com concorrentes. Cada funcionalidade foi priorizada considerando:

- **Impacto no usuário final**
- **Complexidade técnica**
- **Dependências entre funcionalidades**
- **Risco de quebrar código existente**
- **Valor comercial**

---

## 🎯 Funcionalidades Prioritizadas

### Fase 1 - Alta Prioridade (MVP de Melhorias)
1. ✅ **API de Índices Econômicos** (base para remensuração)
2. ⬜ **Sistema de Alertas e Notificações**
3. ⬜ **Upload e Gestão de Documentos**
4. ⬜ **Dashboard Analítico Melhorado**

### Fase 2 - Média Prioridade (Diferenciação)
5. ⬜ **Notas Explicativas Automatizadas**
6. ⬜ **Simulação de Cenários**
7. ⬜ **Remensuração Automática Mensal** (depende da API de índices)
8. ⬜ **Auditoria e Rastreabilidade**

### Fase 3 - Baixa Prioridade (Expansão)
9. ⬜ **Workflow de Aprovação**
10. ⬜ **Integração com Sistemas Contábeis**
11. ⬜ **Multi-idioma**
12. ⬜ **API GraphQL**
13. ⬜ **Suporte Multi-moeda**

---

## 📝 Legenda de Status

- ⬜ **Não iniciado** - Ainda não começou
- 🟡 **Em progresso** - Trabalho em andamento
- ✅ **Concluído** - Implementado e testado
- ❌ **Bloqueado** - Aguardando dependência ou decisão
- ⚠️ **Problema** - Erro identificado, precisa correção

---

# FASE 1 - ALTA PRIORIDADE

---

## 🎯 Funcionalidade 1: API de Índices Econômicos

**Prioridade:** 🔴 Crítica  
**Complexidade:** Média  
**Dependências:** Nenhuma  
**Base para:** Remensuração Automática

### Objetivo
Criar API completa para buscar e armazenar índices econômicos do Banco Central do Brasil (SELIC, IGPM, IPCA, CDI, INPC, TR).

---

### 📋 Etapa 1.1: Criar Modelo de Dados

**Objetivo:** Definir estrutura de dados para índices econômicos

#### Tarefas:
- [ ] 1.1.1 Criar modelo `EconomicIndex` em `backend/app/models.py`
  - Campos: `id`, `index_type`, `reference_date`, `value`, `source`, `created_at`
  - Enum para tipos: SELIC, IGPM, IPCA, CDI, INPC, TR
  - Índices: `idx_economic_indexes_type_date` (index_type + reference_date)

- [ ] 1.1.2 Criar schema Pydantic em `backend/app/schemas.py`
  - `EconomicIndexCreate`, `EconomicIndexOut`, `EconomicIndexListOut`

- [ ] 1.1.3 Criar migration Alembic
  - Arquivo: `backend/alembic/versions/YYYYMMDD_HHMMSS_add_economic_indexes_table.py`
  - Criar tabela `economic_indexes` com constraints e índices

#### Testes:
- [ ] **Teste 1.1.1:** Verificar se modelo pode ser importado sem erros
  ```python
  from app.models import EconomicIndex
  assert EconomicIndex is not None
  ```

- [ ] **Teste 1.1.2:** Verificar se migration pode ser aplicada
  ```bash
  cd backend
  alembic upgrade head
  # Verificar se tabela foi criada
  ```

- [ ] **Teste 1.1.3:** Verificar constraints do modelo
  - Testar inserção válida
  - Testar inserção duplicada (mesmo tipo + data) - deve falhar
  - Testar inserção com valores nulos obrigatórios - deve falhar

#### Checklist de Validação:
- [ ] Migration criada e testada localmente
- [ ] Modelo importa sem erros
- [ ] Constraints funcionando (unicidade tipo+data)
- [ ] Nenhum teste existente quebrado

---

### 📋 Etapa 1.2: Criar Repository

**Objetivo:** Camada de acesso a dados para índices econômicos

#### Tarefas:
- [ ] 1.2.1 Criar `EconomicIndexRepository` em `backend/app/repositories/economic_indexes.py`
  - Métodos: `create()`, `get_by_type_and_date()`, `list_by_type()`, `list_all()`, `get_latest()`
  - Usar SQLAlchemy async

- [ ] 1.2.2 Implementar tratamento de erros
  - `IndexNotFoundError` custom exception
  - Logging apropriado

#### Testes:
- [ ] **Teste 1.2.1:** Testar criação de índice
  ```python
  async def test_create_economic_index():
      repo = EconomicIndexRepository(db)
      index = await repo.create(
          index_type="SELIC",
          reference_date=date(2024, 1, 1),
          value=12.75,
          source="BCB"
      )
      assert index.id is not None
      assert index.index_type == "SELIC"
  ```

- [ ] **Teste 1.2.2:** Testar busca por tipo e data
  ```python
  async def test_get_by_type_and_date():
      # Criar índice
      # Buscar pelo mesmo tipo e data
      # Verificar se retorna o índice correto
  ```

- [ ] **Teste 1.2.3:** Testar busca do mais recente
  ```python
  async def test_get_latest():
      # Criar múltiplos índices com datas diferentes
      # Buscar latest
      # Verificar se retorna o mais recente
  ```

- [ ] **Teste 1.2.4:** Testar listagem por tipo
  ```python
  async def test_list_by_type():
      # Criar índices de tipos diferentes
      # Listar por tipo específico
      # Verificar se retorna apenas do tipo especificado
  ```

#### Checklist de Validação:
- [ ] Todos os métodos do repository implementados
- [ ] Testes unitários passando (cobertura > 80%)
- [ ] Erros tratados adequadamente
- [ ] Nenhum teste existente quebrado

---

### 📋 Etapa 1.3: Criar Service com Integração BCB

**Objetivo:** Lógica de negócio e integração com API do Banco Central

#### Tarefas:
- [ ] 1.3.1 Criar `EconomicIndexService` em `backend/app/services/economic_index_service.py`
  - Método: `fetch_from_bcb(index_type: str, reference_date: date) -> EconomicIndex`
  - Método: `sync_index_from_bcb(index_type: str) -> List[EconomicIndex]`
  - Método: `get_or_fetch(index_type: str, reference_date: date) -> EconomicIndex`

- [ ] 1.3.2 Implementar integração com API BCB
  - URL base: `https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados`
  - Códigos BCB:
    - SELIC: 432
    - IGPM: 189
    - IPCA: 433
    - CDI: 12
    - INPC: 188
    - TR: 226
  - Usar `httpx` para requisições async
  - Tratar erros de rede e timeouts

- [ ] 1.3.3 Implementar cache/verificação de existência
  - Antes de buscar no BCB, verificar se já existe no banco
  - Se existir e for recente (últimos 30 dias), usar do banco

#### Testes:
- [ ] **Teste 1.3.1:** Testar busca única do BCB (mockado)
  ```python
  @pytest.mark.asyncio
  async def test_fetch_from_bcb_mocked():
      service = EconomicIndexService(db)
      # Mockar httpx.get para retornar dados fictícios do BCB
      index = await service.fetch_from_bcb("SELIC", date(2024, 1, 1))
      assert index.value > 0
      assert index.source == "BCB"
  ```

- [ ] **Teste 1.3.2:** Testar get_or_fetch - existe no banco
  ```python
  async def test_get_or_fetch_exists():
      # Criar índice no banco primeiro
      # Chamar get_or_fetch
      # Verificar que não fez requisição ao BCB (usar mock)
      # Verificar que retornou do banco
  ```

- [ ] **Teste 1.3.3:** Testar get_or_fetch - não existe, busca BCB
  ```python
  async def test_get_or_fetch_not_exists():
      # Garantir que não existe no banco
      # Mockar BCB para retornar dados
      # Chamar get_or_fetch
      # Verificar que fez requisição ao BCB
      # Verificar que salvou no banco
      # Verificar que retornou dados corretos
  ```

- [ ] **Teste 1.3.4:** Testar tratamento de erro de rede
  ```python
  async def test_fetch_from_bcb_network_error():
      # Mockar httpx.get para lançar exception
      # Chamar fetch_from_bcb
      # Verificar que exception é tratada adequadamente
  ```

#### Checklist de Validação:
- [ ] Integração com BCB funcionando (testes com mock)
- [ ] Cache funcionando (não busca BCB se existe no banco)
- [ ] Erros de rede tratados
- [ ] Todos os tipos de índice suportados
- [ ] Nenhum teste existente quebrado

---

### 📋 Etapa 1.4: Criar Router/Endpoints

**Objetivo:** Expor API REST para frontend consumir

#### Tarefas:
- [ ] 1.4.1 Criar router em `backend/app/routers/economic_indexes.py`
  - `GET /api/economic-indexes` - Listar índices (com filtros)
    - Query params: `index_type`, `start_date`, `end_date`, `limit`, `offset`
  - `GET /api/economic-indexes/{index_type}/latest` - Último índice de um tipo
  - `GET /api/economic-indexes/{index_type}/{date}` - Índice específico
  - `POST /api/economic-indexes/sync/{index_type}` - Sincronizar do BCB (admin)

- [ ] 1.4.2 Implementar autenticação
  - Endpoints GET: Autenticação JWT opcional (pode ser público)
  - Endpoint POST sync: Requer autenticação admin

- [ ] 1.4.3 Registrar router em `backend/app/main.py`
  ```python
  from .routers.economic_indexes import router as economic_indexes_router
  app.include_router(economic_indexes_router, prefix="/api/economic-indexes", tags=["Economic Indexes"])
  ```

#### Testes:
- [ ] **Teste 1.4.1:** Testar listagem de índices
  ```python
  async def test_list_indexes(client):
      # Criar alguns índices
      response = await client.get("/api/economic-indexes")
      assert response.status_code == 200
      data = response.json()
      assert "indexes" in data
      assert len(data["indexes"]) > 0
  ```

- [ ] **Teste 1.4.2:** Testar filtro por tipo
  ```python
  async def test_list_indexes_filter_by_type(client):
      # Criar índices de tipos diferentes
      response = await client.get("/api/economic-indexes?index_type=SELIC")
      data = response.json()
      assert all(idx["index_type"] == "SELIC" for idx in data["indexes"])
  ```

- [ ] **Teste 1.4.3:** Testar busca do latest
  ```python
  async def test_get_latest(client):
      # Criar múltiplos índices SELIC com datas diferentes
      response = await client.get("/api/economic-indexes/SELIC/latest")
      assert response.status_code == 200
      data = response.json()
      assert data["index_type"] == "SELIC"
      # Verificar que é a data mais recente
  ```

- [ ] **Teste 1.4.4:** Testar sync (requer admin)
  ```python
  async def test_sync_index_admin(client, admin_token):
      response = await client.post(
          "/api/economic-indexes/sync/SELIC",
          headers={"Authorization": f"Bearer {admin_token}"}
      )
      assert response.status_code == 200
  ```

- [ ] **Teste 1.4.5:** Testar sync sem autenticação admin (deve falhar)
  ```python
  async def test_sync_index_unauthorized(client):
      response = await client.post("/api/economic-indexes/sync/SELIC")
      assert response.status_code == 401 or 403
  ```

#### Checklist de Validação:
- [ ] Todos os endpoints implementados
- [ ] Documentação Swagger/OpenAPI gerada corretamente
- [ ] Autenticação funcionando
- [ ] Filtros funcionando
- [ ] Testes de integração passando
- [ ] Nenhum endpoint existente quebrado
- [ ] Frontend pode consumir a API (testar manualmente)

---

### 📋 Etapa 1.5: Testes End-to-End

**Objetivo:** Validar fluxo completo da funcionalidade

#### Tarefas:
- [ ] 1.5.1 Testar fluxo completo manualmente
  1. Criar índices via API
  2. Listar índices
  3. Buscar latest
  4. Sincronizar do BCB (se possível em ambiente de teste)

- [ ] 1.5.2 Testar integração com frontend
  1. Acessar calculadora
  2. Selecionar tipo de reajuste (ex: SELIC)
  3. Verificar se valores são preenchidos automaticamente
  4. Verificar console do navegador (sem erros)

- [ ] 1.5.3 Executar suite completa de testes
  ```bash
  cd backend
  pytest tests/ -v --cov=app --cov-report=html
  ```
  - Cobertura deve ser > 80% para código novo
  - Todos os testes existentes devem passar

#### Checklist de Validação:
- [ ] Fluxo completo funcionando
- [ ] Frontend integrado corretamente
- [ ] Cobertura de testes > 80%
- [ ] Nenhum teste quebrado
- [ ] Performance aceitável (< 500ms para listagem)

---

### 📊 Resumo Funcionalidade 1

**Status:** ⬜ Não iniciado

**Arquivos Criados:**
- `backend/app/models.py` (adicionar EconomicIndex)
- `backend/app/schemas.py` (adicionar schemas)
- `backend/app/repositories/economic_indexes.py`
- `backend/app/services/economic_index_service.py`
- `backend/app/routers/economic_indexes.py`
- `backend/alembic/versions/YYYYMMDD_HHMMSS_add_economic_indexes_table.py`

**Arquivos Modificados:**
- `backend/app/main.py` (registrar router)
- `backend/app/repositories/__init__.py` (exportar repository)

**Testes Criados:**
- `backend/tests/test_economic_indexes_model.py`
- `backend/tests/test_economic_indexes_repository.py`
- `backend/tests/test_economic_indexes_service.py`
- `backend/tests/test_economic_indexes_api.py`

---

## 🎯 Funcionalidade 2: Sistema de Alertas e Notificações

**Prioridade:** 🔴 Alta  
**Complexidade:** Média  
**Dependências:** Nenhuma  
**Base para:** Melhorar experiência do usuário

### Objetivo
Criar sistema de notificações (email e in-app) para eventos importantes do sistema.

---

### 📋 Etapa 2.1: Criar Modelo de Dados de Notificações

**Objetivo:** Estrutura para armazenar notificações

#### Tarefas:
- [ ] 2.1.1 Criar modelo `Notification` em `backend/app/models.py`
  - Campos: `id`, `user_id`, `type`, `title`, `message`, `read`, `created_at`, `metadata` (JSONB)
  - Enum para tipos: CONTRACT_EXPIRING, INDEX_CHANGED, REMEASUREMENT_DONE, SYSTEM_ALERT
  - Índices: `idx_notifications_user_read`, `idx_notifications_created_at`

- [ ] 2.1.2 Criar schema Pydantic
  - `NotificationCreate`, `NotificationOut`, `NotificationListOut`, `NotificationUpdate`

- [ ] 2.1.3 Criar migration
  - Arquivo: `backend/alembic/versions/YYYYMMDD_HHMMSS_add_notifications_table.py`

#### Testes:
- [ ] **Teste 2.1.1:** Criar notificação válida
- [ ] **Teste 2.1.2:** Verificar constraints
- [ ] **Teste 2.1.3:** Verificar índices funcionando

#### Checklist de Validação:
- [ ] Migration criada e testada
- [ ] Modelo importa sem erros
- [ ] Nenhum teste existente quebrado

---

### 📋 Etapa 2.2: Criar Service de Notificações

**Objetivo:** Lógica para criar e enviar notificações

#### Tarefas:
- [ ] 2.2.1 Criar `NotificationService` em `backend/app/services/notification_service.py`
  - Métodos:
    - `create_notification(user_id, type, title, message, metadata=None)`
    - `send_email_notification(user, notification)` (usar EmailService existente)
    - `mark_as_read(notification_id)`
    - `get_unread_count(user_id)`

- [ ] 2.2.2 Integrar com EmailService existente
  - Reutilizar `backend/app/services/email_service.py`
  - Criar templates de email para cada tipo de notificação

#### Testes:
- [ ] **Teste 2.2.1:** Criar notificação
- [ ] **Teste 2.2.2:** Enviar email (mockado)
- [ ] **Teste 2.2.3:** Marcar como lida
- [ ] **Teste 2.2.4:** Contar não lidas

#### Checklist de Validação:
- [ ] Service implementado
- [ ] Integração com email funcionando
- [ ] Testes passando
- [ ] Nenhum teste existente quebrado

---

### 📋 Etapa 2.3: Criar Router/Endpoints

**Objetivo:** API para gerenciar notificações

#### Tarefas:
- [ ] 2.3.1 Criar router em `backend/app/routers/notifications.py`
  - `GET /api/notifications` - Listar notificações do usuário
  - `GET /api/notifications/unread-count` - Contar não lidas
  - `PUT /api/notifications/{id}/read` - Marcar como lida
  - `PUT /api/notifications/read-all` - Marcar todas como lidas

- [ ] 2.3.2 Registrar router em `main.py`

#### Testes:
- [ ] **Teste 2.3.1:** Listar notificações
- [ ] **Teste 2.3.2:** Contar não lidas
- [ ] **Teste 2.3.3:** Marcar como lida
- [ ] **Teste 2.3.4:** Autenticação (deve retornar apenas do usuário logado)

#### Checklist de Validação:
- [ ] Endpoints funcionando
- [ ] Autenticação funcionando
- [ ] Testes passando
- [ ] Nenhum endpoint existente quebrado

---

### 📋 Etapa 2.4: Implementar Triggers de Notificações

**Objetivo:** Criar notificações automaticamente em eventos

#### Tarefas:
- [ ] 2.4.1 Adicionar notificação quando contrato está próximo do vencimento
  - Em `contracts_service.py`, verificar ao listar contratos
  - Se vencimento < 30 dias, criar notificação

- [ ] 2.4.2 Adicionar notificação quando remensuração é feita
  - Quando versão nova é criada após remensuração automática

- [ ] 2.4.3 Criar job agendado para verificar contratos vencendo
  - Usar Cloud Scheduler ou similar
  - Rodar diariamente

#### Testes:
- [ ] **Teste 2.4.1:** Verificar notificação de vencimento
- [ ] **Teste 2.4.2:** Verificar notificação de remensuração
- [ ] **Teste 2.4.3:** Testar job agendado (manualmente primeiro)

#### Checklist de Validação:
- [ ] Notificações sendo criadas automaticamente
- [ ] Emails sendo enviados
- [ ] Job agendado funcionando
- [ ] Nenhuma funcionalidade existente quebrada

---

### 📋 Etapa 2.5: Frontend - Exibir Notificações

**Objetivo:** Interface para usuário ver notificações

#### Tarefas:
- [ ] 2.5.1 Adicionar badge de notificações no header
  - Mostrar contador de não lidas
  - Link para página de notificações

- [ ] 2.5.2 Criar página `notifications.html`
  - Listar notificações
  - Marcar como lida ao clicar
  - Botão "Marcar todas como lidas"

- [ ] 2.5.3 Adicionar polling ou WebSocket
  - Atualizar contador periodicamente (ex: a cada 30 segundos)

#### Testes:
- [ ] **Teste Manual 2.5.1:** Verificar badge aparece
- [ ] **Teste Manual 2.5.2:** Verificar página de notificações
- [ ] **Teste Manual 2.5.3:** Verificar atualização automática

#### Checklist de Validação:
- [ ] UI funcionando
- [ ] Integração com API funcionando
- [ ] Nenhuma página existente quebrada

---

### 📊 Resumo Funcionalidade 2

**Status:** ⬜ Não iniciado

**Dependências:**
- EmailService (já existe)

**Arquivos Criados:**
- `backend/app/services/notification_service.py`
- `backend/app/routers/notifications.py`
- `backend/tests/test_notifications_*.py`
- `notifications.html` (frontend)

---

## 🎯 Funcionalidade 3: Upload e Gestão de Documentos

**Prioridade:** 🔴 Alta  
**Complexidade:** Alta  
**Dependências:** Firebase Storage ou Google Cloud Storage  
**Base para:** Auditoria e compliance

### Objetivo
Permitir upload de PDFs de contratos e documentos relacionados, com armazenamento seguro e versionamento.

---

### 📋 Etapa 3.1: Configurar Storage

**Objetivo:** Configurar Firebase Storage ou Cloud Storage

#### Tarefas:
- [ ] 3.1.1 Decidir provider (Firebase Storage recomendado)
- [ ] 3.1.2 Criar bucket/configurar storage
- [ ] 3.1.3 Configurar regras de acesso
- [ ] 3.1.4 Obter credenciais e adicionar ao `.env`

#### Testes:
- [ ] **Teste 3.1.1:** Verificar acesso ao storage
- [ ] **Teste 3.1.2:** Verificar regras de acesso

#### Checklist de Validação:
- [ ] Storage configurado
- [ ] Credenciais configuradas
- [ ] Regras de acesso testadas

---

### 📋 Etapa 3.2: Criar Modelo de Dados

**Objetivo:** Estrutura para armazenar metadados de documentos

#### Tarefas:
- [ ] 3.2.1 Criar modelo `Document` em `backend/app/models.py`
  - Campos: `id`, `contract_id`, `user_id`, `filename`, `file_path`, `file_size`, `mime_type`, `version`, `created_at`
  - Relação com Contract

- [ ] 3.2.2 Criar migration

#### Testes:
- [ ] **Teste 3.2.1:** Criar documento válido
- [ ] **Teste 3.2.2:** Verificar constraints

#### Checklist de Validação:
- [ ] Migration criada
- [ ] Modelo funcionando
- [ ] Nenhum teste existente quebrado

---

### 📋 Etapa 3.3: Criar Service de Upload

**Objetivo:** Lógica para upload e gerenciamento de arquivos

#### Tarefas:
- [ ] 3.3.1 Criar `DocumentService` em `backend/app/services/document_service.py`
  - Métodos:
    - `upload_document(contract_id, file, user_id) -> Document`
    - `get_documents(contract_id) -> List[Document]`
    - `delete_document(document_id, user_id)`
    - `get_document_url(document_id) -> str` (signed URL)

- [ ] 3.3.2 Implementar upload para storage
  - Validar tipo de arquivo (apenas PDF)
  - Validar tamanho (máx 10MB)
  - Gerar nome único
  - Upload para storage
  - Salvar metadados no banco

- [ ] 3.3.3 Implementar download seguro
  - Gerar signed URL com expiração
  - Verificar permissões do usuário

#### Testes:
- [ ] **Teste 3.3.1:** Upload de arquivo válido
- [ ] **Teste 3.3.2:** Upload de arquivo inválido (tipo/tamanho) - deve falhar
- [ ] **Teste 3.3.3:** Listar documentos
- [ ] **Teste 3.3.4:** Gerar URL assinada
- [ ] **Teste 3.3.5:** Verificar permissões (usuário só vê seus documentos)

#### Checklist de Validação:
- [ ] Service implementado
- [ ] Upload funcionando
- [ ] Validações funcionando
- [ ] Download seguro funcionando
- [ ] Testes passando
- [ ] Nenhum teste existente quebrado

---

### 📋 Etapa 3.4: Criar Router/Endpoints

**Objetivo:** API para upload/download de documentos

#### Tarefas:
- [ ] 3.4.1 Criar router em `backend/app/routers/documents.py`
  - `POST /api/contracts/{contract_id}/documents` - Upload
  - `GET /api/contracts/{contract_id}/documents` - Listar
  - `GET /api/documents/{document_id}/download` - Download (retorna signed URL)
  - `DELETE /api/documents/{document_id}` - Deletar

- [ ] 3.4.2 Implementar multipart/form-data para upload
  - Usar `UploadFile` do FastAPI

#### Testes:
- [ ] **Teste 3.4.1:** Upload via API
- [ ] **Teste 3.4.2:** Listar documentos
- [ ] **Teste 3.4.3:** Download (verificar URL assinada)
- [ ] **Teste 3.4.4:** Deletar documento
- [ ] **Teste 3.4.5:** Autenticação (só próprio usuário)

#### Checklist de Validação:
- [ ] Endpoints funcionando
- [ ] Upload via API funcionando
- [ ] Testes passando
- [ ] Nenhum endpoint existente quebrado

---

### 📋 Etapa 3.5: Frontend - Interface de Upload

**Objetivo:** Interface para usuário fazer upload e ver documentos

#### Tarefas:
- [ ] 3.5.1 Adicionar seção de documentos na página do contrato
- [ ] 3.5.2 Implementar upload com drag-and-drop
- [ ] 3.5.3 Implementar visualização de PDF (usar PDF.js ou iframe)
- [ ] 3.5.4 Implementar download

#### Testes:
- [ ] **Teste Manual 3.5.1:** Upload de arquivo
- [ ] **Teste Manual 3.5.2:** Visualizar PDF
- [ ] **Teste Manual 3.5.3:** Download
- [ ] **Teste Manual 3.5.4:** Deletar

#### Checklist de Validação:
- [ ] UI funcionando
- [ ] Upload funcionando
- [ ] Visualização funcionando
- [ ] Nenhuma página existente quebrada

---

### 📊 Resumo Funcionalidade 3

**Status:** ⬜ Não iniciado

**Dependências:**
- Firebase Storage ou Cloud Storage configurado

---

## 🎯 Funcionalidade 4: Dashboard Analítico Melhorado

**Prioridade:** 🔴 Alta  
**Complexidade:** Média  
**Dependências:** Nenhuma  
**Base para:** Valor para gestores

### Objetivo
Melhorar dashboard com métricas visuais, gráficos e análises dos contratos.

---

### 📋 Etapa 4.1: Criar Endpoints de Métricas

**Objetivo:** API para fornecer dados agregados

#### Tarefas:
- [ ] 4.1.1 Adicionar endpoints em `backend/app/routers/user_dashboard.py` ou criar novo router
  - `GET /api/dashboard/metrics` - Métricas gerais
    - Total de contratos
    - Valor total de passivos
    - Valor total de ativos
    - Despesas mensais totais
  - `GET /api/dashboard/evolution` - Evolução ao longo do tempo
    - Passivo por mês (últimos 12 meses)
  - `GET /api/dashboard/distribution` - Distribuição por categoria
  - `GET /api/dashboard/upcoming-expirations` - Próximos vencimentos

- [ ] 4.1.2 Criar queries agregadas eficientes
  - Usar SQLAlchemy para agregações
  - Otimizar com índices se necessário

#### Testes:
- [ ] **Teste 4.1.1:** Buscar métricas
- [ ] **Teste 4.1.2:** Verificar cálculos corretos
- [ ] **Teste 4.1.3:** Verificar performance (< 500ms)

#### Checklist de Validação:
- [ ] Endpoints criados
- [ ] Queries otimizadas
- [ ] Testes passando
- [ ] Nenhum endpoint existente quebrado

---

### 📋 Etapa 4.2: Frontend - Implementar Gráficos

**Objetivo:** Visualizar métricas com gráficos

#### Tarefas:
- [ ] 4.2.1 Escolher biblioteca de gráficos (Chart.js recomendado)
- [ ] 4.2.2 Melhorar `dashboard.html` com seção de métricas
  - Cards com métricas principais
  - Gráfico de linha: Evolução do passivo
  - Gráfico de pizza: Distribuição por categoria
  - Gráfico de barras: Despesas mensais
  - Tabela: Próximos vencimentos

- [ ] 4.2.3 Implementar filtros (período, categoria)

#### Testes:
- [ ] **Teste Manual 4.2.1:** Verificar gráficos renderizam
- [ ] **Teste Manual 4.2.2:** Verificar dados corretos
- [ ] **Teste Manual 4.2.3:** Verificar filtros funcionando

#### Checklist de Validação:
- [ ] Gráficos funcionando
- [ ] Dados corretos
- [ ] Filtros funcionando
- [ ] Performance aceitável
- [ ] Nenhuma página existente quebrada

---

### 📊 Resumo Funcionalidade 4

**Status:** ⬜ Não iniciado

**Dependências:**
- Contratos e versões (já existem)

---

# FASE 2 - MÉDIA PRIORIDADE

---

## 🎯 Funcionalidade 5: Notas Explicativas Automatizadas

**Prioridade:** 🟡 Média  
**Complexidade:** Baixa  
**Dependências:** Nenhuma  
**Base para:** Compliance e auditoria

### Objetivo
Gerar notas explicativas automaticamente conforme CPC 06/IFRS 16, baseadas nos dados dos contratos.

---

### 📋 Etapa 5.1: Criar Template de Notas

**Objetivo:** Estrutura base para notas explicativas

#### Tarefas:
- [ ] 5.1.1 Criar arquivo `backend/app/templates/notes_explicativas.md`
  - Template Markdown conforme estrutura CPC 06
  - Seções: Reconhecimento Inicial, Critérios de Mensuração, Informações por Categoria, Reconciliação

- [ ] 5.1.2 Criar função de geração em `backend/app/services/notes_service.py`
  - Método: `generate_explanatory_notes(contract_ids: List[str], competencia: date) -> str`
  - Preencher template com dados reais dos contratos

- [ ] 5.1.3 Implementar formatação
  - Valores monetários formatados
  - Datas formatadas
  - Tabelas formatadas

#### Testes:
- [ ] **Teste 5.1.1:** Gerar notas para um contrato
  ```python
  async def test_generate_notes_single_contract():
      service = NotesService(db)
      notes = await service.generate_explanatory_notes([contract_id], date(2024, 12, 31))
      assert "IFRS 16" in notes
      assert "Reconhecimento Inicial" in notes
      assert str(contract.total_vp) in notes
  ```

- [ ] **Teste 5.1.2:** Gerar notas para múltiplos contratos
- [ ] **Teste 5.1.3:** Verificar formatação de valores

#### Checklist de Validação:
- [ ] Template criado
- [ ] Geração funcionando
- [ ] Formatação correta
- [ ] Nenhum teste existente quebrado

---

### 📋 Etapa 5.2: Criar Endpoint e Exportação

**Objetivo:** API para gerar e exportar notas

#### Tarefas:
- [ ] 5.2.1 Adicionar endpoint em router existente ou criar novo
  - `POST /api/contracts/generate-notes` - Gerar notas
    - Body: `{contract_ids: List[str], competencia: str}`
    - Retorna: Markdown das notas

- [ ] 5.2.2 Implementar exportação para Word
  - Usar biblioteca `python-docx`
  - Converter Markdown para Word

- [ ] 5.2.3 Implementar exportação para PDF
  - Usar biblioteca `reportlab` ou similar
  - Converter Markdown para PDF

#### Testes:
- [ ] **Teste 5.2.1:** Gerar notas via API
- [ ] **Teste 5.2.2:** Exportar Word
- [ ] **Teste 5.2.3:** Exportar PDF

#### Checklist de Validação:
- [ ] Endpoint funcionando
- [ ] Exportações funcionando
- [ ] Testes passando
- [ ] Nenhum endpoint existente quebrado

---

### 📋 Etapa 5.3: Frontend - Botão de Exportação

**Objetivo:** Interface para usuário gerar notas

#### Tarefas:
- [ ] 5.3.1 Adicionar botão "Gerar Notas Explicativas" em `relatorios.html`
- [ ] 5.3.2 Implementar chamada à API
- [ ] 5.3.3 Implementar download de arquivo gerado

#### Testes:
- [ ] **Teste Manual 5.3.1:** Gerar notas
- [ ] **Teste Manual 5.3.2:** Download Word
- [ ] **Teste Manual 5.3.3:** Download PDF

#### Checklist de Validação:
- [ ] UI funcionando
- [ ] Download funcionando
- [ ] Nenhuma página existente quebrada

---

### 📊 Resumo Funcionalidade 5

**Status:** ⬜ Não iniciado

**Arquivos Criados:**
- `backend/app/templates/notes_explicativas.md`
- `backend/app/services/notes_service.py`
- `backend/tests/test_notes_service.py`
- `backend/tests/test_notes_api.py`

---

## 🎯 Funcionalidade 6: Simulação de Cenários

**Prioridade:** 🟡 Média  
**Complexidade:** Média  
**Dependências:** Nenhuma  
**Base para:** Análise de impacto

### Objetivo
Permitir criar cenários "what-if" para avaliar impacto de mudanças em contratos.

---

### 📋 Etapa 6.1: Criar Modelo de Cenário

**Objetivo:** Estrutura para armazenar cenários

#### Tarefas:
- [ ] 6.1.1 Criar modelo `Scenario` em `backend/app/models.py`
  - Campos: `id`, `contract_id`, `user_id`, `name`, `description`, `base_version_id`
  - Campos de modificação: `modified_fields` (JSONB) - armazena quais campos foram alterados
  - Relação com Contract e ContractVersion

- [ ] 6.1.2 Criar schema Pydantic
  - `ScenarioCreate`, `ScenarioOut`, `ScenarioComparison`

- [ ] 6.1.3 Criar migration

#### Testes:
- [ ] **Teste 6.1.1:** Criar cenário válido
- [ ] **Teste 6.1.2:** Verificar constraints

#### Checklist de Validação:
- [ ] Migration criada
- [ ] Modelo funcionando
- [ ] Nenhum teste existente quebrado

---

### 📋 Etapa 6.2: Implementar Cálculo de Cenário

**Objetivo:** Recalcular contrato com valores modificados

#### Tarefas:
- [ ] 6.2.1 Criar `ScenarioService` em `backend/app/services/scenario_service.py`
  - Método: `create_scenario(contract_id, base_version_id, modifications) -> Scenario`
  - Método: `calculate_scenario(scenario_id) -> dict` (retorna resultados calculados)
  - Método: `compare_scenarios(original_version_id, scenario_id) -> dict`

- [ ] 6.2.2 Reutilizar lógica de cálculo existente
  - Adaptar `calcular()` do frontend ou criar versão backend
  - Aplicar modificações antes de calcular

- [ ] 6.2.3 Salvar resultados calculados
  - Armazenar em campo JSONB no Scenario

#### Testes:
- [ ] **Teste 6.2.1:** Criar cenário e calcular
  ```python
  async def test_calculate_scenario():
      # Criar contrato e versão base
      # Criar cenário modificando parcela_inicial
      # Calcular cenário
      # Verificar que VP mudou
  ```

- [ ] **Teste 6.2.2:** Comparar cenários
  ```python
  async def test_compare_scenarios():
      # Criar cenário
      # Comparar com versão original
      # Verificar diferenças calculadas corretamente
  ```

#### Checklist de Validação:
- [ ] Service implementado
- [ ] Cálculo funcionando
- [ ] Comparação funcionando
- [ ] Testes passando
- [ ] Nenhum teste existente quebrado

---

### 📋 Etapa 6.3: Criar Router/Endpoints

**Objetivo:** API para gerenciar cenários

#### Tarefas:
- [ ] 6.3.1 Criar router em `backend/app/routers/scenarios.py`
  - `POST /api/contracts/{contract_id}/scenarios` - Criar cenário
  - `GET /api/scenarios/{scenario_id}` - Obter cenário
  - `POST /api/scenarios/{scenario_id}/calculate` - Calcular cenário
  - `GET /api/scenarios/{scenario_id}/compare` - Comparar com original
  - `GET /api/contracts/{contract_id}/scenarios` - Listar cenários do contrato

- [ ] 6.3.2 Registrar router em `main.py`

#### Testes:
- [ ] **Teste 6.3.1:** Criar cenário via API
- [ ] **Teste 6.3.2:** Calcular cenário via API
- [ ] **Teste 6.3.3:** Comparar cenários via API
- [ ] **Teste 6.3.4:** Autenticação (só próprio usuário)

#### Checklist de Validação:
- [ ] Endpoints funcionando
- [ ] Testes passando
- [ ] Nenhum endpoint existente quebrado

---

### 📋 Etapa 6.4: Frontend - Interface de Cenários

**Objetivo:** UI para criar e comparar cenários

#### Tarefas:
- [ ] 6.4.1 Adicionar seção "Simular Cenário" na página do contrato
- [ ] 6.4.2 Formulário para modificar variáveis
  - Parcela inicial, taxa, prazo, etc.
- [ ] 6.4.3 Visualização lado a lado (original vs. cenário)
- [ ] 6.4.4 Destaque de diferenças

#### Testes:
- [ ] **Teste Manual 6.4.1:** Criar cenário
- [ ] **Teste Manual 6.4.2:** Ver comparação
- [ ] **Teste Manual 6.4.3:** Salvar cenário

#### Checklist de Validação:
- [ ] UI funcionando
- [ ] Comparação visual funcionando
- [ ] Nenhuma página existente quebrada

---

### 📊 Resumo Funcionalidade 6

**Status:** ⬜ Não iniciado

**Dependências:**
- Lógica de cálculo (já existe no frontend, precisa adaptar para backend)

---

## 🎯 Funcionalidade 7: Remensuração Automática Mensal

**Prioridade:** 🟡 Média  
**Complexidade:** Alta  
**Dependências:** ✅ Funcionalidade 1 (API de Índices)  
**Base para:** Conformidade IFRS 16

### Objetivo
Recalcular automaticamente contratos quando índices econômicos mudam, criando novas versões.

---

### 📋 Etapa 7.1: Criar Job Agendado

**Objetivo:** Processo que roda periodicamente

#### Tarefas:
- [ ] 7.1.1 Criar endpoint interno para job
  - `POST /api/internal/remeasure-contracts` (requer admin token ou API key)
  - Ou criar Cloud Function separada

- [ ] 7.1.2 Configurar Cloud Scheduler (Google Cloud)
  - Agendar para rodar no dia 1º de cada mês
  - Chamar endpoint ou Cloud Function

- [ ] 7.1.3 Implementar lógica básica de job
  - Buscar todos contratos ativos
  - Para cada contrato, verificar se usa índice econômico
  - Se usa, verificar se índice mudou desde última versão

#### Testes:
- [ ] **Teste 7.1.1:** Executar job manualmente via endpoint
- [ ] **Teste 7.1.2:** Verificar que job identifica contratos corretos
- [ ] **Teste 7.1.3:** Verificar autenticação (só admin/API key)

#### Checklist de Validação:
- [ ] Endpoint criado
- [ ] Job pode ser executado manualmente
- [ ] Agendamento configurado (ou instruções documentadas)
- [ ] Nenhum endpoint existente quebrado

---

### 📋 Etapa 7.2: Implementar Detecção de Mudanças

**Objetivo:** Identificar quando recalcular

#### Tarefas:
- [ ] 7.2.1 Criar método em `ContractService`
  - `find_contracts_using_index(index_type: str) -> List[Contract]`
  - Buscar contratos que têm versões usando determinado índice

- [ ] 7.2.2 Criar método para comparar índices
  - `has_index_changed(contract_id, index_type, reference_date) -> bool`
  - Buscar última versão do contrato
  - Buscar índice usado nessa versão
  - Buscar índice atual do BCB
  - Comparar valores

- [ ] 7.2.3 Integrar com EconomicIndexService
  - Usar `get_or_fetch()` para obter índice atual
  - Comparar com índice da versão

#### Testes:
- [ ] **Teste 7.2.1:** Encontrar contratos usando índice
  ```python
  async def test_find_contracts_using_index():
      # Criar contratos, um usando IGPM, outro usando manual
      contracts = await service.find_contracts_using_index("IGPM")
      assert len(contracts) == 1
      assert contracts[0].id == contract_igpm.id
  ```

- [ ] **Teste 7.2.2:** Detectar mudança de índice
  ```python
  async def test_has_index_changed():
      # Criar contrato com versão usando IGPM de jan/2024
      # Mockar BCB para retornar IGPM diferente para fev/2024
      # Verificar que has_index_changed retorna True
  ```

- [ ] **Teste 7.2.3:** Não detectar mudança quando igual
  ```python
  async def test_has_index_not_changed():
      # Índice não mudou
      # Verificar que retorna False
  ```

#### Checklist de Validação:
- [ ] Detecção funcionando
- [ ] Comparação correta
- [ ] Testes passando
- [ ] Nenhum teste existente quebrado

---

### 📋 Etapa 7.3: Implementar Recalculo Automático

**Objetivo:** Recalcular e criar nova versão

#### Tarefas:
- [ ] 7.3.1 Criar método `remeasure_contract(contract_id) -> ContractVersion`
  - Buscar última versão do contrato
  - Obter índice atual do BCB
  - Recalcular contrato com novo índice
  - Criar nova versão arquivada automaticamente
  - Retornar nova versão

- [ ] 7.3.2 Integrar com lógica de cálculo existente
  - Adaptar cálculo do frontend ou criar versão backend
  - Aplicar novo valor do índice

- [ ] 7.3.3 Adicionar campo `auto_remeasured` na versão
  - Indicar que versão foi criada automaticamente
  - Adicionar nota automática explicando remensuração

#### Testes:
- [ ] **Teste 7.3.1:** Remensurar contrato
  ```python
  async def test_remeasure_contract():
      # Criar contrato com versão usando IGPM antigo
      # Mockar BCB para retornar IGPM novo
      # Executar remensuração
      # Verificar que nova versão foi criada
      # Verificar que VP mudou (se índice mudou significativamente)
  ```

- [ ] **Teste 7.3.2:** Verificar que versão automática foi marcada
- [ ] **Teste 7.3.3:** Verificar nota automática foi adicionada

#### Checklist de Validação:
- [ ] Remensuração funcionando
- [ ] Nova versão criada corretamente
- [ ] Valores recalculados corretamente
- [ ] Testes passando
- [ ] Nenhum teste existente quebrado

---

### 📋 Etapa 7.4: Integrar com Notificações

**Objetivo:** Notificar usuário sobre remensuração

#### Tarefas:
- [ ] 7.4.1 Após criar versão automática, criar notificação
  - Tipo: REMEASUREMENT_DONE
  - Título: "Contrato {nome} foi remensurado"
  - Mensagem: "Nova versão criada com índice atualizado"

- [ ] 7.4.2 Enviar email ao usuário
  - Usar EmailService
  - Template de email informando remensuração

- [ ] 7.4.3 Adicionar link para ver nova versão no email

#### Testes:
- [ ] **Teste 7.4.1:** Verificar notificação criada após remensuração
- [ ] **Teste 7.4.2:** Verificar email enviado (mockado)

#### Checklist de Validação:
- [ ] Notificações sendo criadas
- [ ] Emails sendo enviados
- [ ] Testes passando
- [ ] Nenhum teste existente quebrado

---

### 📋 Etapa 7.5: Testes End-to-End do Job

**Objetivo:** Validar fluxo completo

#### Tarefas:
- [ ] 7.5.1 Executar job completo em ambiente de teste
  1. Criar contratos com índices diferentes
  2. Criar versões antigas
  3. Mockar BCB para retornar índices novos
  4. Executar job
  5. Verificar que novas versões foram criadas
  6. Verificar que notificações foram criadas

- [ ] 7.5.2 Testar casos edge
  - Contrato sem índice (não deve remensurar)
  - Índice não mudou (não deve remensurar)
  - Múltiplos contratos (deve processar todos)

#### Checklist de Validação:
- [ ] Job funcionando end-to-end
- [ ] Casos edge tratados
- [ ] Performance aceitável

---

### 📊 Resumo Funcionalidade 7

**Status:** ⬜ Não iniciado

**Dependências:**
- ✅ Funcionalidade 1 (API de Índices)
- Funcionalidade 2 (Notificações) - opcional mas recomendado

**Arquivos Criados:**
- `backend/app/services/remeasurement_service.py`
- `backend/app/routers/internal.py` (ou adicionar em router existente)
- `backend/tests/test_remeasurement_*.py`
- Cloud Function ou Cloud Scheduler config

---

## 🎯 Funcionalidade 8: Auditoria e Rastreabilidade

**Prioridade:** 🟡 Média  
**Complexidade:** Média  
**Dependências:** Nenhuma  
**Base para:** Compliance e segurança

### Objetivo
Registrar todas as ações importantes do sistema (quem, o quê, quando).

---

### 📋 Etapa 8.1: Criar Modelo de Audit Log

**Objetivo:** Estrutura para armazenar logs

#### Tarefas:
- [ ] 8.1.1 Criar modelo `AuditLog` em `backend/app/models.py`
  - Campos: `id`, `user_id`, `action`, `entity_type`, `entity_id`, `old_value` (JSONB), `new_value` (JSONB), `ip_address`, `user_agent`, `created_at`
  - Enum para ações: CREATE, UPDATE, DELETE, APPROVE, REJECT, etc.
  - Enum para entity_type: CONTRACT, CONTRACT_VERSION, LICENSE, USER, etc.
  - Índices: `idx_audit_log_user`, `idx_audit_log_entity`, `idx_audit_log_created_at`

- [ ] 8.1.2 Criar schema Pydantic
  - `AuditLogCreate`, `AuditLogOut`, `AuditLogListOut`

- [ ] 8.1.3 Criar migration

#### Testes:
- [ ] **Teste 8.1.1:** Criar log válido
- [ ] **Teste 8.1.2:** Verificar índices funcionando

#### Checklist de Validação:
- [ ] Migration criada
- [ ] Modelo funcionando
- [ ] Nenhum teste existente quebrado

---

### 📋 Etapa 8.2: Criar Repository e Service

**Objetivo:** Camadas de acesso e lógica

#### Tarefas:
- [ ] 8.2.1 Criar `AuditLogRepository` em `backend/app/repositories/audit_log.py`
  - Métodos: `create()`, `list_by_user()`, `list_by_entity()`, `list_by_date_range()`

- [ ] 8.2.2 Criar `AuditLogService` em `backend/app/services/audit_log_service.py`
  - Método: `log_action(user_id, action, entity_type, entity_id, old_value, new_value, request)`

#### Testes:
- [ ] **Teste 8.2.1:** Criar log via service
- [ ] **Teste 8.2.2:** Listar logs por usuário
- [ ] **Teste 8.2.3:** Listar logs por entidade

#### Checklist de Validação:
- [ ] Repository e Service implementados
- [ ] Testes passando
- [ ] Nenhum teste existente quebrado

---

### 📋 Etapa 8.3: Implementar Middleware de Auditoria

**Objetivo:** Capturar ações automaticamente

#### Tarefas:
- [ ] 8.3.1 Criar middleware em `backend/app/middleware/audit_middleware.py`
  - Interceptar requisições
  - Capturar método HTTP, endpoint, body
  - Capturar IP, user_agent
  - Identificar ação (CREATE, UPDATE, DELETE baseado em método HTTP)

- [ ] 8.3.2 Registrar middleware em `main.py`
  - Aplicar apenas a rotas que precisam auditoria

- [ ] 8.3.3 Integrar com routers existentes
  - Adicionar logging em operações críticas manualmente se necessário

#### Testes:
- [ ] **Teste 8.3.1:** Verificar que middleware captura requisição
- [ ] **Teste 8.3.2:** Verificar que log é criado

#### Checklist de Validação:
- [ ] Middleware funcionando
- [ ] Logs sendo criados
- [ ] Testes passando
- [ ] Nenhum endpoint existente quebrado

---

### 📋 Etapa 8.4: Criar Router/Endpoints (Admin)

**Objetivo:** API para consultar logs (apenas admin)

#### Tarefas:
- [ ] 8.4.1 Adicionar endpoints em `backend/app/routers/admin.py`
  - `GET /api/admin/audit-logs` - Listar logs (com filtros)
    - Query params: `user_id`, `entity_type`, `entity_id`, `start_date`, `end_date`, `action`
  - `GET /api/admin/audit-logs/{id}` - Obter log específico
  - `GET /api/admin/audit-logs/export` - Exportar logs (CSV)

- [ ] 8.4.2 Requer autenticação admin

#### Testes:
- [ ] **Teste 8.4.1:** Listar logs (admin)
- [ ] **Teste 8.4.2:** Filtrar logs
- [ ] **Teste 8.4.3:** Exportar logs
- [ ] **Teste 8.4.4:** Não autorizado (usuário comum não pode acessar)

#### Checklist de Validação:
- [ ] Endpoints funcionando
- [ ] Autenticação funcionando
- [ ] Filtros funcionando
- [ ] Testes passando
- [ ] Nenhum endpoint existente quebrado

---

### 📊 Resumo Funcionalidade 8

**Status:** ⬜ Não iniciado

**Arquivos Criados:**
- `backend/app/middleware/audit_middleware.py`
- `backend/app/repositories/audit_log.py`
- `backend/app/services/audit_log_service.py`
- `backend/tests/test_audit_*.py`

**Arquivos Modificados:**
- `backend/app/routers/admin.py` (adicionar endpoints)
- `backend/app/main.py` (registrar middleware)

---

# FASE 3 - BAIXA PRIORIDADE

> **Nota:** Aguardar conclusão das Fases 1 e 2 antes de iniciar esta fase.

---

## 🎯 Funcionalidade 9: Workflow de Aprovação

**Prioridade:** 🟢 Baixa  
**Complexidade:** Alta  
**Dependências:** Nenhuma

### Resumo Rápido

- [ ] 9.1 Criar modelo `Approval` e estados (DRAFT, PENDING, APPROVED, REJECTED)
- [ ] 9.2 Criar service de aprovação
- [ ] 9.3 Criar endpoints de aprovação
- [ ] 9.4 Frontend - Interface de aprovação
- [ ] 9.5 Integrar notificações

**Arquivos:** `backend/app/models.py`, `backend/app/services/approval_service.py`, `backend/app/routers/approvals.py`

---

## 🎯 Funcionalidade 10: Integração com Sistemas Contábeis

**Prioridade:** 🟢 Baixa  
**Complexidade:** Alta  
**Dependências:** Nenhuma

### Resumo Rápido

- [ ] 10.1 Criar formatos de exportação (XML, TXT)
- [ ] 10.2 Criar templates para ERPs comuns (TOTVS, SAP)
- [ ] 10.3 Criar endpoint de exportação
- [ ] 10.4 Frontend - Botão de exportação

**Arquivos:** `backend/app/services/export_service.py`, `backend/app/routers/exports.py`

---

## 🎯 Funcionalidade 11: Multi-idioma

**Prioridade:** 🟢 Baixa  
**Complexidade:** Baixa  
**Dependências:** Nenhuma

### Resumo Rápido

- [ ] 11.1 Criar arquivos de tradução (pt-BR.json, en-US.json, es-ES.json)
- [ ] 11.2 Implementar sistema de i18n no frontend
- [ ] 11.3 Adicionar seletor de idioma

**Arquivos:** `assets/i18n/pt-BR.json`, `assets/i18n/en-US.json`, `assets/js/i18n.js`

---

## 🎯 Funcionalidade 12: API GraphQL

**Prioridade:** 🟢 Baixa  
**Complexidade:** Média  
**Dependências:** Nenhuma

### Resumo Rápido

- [ ] 12.1 Instalar Strawberry GraphQL (ou similar)
- [ ] 12.2 Criar schema GraphQL
- [ ] 12.3 Criar resolvers
- [ ] 12.4 Registrar endpoint GraphQL

**Arquivos:** `backend/app/graphql/schema.py`, `backend/app/graphql/resolvers.py`

---

## 🎯 Funcionalidade 13: Suporte Multi-moeda

**Prioridade:** 🟢 Baixa  
**Complexidade:** Média  
**Dependências:** API de câmbio

### Resumo Rápido

- [ ] 13.1 Adicionar campo `currency` ao modelo Contract
- [ ] 13.2 Integrar API de câmbio
- [ ] 13.3 Converter valores em relatórios consolidados
- [ ] 13.4 Frontend - Seletor de moeda

**Arquivos:** Modificar `backend/app/models.py`, `backend/app/services/currency_service.py`

---

# 📊 Checklist Geral de Implementação

## Antes de Iniciar Cada Funcionalidade

- [ ] Revisar documentação existente
- [ ] Verificar dependências
- [ ] Criar branch Git: `feature/nome-da-funcionalidade`
- [ ] Executar testes existentes (todos devem passar)

## Durante Implementação

- [ ] Seguir padrões de código existentes
- [ ] Escrever testes junto com código
- [ ] Documentar código complexo
- [ ] Commits frequentes e descritivos

## Antes de Merge

- [ ] Todos os testes passando (novos e existentes)
- [ ] Cobertura de testes > 80% para código novo
- [ ] Código revisado (self-review)
- [ ] Documentação atualizada
- [ ] Testes manuais realizados
- [ ] Performance aceitável
- [ ] Nenhuma funcionalidade existente quebrada

## Após Merge

- [ ] Monitorar logs em produção
- [ ] Coletar feedback de usuários
- [ ] Ajustar conforme necessário

---

# 🔄 Processo de Testes

## Níveis de Teste

### 1. Testes Unitários
- Testar funções/métodos isoladamente
- Mockar dependências externas
- Cobertura > 80%

### 2. Testes de Integração
- Testar interação entre componentes
- Testar com banco de dados real (SQLite in-memory)
- Testar APIs end-to-end

### 3. Testes End-to-End
- Testar fluxo completo do usuário
- Testar em ambiente similar a produção
- Testar integração frontend-backend

### 4. Testes Manuais
- Testar UI/UX
- Testar casos edge
- Testar em diferentes navegadores

## Comandos de Teste

```bash
# Backend - Todos os testes
cd backend
pytest -v

# Backend - Com cobertura
pytest -v --cov=app --cov-report=html

# Backend - Teste específico
pytest tests/test_economic_indexes_api.py -v

# Backend - Testes com markers
pytest -v -m "not slow"  # Excluir testes lentos
pytest -v -m integration  # Apenas testes de integração

# Frontend - Teste manual
# Abrir navegador e testar funcionalidades

# E2E - Teste completo do sistema
.\testar_sistema_completo.ps1
```

## Estrutura de Testes Existente

### Fixtures Disponíveis (conftest.py)

- `client` - AsyncClient do FastAPI
- `db_session` - Sessão do banco de dados (SQLite in-memory)
- `basic_user` - Usuário com plano básico
- `pro_user` - Usuário com plano pro
- `admin_user` - Usuário admin
- `basic_license` - Licença básica
- `active_subscription` - Assinatura ativa

### Padrões de Teste

1. **Testes Unitários:** Testar funções isoladamente
2. **Testes de Integração:** Testar interação entre componentes
3. **Testes de API:** Usar `client` fixture para testar endpoints
4. **Mockar Dependências Externas:** BCB, Stripe, Email (usar `unittest.mock` ou `pytest-mock`)

### Exemplo de Teste

```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
async def test_create_economic_index(client: AsyncClient, db_session: AsyncSession):
    """Teste de criação de índice econômico"""
    # Arrange
    data = {
        "index_type": "SELIC",
        "reference_date": "2024-01-01",
        "value": 12.75,
        "source": "BCB"
    }
    
    # Act
    response = await client.post("/api/economic-indexes", json=data)
    
    # Assert
    assert response.status_code == 201
    result = response.json()
    assert result["index_type"] == "SELIC"
    assert result["value"] == 12.75
```

---

# 📝 Notas Importantes

1. **Não Quebrar Código Existente**
   - Sempre executar todos os testes antes de commitar
   - Revisar mudanças em arquivos existentes com cuidado
   - Testar funcionalidades existentes após mudanças

2. **Priorizar Qualidade**
   - Código limpo e bem documentado
   - Testes robustos
   - Tratamento de erros adequado

3. **Comunicação**
   - Documentar decisões técnicas
   - Atualizar este documento conforme progresso
   - Reportar problemas encontrados

---

---

# 📈 Métricas de Progresso

## Fase 1 - Alta Prioridade

| Funcionalidade | Status | Progresso | Testes |
|----------------|--------|-----------|--------|
| 1. API de Índices Econômicos | ⬜ | 0% | 0/15 |
| 2. Sistema de Alertas | ⬜ | 0% | 0/12 |
| 3. Upload de Documentos | ⬜ | 0% | 0/10 |
| 4. Dashboard Analítico | ⬜ | 0% | 0/8 |

## Fase 2 - Média Prioridade

| Funcionalidade | Status | Progresso | Testes |
|----------------|--------|-----------|--------|
| 5. Notas Explicativas | ⬜ | 0% | 0/6 |
| 6. Simulação de Cenários | ⬜ | 0% | 0/10 |
| 7. Remensuração Automática | ⬜ | 0% | 0/15 |
| 8. Auditoria | ⬜ | 0% | 0/12 |

## Fase 3 - Baixa Prioridade

| Funcionalidade | Status | Progresso |
|----------------|--------|-----------|
| 9. Workflow Aprovação | ⬜ | 0% |
| 10. Integração ERP | ⬜ | 0% |
| 11. Multi-idioma | ⬜ | 0% |
| 12. API GraphQL | ⬜ | 0% |
| 13. Multi-moeda | ⬜ | 0% |

---

# 🔍 Checklist de Qualidade por Funcionalidade

Antes de marcar uma funcionalidade como concluída, verificar:

## Código
- [ ] Código segue padrões do projeto (Service-Repository pattern)
- [ ] Código documentado (docstrings onde necessário)
- [ ] Sem código duplicado
- [ ] Tratamento de erros adequado
- [ ] Logging apropriado

## Testes
- [ ] Testes unitários criados (cobertura > 80% para código novo)
- [ ] Testes de integração criados
- [ ] Todos os testes passando
- [ ] Nenhum teste existente quebrado
- [ ] Testes manuais realizados

## Performance
- [ ] Queries otimizadas (índices criados se necessário)
- [ ] Tempo de resposta < 500ms para endpoints GET
- [ ] Tempo de resposta < 2s para endpoints POST (exceto operações pesadas)

## Segurança
- [ ] Autenticação/autorização implementada corretamente
- [ ] Validação de inputs
- [ ] Nenhum secret exposto
- [ ] SQL injection prevenido (usar SQLAlchemy, não SQL raw)

## Integração
- [ ] Frontend integrado (se aplicável)
- [ ] API documentada no Swagger
- [ ] Nenhuma funcionalidade existente quebrada
- [ ] Migrations aplicadas e testadas

## Documentação
- [ ] README atualizado (se necessário)
- [ ] Comentários no código (código complexo)
- [ ] Este documento atualizado

---

# 🚨 Regras de Ouro

1. **Nunca quebrar código existente**
   - Sempre executar todos os testes antes de commitar
   - Se algum teste quebrar, corrigir antes de continuar

2. **Testes primeiro (quando possível)**
   - TDD (Test-Driven Development) é recomendado
   - Pelo menos escrever testes junto com código

3. **Commits frequentes e descritivos**
   - Commits pequenos e focados
   - Mensagens claras: "feat: adiciona API de índices econômicos"

4. **Revisão antes de merge**
   - Self-review do código
   - Verificar checklist de qualidade
   - Executar testes completos

5. **Documentar decisões**
   - Se fizer escolha arquitetural importante, documentar em `docs/ai/DECISIONS.md`
   - Atualizar `docs/ai/CHANGELOG_AI.md` após implementação

---

**Última Atualização:** 2026-01-01  
**Próxima Revisão:** Após conclusão da Fase 1

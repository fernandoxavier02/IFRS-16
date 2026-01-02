# 📧 Fluxo de Envio de Emails - Sistema de Notificações

## 📋 Visão Geral

O sistema de envio de emails está **totalmente integrado** ao sistema de notificações. Sempre que uma notificação é criada, um email é enviado automaticamente ao usuário (exceto se explicitamente desabilitado).

---

## 🔄 Fluxo Completo

### 1. **Trigger de Notificação**

Uma notificação pode ser criada por:

#### A) **Remensuração Automática**
```python
# backend/app/services/remeasurement_service.py:559
await NotificationService.notify_remeasurement_done(
    db=db,
    user_id=UUID(contract['user_id']),
    contract_id=UUID(contract['contract_id']),
    contract_name=contract['contract_name'],
    version_number=new_version['version_number'],
    index_type=contract['reajuste_tipo'],
    old_value=remeasurement_data['previous_value'],
    new_value=remeasurement_data['new_value']
)
```

#### B) **Contrato Vencendo** (Job Agendado)
```python
# backend/app/services/contract_expiration_service.py
await NotificationService.notify_contract_expiring(
    db=db,
    user_id=user_id,
    contract_id=contract_id,
    contract_name=contract_name,
    days_until_expiry=15
)
```

#### C) **Índice Econômico Atualizado**
```python
await NotificationService.notify_index_updated(
    db=db,
    user_id=user_id,
    index_type="IGPM",
    reference_date="2025-01-01",
    value="5.5"
)
```

#### D) **Licença Vencendo**
```python
await NotificationService.notify_license_expiring(
    db=db,
    user_id=user_id,
    license_id=license_id,
    days_until_expiry=7
)
```

#### E) **Alerta do Sistema**
```python
await NotificationService.notify_system_alert(
    db=db,
    user_id=user_id,
    title="Manutenção Programada",
    message="O sistema estará em manutenção amanhã..."
)
```

---

### 2. **Criação da Notificação** (`NotificationService.create_notification`)

```python
# backend/app/services/notification_service.py:24-107

# Passo 1: Criar registro no banco
notification = Notification(
    user_id=user_id,
    notification_type=notification_type,
    title=title,
    message=message,
    entity_type=entity_type,
    entity_id=entity_id,
    extra_data=json.dumps(metadata),
    read=False
)
db.add(notification)
await db.commit()

# Passo 2: Enviar email (se send_email=True)
if send_email:
    # Buscar usuário
    user = await db.get(User, user_id)
    
    # Gerar template
    html_content, text_content = _generate_email_template(...)
    
    # Enviar via EmailService
    await EmailService.send_email(
        to_email=user.email,
        subject=title,
        html_content=html_content,
        text_content=text_content
    )
```

---

### 3. **Geração do Template de Email** (`_generate_email_template`)

O sistema gera templates **personalizados** baseados no tipo de notificação:

#### A) **CONTRACT_EXPIRING** (Contrato Vencendo)
```html
<!-- Alerta amarelo com dias até vencimento -->
⚠️ Atenção: Este contrato vence em 15 dias.
Verifique se é necessário renovar ou encerrar o contrato.
```

#### B) **REMEASUREMENT_DONE** (Remensuração Realizada)
```html
<!-- Box azul com detalhes da remensuração -->
📊 Detalhes da Remensuração:
- Índice: IGPM
- Valor Anterior: 5.5000%
- Novo Valor: 6.0000%
- Nova Versão: #2
```

#### C) **INDEX_UPDATED** (Índice Atualizado)
```html
<!-- Box azul com informações do índice -->
📈 Índice Atualizado:
- Tipo: IGPM
- Data de Referência: 2025-01-01
- Valor: 5.5%
```

#### D) **LICENSE_EXPIRING** (Licença Vencendo)
```html
<!-- Alerta amarelo com dias até expiração -->
⚠️ Atenção: Sua licença expira em 7 dias.
Renove para continuar tendo acesso ao sistema.
```

#### E) **SYSTEM_ALERT** (Alerta Genérico)
```html
<!-- Sem box extra, apenas título e mensagem -->
```

---

### 4. **Envio via EmailService** (`EmailService.send_email`)

```python
# backend/app/services/email_service.py:103-121

# Envia email de forma assíncrona via SMTP
await EmailService.send_email(
    to_email="usuario@exemplo.com",
    subject="Contrato 'Contrato Teste' próximo do vencimento",
    html_content="<html>...</html>",
    text_content="Versão texto simples..."
)
```

**Configuração SMTP** (variáveis de ambiente):
- `SMTP_HOST` - Servidor SMTP
- `SMTP_PORT` - Porta (587 para STARTTLS, 465 para SSL)
- `SMTP_USER` - Usuário SMTP
- `SMTP_PASSWORD` - Senha SMTP
- `SMTP_FROM_EMAIL` - Email remetente
- `SMTP_FROM_NAME` - Nome remetente
- `SMTP_USE_SSL` - Usar SSL (True/False)
- `SMTP_USE_STARTTLS` - Usar STARTTLS (True/False)

---

## 📊 Diagrama do Fluxo

```
┌─────────────────────────────────────────────────────────────┐
│ 1. EVENTO (Remensuração, Contrato Vencendo, etc.)          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. NotificationService.notify_*()                           │
│    - Chama create_notification()                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. NotificationService.create_notification()                │
│    ├─ Criar registro no banco (tabela notifications)       │
│    ├─ Buscar usuário (para obter email)                     │
│    ├─ Gerar template HTML/texto (_generate_email_template)  │
│    └─ Chamar EmailService.send_email()                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. EmailService.send_email()                                │
│    ├─ Criar mensagem MIME (HTML + texto)                   │
│    ├─ Conectar ao servidor SMTP                             │
│    ├─ Autenticar                                            │
│    └─ Enviar email                                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Email entregue ao usuário                                │
│    - Caixa de entrada                                        │
│    - Link para ver detalhes no sistema                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Exemplos Práticos

### Exemplo 1: Remensuração Automática

**Quando:** Job mensal de remensuração executa

**Fluxo:**
1. `RemeasurementService.run_remeasurement_job()` detecta contrato que precisa remensurar
2. Calcula novos valores
3. Cria nova versão do contrato
4. Chama `NotificationService.notify_remeasurement_done()`
5. **Email enviado automaticamente** com:
   - Título: "Remensuração automática: Contrato XYZ"
   - Detalhes: Índice IGPM mudou de 5.5% para 6.0%
   - Link: `https://projeto-pulsar.web.app/contracts.html?contract_id=xxx`

### Exemplo 2: Contrato Vencendo

**Quando:** Job diário verifica contratos vencendo

**Fluxo:**
1. `ContractExpirationService.check_and_notify_expiring_contracts()` executa
2. Busca contratos que vencem nos próximos 30 dias
3. Para cada contrato, chama `NotificationService.notify_contract_expiring()`
4. **Email enviado automaticamente** com:
   - Título: "Contrato 'Contrato XYZ' próximo do vencimento"
   - Alerta: "Vence em 15 dias"
   - Link: `https://projeto-pulsar.web.app/contracts.html?contract_id=xxx`

### Exemplo 3: Desabilitar Email (Apenas Notificação)

```python
# Criar notificação SEM enviar email
await NotificationService.create_notification(
    db=db,
    user_id=user_id,
    notification_type=NotificationType.SYSTEM_ALERT,
    title="Notificação Interna",
    message="Esta notificação não enviará email",
    send_email=False  # ← Desabilita envio de email
)
```

---

## ⚙️ Configuração

### Variáveis de Ambiente Necessárias

```bash
# SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-app
SMTP_FROM_EMAIL=noreply@ifrs16.com
SMTP_FROM_NAME=IFRS 16
SMTP_USE_SSL=false
SMTP_USE_STARTTLS=true

# Frontend URL (para links nos emails)
FRONTEND_URL=https://projeto-pulsar.web.app
```

### Verificação de Configuração

Se `SMTP_USER` ou `SMTP_PASSWORD` não estiverem configurados, o sistema:
- ✅ **Ainda cria a notificação** no banco
- ⚠️ **Loga um aviso** mas não falha
- ❌ **Não envia email**

```python
# backend/app/services/email_service.py:34-40
if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
    print("[WARN] SMTP não configurado - email não enviado")
    return False
```

---

## 🛡️ Tratamento de Erros

### 1. **Email Falha, Notificação Não Falha**

```python
try:
    await EmailService.send_email(...)
except Exception as e:
    # Loga erro mas não interrompe o fluxo
    logger.error(f"Erro ao enviar email: {e}")
    # Notificação já foi criada no banco ✅
```

### 2. **Usuário Sem Email**

```python
if user and user.email:
    # Envia email
else:
    # Apenas cria notificação no banco
    # Não tenta enviar email
```

### 3. **SMTP Indisponível**

- EmailService retorna `False`
- Erro é logado
- Notificação permanece no banco
- Usuário pode ver notificação no sistema

---

## 📝 Estrutura do Email

### Template Base (Todos os Tipos)

```html
┌─────────────────────────────────────────┐
│  HEADER (Gradiente azul)                │
│  IFRS 16                                │
│  Sistema de Gestão de Arrendamentos     │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│  TÍTULO (H2)                            │
│  {title}                                │
│                                         │
│  MENSAGEM                               │
│  {message}                              │
│                                         │
│  [BOX EXTRA - Baseado no tipo]          │
│  - CONTRACT_EXPIRING: Alerta amarelo    │
│  - REMEASUREMENT_DONE: Detalhes azul    │
│  - INDEX_UPDATED: Info azul             │
│  - LICENSE_EXPIRING: Alerta amarelo     │
│                                         │
│  [BOTÃO] Ver Detalhes                   │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│  FOOTER (Cinza claro)                   │
│  Precisa de ajuda? Entre em contato... │
│  © 2025 IFRS 16                         │
└─────────────────────────────────────────┘
```

---

## 🔍 Logs e Monitoramento

### Logs Gerados

```python
# Notificação criada
logger.info(f"Notificação criada: user_id={user_id}, type={notification_type.value}")

# Email enviado
logger.info(f"Email enviado para {user.email} sobre notificação {notification.id}")

# Erro no email
logger.error(f"Erro ao enviar email para notificação {notification.id}: {e}")
```

### Verificação Manual

```python
# Verificar se email foi enviado
# 1. Verificar logs do backend
# 2. Verificar caixa de entrada do usuário
# 3. Verificar se notificação foi criada no banco
```

---

## ✅ Resumo

1. **Automático**: Emails são enviados automaticamente quando notificações são criadas
2. **Personalizado**: Templates diferentes para cada tipo de notificação
3. **Resiliente**: Falhas no email não impedem criação da notificação
4. **Configurável**: Pode desabilitar email por notificação (`send_email=False`)
5. **Rastreável**: Logs detalhados de cada envio

---

## 🚀 Próximos Passos

- [ ] Configurar SMTP em produção
- [ ] Testar envio de emails em ambiente de staging
- [ ] Configurar Cloud Scheduler para job de contratos vencendo
- [ ] Monitorar taxa de entrega de emails
- [ ] Implementar retry automático para emails falhados (futuro)

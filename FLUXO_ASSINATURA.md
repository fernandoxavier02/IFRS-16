# Fluxo de Assinatura IFRS 16 - Consolidado

## 🎯 Visão Geral

Este documento apresenta o fluxo completo de assinatura após a consolidação, mostrando desde a escolha do plano até a validação da licença.

---

## 📊 Fluxo Principal - Checkout e Ativação

```mermaid
sequenceDiagram
    autonumber
    actor User as Usuário
    participant Frontend as pricing.html
    participant Stripe as Stripe Pricing Table
    participant Webhook as Webhook Handler
    participant Service as StripeService
    participant Config as PLAN_CONFIG
    participant DB as Database
    participant Email as EmailService
    participant Dashboard as Dashboard

    %% FASE 1: Escolha do Plano
    User->>Frontend: Acessa página de preços
    Frontend->>Config: GET /api/payments/prices
    Config-->>Frontend: 6 planos (Basic/Pro/Enterprise × Monthly/Yearly)
    Frontend-->>User: Exibe tabela de preços

    User->>Frontend: Clica "Assinar" em plano
    Frontend->>Stripe: Redireciona para Pricing Table

    %% FASE 2: Checkout
    User->>Stripe: Preenche dados e paga
    Stripe-->>User: Redireciona para /dashboard.html?success=true

    %% FASE 3: Webhook Processing
    Stripe->>Webhook: POST /api/payments/webhook
    Note over Webhook: checkout.session.completed

    Webhook->>Webhook: Valida signature Stripe

    %% Verificar idempotência
    Webhook->>Service: handle_checkout_completed(session)
    Service->>DB: Verificar stripe_session_id
    alt Session já processada
        DB-->>Service: Subscription existente
        Service-->>Webhook: Retorna subscription (idempotente)
        Webhook-->>Stripe: 200 OK (duplicata ignorada)
    else Nova session
        %% Obter configuração do plano
        Service->>Config: get_plan_by_price_id(price_id)
        Config-->>Service: plan_config {max_contracts: 3/20/-1, duration, features}

        %% Verificar usuário
        Service->>DB: Buscar usuário por email
        alt Usuário não existe
            Service->>Service: Gerar senha temporária (8 chars)
            Service->>DB: Criar User + hash bcrypt
            Note over Service: [OK] Novo usuario criado
        end

        %% Criar License
        Service->>Service: generate_license_key() → FX20251230-IFRS16-ABC123
        Service->>DB: Criar License
        Note over DB: key, user_id, license_type<br/>max_activations (de PLAN_CONFIG)<br/>expires_at, features

        %% Criar Subscription
        Service->>DB: Criar Subscription
        Note over DB: stripe_subscription_id<br/>stripe_session_id (idempotência!)<br/>stripe_price_id, plan_type<br/>license_id (UNIQUE), user_id

        %% Commit atômico
        Service->>DB: COMMIT (transação atômica)
        Note over Service: [OK] Licenca criada

        %% Enviar email
        alt Usuário novo (tem senha temp)
            Service->>Email: send_welcome_email(user, temp_password, license)
            Email-->>User: Email com senha temporária
        else Usuário existente
            Service->>Email: send_subscription_confirmation(user, license)
            Email-->>User: Email de confirmação
        end

        Service-->>Webhook: Subscription criada
        Webhook-->>Stripe: 200 OK
    end

    %% FASE 4: Acesso ao Dashboard
    User->>Dashboard: Acessa /dashboard.html
    Dashboard->>Dashboard: Login com email + senha temp
    Dashboard->>Dashboard: GET /api/user/subscription
    Dashboard-->>User: Exibe licença ativa
```

---

## 🔄 Fluxo de Webhooks - Ciclo de Vida

```mermaid
graph TB
    Start([Stripe envia webhook]) --> Validate{Validar<br/>signature}
    Validate -->|Inválida| Reject[❌ 400 Bad Request]
    Validate -->|Válida| CheckEvent{Tipo de<br/>evento?}

    %% checkout.session.completed
    CheckEvent -->|checkout.session.<br/>completed| CheckSession{Session ID<br/>já existe?}
    CheckSession -->|Sim| Idempotent[⚠️ Idempotência:<br/>Retornar existente]
    CheckSession -->|Não| GetConfig[Obter PLAN_CONFIG<br/>por price_id]
    GetConfig --> CreateUser{Usuário<br/>existe?}
    CreateUser -->|Não| NewUser[Criar User +<br/>senha temp]
    CreateUser -->|Sim| ExistingUser[Usar existente]
    NewUser --> CreateLicense
    ExistingUser --> CreateLicense[Criar License +<br/>Subscription]
    CreateLicense --> CommitDB[(Commit atômico)]
    CommitDB --> SendEmail[📧 Enviar email]
    SendEmail --> Success1[✅ 200 OK]
    Idempotent --> Success1

    %% invoice.paid
    CheckEvent -->|invoice.paid| FindSub1[Buscar Subscription<br/>por stripe_id]
    FindSub1 --> UpdatePeriod[Atualizar<br/>current_period_end]
    UpdatePeriod --> RenewLicense[Renovar License<br/>expires_at]
    RenewLicense --> Success2[✅ 200 OK<br/>[OK] Subscription renovada]

    %% invoice.payment_failed
    CheckEvent -->|invoice.payment_<br/>failed| FindSub2[Buscar Subscription]
    FindSub2 --> MarkPastDue[Marcar status:<br/>PAST_DUE]
    MarkPastDue --> Success3[✅ 200 OK<br/>[WARN] Pagamento falhou]

    %% customer.subscription.deleted
    CheckEvent -->|customer.subscription.<br/>deleted| FindSub3[Buscar Subscription]
    FindSub3 --> CancelSub[Status: CANCELLED]
    CancelSub --> RevokeLicense[Revogar License<br/>revoked=true<br/>status=CANCELLED]
    RevokeLicense --> Success4[✅ 200 OK<br/>[CANCEL] Subscription cancelada]

    %% Evento desconhecido
    CheckEvent -->|Outro| Ignore[ℹ️ 200 OK<br/>Evento ignorado]

    style CheckSession fill:#ffd43b
    style Idempotent fill:#51cf66
    style CreateLicense fill:#4dabf7
    style CommitDB fill:#ff6b6b
    style RevokeLicense fill:#ff6b6b
```

---

## 🗄️ Fluxo de Dados - Arquitetura

```mermaid
erDiagram
    PLAN_CONFIG ||--o{ SUBSCRIPTION : "configura"
    USER ||--o{ SUBSCRIPTION : "possui"
    USER ||--o{ LICENSE : "possui"
    SUBSCRIPTION ||--|| LICENSE : "vincula (1:1)"
    LICENSE ||--o{ VALIDATION_LOG : "registra"

    PLAN_CONFIG {
        string plan_key PK "basic_monthly, pro_yearly"
        string price_id_env "STRIPE_PRICE_BASIC_MONTHLY"
        string license_type "basic, pro, enterprise"
        int duration_months "1, 12"
        int max_contracts "3, 20, -1"
        int max_activations "2, 5, 10"
        string display_name "Básico - Mensal"
        decimal amount "299.00, 3229.20"
        json features "export_excel, multi_user, etc"
    }

    USER {
        uuid id PK
        string email UK "user@example.com"
        string name
        string password_hash "bcrypt"
        string stripe_customer_id UK
        string company_name
        datetime created_at
    }

    SUBSCRIPTION {
        uuid id PK
        uuid user_id FK
        uuid license_id FK "UNIQUE!"
        string stripe_subscription_id UK
        string stripe_session_id UK "Para idempotência"
        string stripe_price_id
        enum plan_type "basic_monthly, pro_yearly"
        enum status "ACTIVE, CANCELLED, PAST_DUE"
        datetime current_period_start
        datetime current_period_end
        datetime created_at
    }

    LICENSE {
        uuid id PK
        string key UK "FX20251230-IFRS16-ABC123"
        uuid user_id FK
        enum license_type "BASIC, PRO, ENTERPRISE"
        enum status "ACTIVE, EXPIRED, CANCELLED"
        int max_activations "de PLAN_CONFIG"
        json features "max_contracts, export_excel, etc"
        datetime expires_at "= subscription.current_period_end"
        boolean revoked
        string revoke_reason
        datetime created_at
    }

    VALIDATION_LOG {
        uuid id PK
        uuid license_id FK
        string machine_id
        string ip_address
        datetime validated_at
    }
```

---

## 🔐 Fluxo de Validação de Licença

```mermaid
sequenceDiagram
    autonumber
    actor App as Aplicação Desktop
    participant API as /api/validate-license
    participant Service as LicenseService
    participant DB as Database
    participant JWT as JWT Token

    App->>API: POST {key, machine_id, app_version}

    API->>API: Validar rate limit (30/min)

    API->>Service: Validar licença
    Service->>DB: SELECT License WHERE key = ?

    alt Licença não encontrada
        DB-->>Service: null
        Service-->>API: 404 Not Found
        API-->>App: ❌ Chave inválida
    end

    Service->>Service: Verificar status

    alt Status não é ACTIVE
        Service-->>API: 403 Forbidden
        API-->>App: ❌ Licença expirada/cancelada
    end

    Service->>Service: Verificar revogação

    alt Licença revogada
        Service-->>API: 403 Forbidden
        API-->>App: ❌ Licença revogada
    end

    Service->>Service: Verificar expiração

    alt expires_at < now()
        Service->>DB: UPDATE status = EXPIRED
        Service-->>API: 403 Forbidden
        API-->>App: ❌ Licença expirada
    end

    Service->>Service: Verificar machine_id (ativações)
    Service->>DB: SELECT COUNT(*) FROM validation_logs<br/>WHERE license_id AND DISTINCT machine_id

    alt Ativações >= max_activations
        alt machine_id não está na lista
            Service-->>API: 403 Forbidden
            API-->>App: ❌ Limite de ativações excedido
        end
    end

    %% Sucesso
    Service->>DB: INSERT validation_log<br/>(license_id, machine_id, ip, timestamp)
    Service->>JWT: create_license_token(license_id, user_id)
    JWT-->>Service: token JWT (24h)

    Service-->>API: 200 OK + token + data
    API-->>App: ✅ {valid: true, token, data: {<br/>  customer_name,<br/>  license_type,<br/>  expires_at,<br/>  features: {max_contracts, export_excel, etc}<br/>}}

    App->>App: Armazenar token JWT
    App->>App: Usar features.max_contracts<br/>para limitar funcionalidades
```

---

## 🔄 Fluxo de Upgrade de Plano

```mermaid
graph TB
    Start([Usuário em Basic]) --> OpenPortal[Clica Gerenciar Pagamento]
    OpenPortal --> Portal[GET /api/payments/portal]
    Portal --> Stripe[Redireciona para<br/>Stripe Customer Portal]
    Stripe --> UserAction{Usuário<br/>escolhe ação}

    UserAction -->|Upgrade| SelectPlan[Escolhe plano Pro]
    SelectPlan --> StripeUpgrade[Stripe processa upgrade]
    StripeUpgrade --> WebhookUpdate[Webhook: customer.subscription.updated]

    WebhookUpdate --> FindSub[Buscar Subscription<br/>por stripe_subscription_id]
    FindSub --> UpdatePrice[Atualizar stripe_price_id]
    UpdatePrice --> GetNewConfig[PLAN_CONFIG.get_plan_by_price_id<br/>→ pro_monthly/pro_yearly]

    GetNewConfig --> UpdateSub[Atualizar Subscription:<br/>plan_type = pro_monthly]
    UpdateSub --> UpdateLicense[Atualizar License:<br/>license_type = PRO<br/>max_activations = 5<br/>features.max_contracts = 20]

    UpdateLicense --> EmailUpgrade[📧 Email confirmação upgrade]
    EmailUpgrade --> Success[✅ Upgrade completo]

    UserAction -->|Cancelar| CancelFlow[Cancelamento]
    CancelFlow --> WebhookCancel[Webhook: subscription.deleted]
    WebhookCancel --> Revoke[Revogar License]
    Revoke --> EmailCancel[📧 Email cancelamento]

    style GetNewConfig fill:#51cf66
    style UpdateLicense fill:#4dabf7
    style Revoke fill:#ff6b6b
```

---

## 📋 Fonte Única de Verdade - PLAN_CONFIG

```mermaid
graph LR
    subgraph "PLAN_CONFIG (config.py)"
        Basic[basic_monthly<br/>3 contratos, 2 ativações<br/>R$ 299/mês]
        BasicY[basic_yearly<br/>3 contratos, 2 ativações<br/>R$ 3.229,20/ano]
        Pro[pro_monthly<br/>20 contratos, 5 ativações<br/>R$ 499/mês]
        ProY[pro_yearly<br/>20 contratos, 5 ativações<br/>R$ 5.389,20/ano]
        Ent[enterprise_monthly<br/>ilimitado, 10 ativações<br/>R$ 999/mês]
        EntY[enterprise_yearly<br/>ilimitado, 10 ativações<br/>R$ 10.789,20/ano]
    end

    subgraph "Consumers"
        Webhook[StripeService<br/>handle_checkout_completed]
        Prices[/api/payments/prices]
        Frontend[pricing.html]
        Renewal[handle_invoice_paid]
    end

    Basic --> Webhook
    BasicY --> Webhook
    Pro --> Webhook
    ProY --> Webhook
    Ent --> Webhook
    EntY --> Webhook

    Basic --> Prices
    BasicY --> Prices
    Pro --> Prices
    ProY --> Prices
    Ent --> Prices
    EntY --> Prices

    Prices --> Frontend

    Basic --> Renewal
    Pro --> Renewal
    Ent --> Renewal

    style Basic fill:#51cf66
    style Pro fill:#4dabf7
    style Ent fill:#ff6b6b
```

---

## 🛡️ Idempotência de Webhooks

```mermaid
sequenceDiagram
    participant Stripe
    participant Webhook as Webhook Handler
    participant Service as StripeService
    participant DB as Database

    Note over Stripe,DB: Cenário: Webhook duplicado (retry automático)

    %% Primeira tentativa
    Stripe->>Webhook: checkout.session.completed<br/>session_id: cs_123
    Webhook->>Service: handle_checkout_completed(session)
    Service->>DB: SELECT * FROM subscriptions<br/>WHERE stripe_session_id = 'cs_123'
    DB-->>Service: null (não existe)
    Service->>DB: INSERT Subscription + License
    DB-->>Service: ✅ Criado
    Service-->>Webhook: subscription_obj
    Webhook-->>Stripe: 200 OK

    Note over Stripe: Aguarda 5 segundos...<br/>Não recebeu resposta (timeout)

    %% Segunda tentativa (duplicada)
    Stripe->>Webhook: checkout.session.completed<br/>session_id: cs_123 (DUPLICADO)
    Webhook->>Service: handle_checkout_completed(session)
    Service->>DB: SELECT * FROM subscriptions<br/>WHERE stripe_session_id = 'cs_123'
    DB-->>Service: subscription existente (encontrado!)

    Note over Service: [WARN] Webhook duplicado:<br/>session_id ja processado: cs_123

    Service-->>Webhook: subscription_obj (existente)
    Webhook-->>Stripe: 200 OK

    Note over DB: ✅ Zero duplicatas criadas!<br/>Unique index protege integridade
```

---

## 📊 Estados da Subscription

```mermaid
stateDiagram-v2
    [*] --> ACTIVE: checkout.session.completed<br/>(criação inicial)

    ACTIVE --> ACTIVE: invoice.paid<br/>(renovação mensal/anual)

    ACTIVE --> PAST_DUE: invoice.payment_failed<br/>(falha no pagamento)

    PAST_DUE --> ACTIVE: invoice.paid<br/>(pagamento recuperado)

    PAST_DUE --> CANCELLED: subscription.deleted<br/>(cancelamento automático)

    ACTIVE --> CANCELLED: subscription.deleted<br/>(usuário cancela)

    CANCELLED --> [*]

    note right of ACTIVE
        License: ACTIVE
        revoked: false
        Validação: ✅ OK
    end note

    note right of PAST_DUE
        License: ACTIVE
        revoked: false
        Validação: ⚠️ Warning
        (ainda funciona)
    end note

    note right of CANCELLED
        License: CANCELLED
        revoked: true
        Validação: ❌ 403
    end note
```

---

## ✅ Validações e Constraints

```mermaid
graph TB
    subgraph "Startup Validation"
        Start[App inicia] --> ValidateStripe{validate_stripe_config}
        ValidateStripe -->|6 price IDs OK| Continue[✅ Inicia app]
        ValidateStripe -->|Falta price ID| Crash[❌ RuntimeError<br/>App não inicia]
    end

    subgraph "Database Constraints"
        License1[licenses.key] --> UK1[UNIQUE]
        Sub1[subscriptions.stripe_subscription_id] --> UK2[UNIQUE]
        Sub2[subscriptions.stripe_session_id] --> UK3[UNIQUE + INDEX<br/>Idempotência]
        Sub3[subscriptions.license_id] --> UK4[UNIQUE<br/>1:1 relationship]
    end

    subgraph "Business Rules"
        ValidateLic[Validação de Licença] --> CheckStatus{Status?}
        CheckStatus -->|ACTIVE| CheckExp{Expirada?}
        CheckStatus -->|EXPIRED| Deny1[❌ 403]
        CheckStatus -->|CANCELLED| Deny2[❌ 403]
        CheckExp -->|Sim| Deny3[❌ 403]
        CheckExp -->|Não| CheckRev{Revogada?}
        CheckRev -->|Sim| Deny4[❌ 403]
        CheckRev -->|Não| CheckAct{Ativações?}
        CheckAct -->|>= max| CheckMachine{Machine ID<br/>conhecida?}
        CheckMachine -->|Não| Deny5[❌ 403 Limite]
        CheckMachine -->|Sim| Allow[✅ 200 OK]
        CheckAct -->|< max| Allow
    end

    style Crash fill:#ff6b6b
    style Continue fill:#51cf66
    style Allow fill:#51cf66
    style Deny1 fill:#ff6b6b
    style Deny2 fill:#ff6b6b
    style Deny3 fill:#ff6b6b
    style Deny4 fill:#ff6b6b
    style Deny5 fill:#ff6b6b
```

---

## 🎯 Resumo dos Endpoints

### Públicos (sem autenticação)
- `POST /api/validate-license` - Valida chave de licença, retorna JWT
- `GET /api/payments/prices` - Lista planos disponíveis (usa PLAN_CONFIG)
- `POST /api/payments/webhook` - Recebe webhooks do Stripe

### Autenticados (requer JWT)
- `GET /api/payments/portal` - Redireciona para Customer Portal
- `GET /api/user/subscription` - Retorna subscription do usuário logado
- `POST /api/check-license` - Verifica status com token JWT

---

## 📈 Métricas de Sucesso

### Consolidação ✅
- ✅ 1 router de pagamentos (payments.py)
- ✅ PLAN_CONFIG como fonte única de verdade
- ✅ Zero código duplicado

### Consistência ✅
- ✅ Limites: 3/20/ilimitado em todo o sistema
- ✅ 6 price IDs validados no startup
- ✅ Idempotência via stripe_session_id

### Qualidade ✅
- ✅ 7/7 testes E2E passando (100%)
- ✅ 165/194 testes unitários (85%)
- ✅ Documentação completa

---

**Criado em:** 2025-12-30
**Versão:** 1.0
**Status:** ✅ Consolidação Completa

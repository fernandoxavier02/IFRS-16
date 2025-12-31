# 30-DATA_BACKEND.md
> **Data Models & Backend — IFRS 16**

---

## Core Domain Models

| Model | Tabela | Propósito |
|-------|--------|-----------|
| `User` | `users` | Contas de clientes |
| `AdminUser` | `admin_users` | Usuários do painel admin |
| `License` | `licenses` | Chaves de licença |
| `Subscription` | `subscriptions` | Assinaturas Stripe |
| `Contract` | `contracts` | Contratos IFRS 16 |
| `ValidationLog` | `validation_logs` | Audit trail de validações |

---

## License Types & Features

| Tipo | Max Contratos | Excel Export | Multi-user |
|------|---------------|--------------|------------|
| Trial | 5 | ❌ | ❌ |
| Basic | 50 | ✅ | ❌ |
| Pro | 500 | ✅ | ✅ (5) |
| Enterprise | ∞ | ✅ | ✅ (∞) |

---

## API Endpoints Principais

### Auth (`/auth`)
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/auth/register` | Criar conta |
| POST | `/auth/login` | Login (retorna JWT) |
| GET | `/auth/me` | Dados do usuário logado |

### Licenses (`/licenses`)
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/licenses/validate` | Validar licença |
| GET | `/licenses/my-licenses` | Licenças do usuário |

### Admin (`/admin`)
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/admin/users` | Listar usuários |
| GET | `/admin/licenses` | Listar licenças |
| POST | `/admin/licenses` | Criar licença |

### Stripe (`/stripe`)
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/stripe/create-checkout-session` | Criar sessão checkout |
| POST | `/stripe/webhook` | Webhook Stripe |

---

## Autenticação de Endpoints

| Tipo | Método |
|------|--------|
| Público | Nenhum |
| User endpoints | `Authorization: Bearer <JWT>` |
| Admin endpoints | `X-Admin-Token` header OU Admin JWT |

---

## Schemas Principais (Pydantic)

```python
# User
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool

# License
class LicenseResponse(BaseModel):
    id: int
    license_key: str
    license_type: str  # trial/basic/pro/enterprise
    status: str
    expires_at: datetime
    is_valid: bool

# Contract
class ContractCreate(BaseModel):
    name: str
    start_date: date
    end_date: date
    monthly_payment: Decimal
```

---

## Database Constraints

1. **Unique:** `users.email`, `licenses.license_key`
2. **Foreign Keys:** `licenses.user_id → users.id`
3. **Indexes:** `licenses.license_key`, `users.email`
4. **Check:** `licenses.status IN ('active', 'expired', 'revoked')`

---

## Testing Strategy

- **Framework:** pytest + pytest-asyncio
- **Database:** SQLite in-memory (`aiosqlite`)
- **Client:** `httpx.AsyncClient` com ASGI transport
- **Fixtures:** `backend/tests/conftest.py`

### Markers
| Marker | Uso |
|--------|-----|
| `@pytest.mark.asyncio` | Testes async |
| `@pytest.mark.slow` | Testes lentos |
| `@pytest.mark.integration` | Testes de integração |

---

*Ver `40-FRONTEND_APP.md` para detalhes do frontend.*

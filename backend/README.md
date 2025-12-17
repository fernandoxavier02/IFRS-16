# IFRS 16 License Management API

API de gerenciamento de licenças para a Calculadora IFRS 16.

## Requisitos

- Python 3.10+
- PostgreSQL 14+

## Configuração

### 1. Criar ambiente virtual

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar variáveis de ambiente

```bash
# Copiar arquivo de exemplo
copy .env.example .env

# Editar .env com suas configurações
```

### 4. Configurar PostgreSQL

```bash
# Criar banco de dados
createdb ifrs16_licenses

# Ou via psql
psql -U postgres -c "CREATE DATABASE ifrs16_licenses;"
```

### 5. Executar migrations

```bash
alembic upgrade head
```

### 6. Criar primeira licença (opcional)

```bash
python -m app.scripts.create_license
```

## Executar

### Desenvolvimento

```bash
uvicorn app.main:app --reload --port 8000
```

### Produção

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Testes

```bash
# Rodar todos os testes
pytest -v

# Com cobertura
pytest -v --cov=app --cov-report=html

# Testes específicos
pytest tests/test_licenses.py -v
pytest tests/test_admin.py -v
pytest tests/test_auth.py -v
```

## Documentação da API

Após iniciar o servidor, acesse:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints

### Públicos

- `POST /api/validate-license` - Validar chave de licença
- `POST /api/check-license` - Verificar status do token

### Administrativos (requer X-Admin-Token)

- `GET /api/admin/licenses` - Listar todas licenças
- `POST /api/admin/generate-license` - Gerar nova licença
- `POST /api/admin/revoke-license` - Revogar licença
- `POST /api/admin/reactivate-license` - Reativar licença

## Estrutura do Projeto

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app principal
│   ├── config.py            # Configurações
│   ├── database.py          # Conexão PostgreSQL
│   ├── models.py            # Modelos SQLAlchemy
│   ├── schemas.py           # Pydantic schemas
│   ├── crud.py              # Operações de banco
│   ├── auth.py              # Autenticação JWT
│   └── routers/
│       ├── licenses.py      # Endpoints de licença
│       └── admin.py         # Endpoints admin
├── tests/
│   ├── conftest.py          # Fixtures pytest
│   ├── test_licenses.py
│   ├── test_admin.py
│   └── test_auth.py
├── alembic/                 # Migrations
├── requirements.txt
├── .env.example
└── README.md
```

## Licença

© 2025 Fernando Xavier - Todos os direitos reservados


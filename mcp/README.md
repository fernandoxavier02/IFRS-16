# MCP Servers - IFRS 16

Servidores MCP (Model Context Protocol) para integração direta com serviços externos.

## 📦 Servidores Disponíveis

### 1. Stripe MCP (`stripe_mcp_server.py`)
Integração completa com a API do Stripe para:
- **Clientes**: Listar, criar, atualizar, deletar
- **Assinaturas**: Gerenciar subscriptions
- **Pagamentos**: Payment Intents, Invoices
- **Produtos/Preços**: Gerenciar catálogo
- **Checkout**: Criar sessões de checkout
- **Webhooks**: Listar e criar endpoints
- **Saldo**: Consultar balance

### 2. Firebase MCP (`firebase_mcp_server.py`)
Integração com Firebase Admin SDK:
- **Firestore**: CRUD completo em coleções/documentos
- **Authentication**: Gerenciar usuários
- **Storage**: Upload/download de arquivos
- **Hosting**: Informações do projeto

### 3. Cloud SQL MCP (`cloudsql_mcp_server.py`)
Conexão direta com PostgreSQL no Google Cloud SQL:
- **Queries**: Executar SQL arbitrário
- **CRUD**: Select, Insert, Update, Delete
- **Schema**: Listar tabelas, descrever estrutura
- **IFRS 16**: Funções específicas (licenses, users, subscriptions)
- **Monitoramento**: Health check, conexões ativas, tamanho do banco

## 🚀 Instalação

### 1. Executar script de setup
```powershell
cd mcp
.\setup_mcps.ps1
```

### 2. Instalar dependências manualmente
```bash
pip install -r mcp/requirements.txt
```

### 3. Configurar credenciais

#### Stripe
1. Acesse https://dashboard.stripe.com/apikeys
2. Copie a Secret Key (`sk_live_...` ou `sk_test_...`)
3. Edite `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "stripe": {
      "command": "npx",
      "args": ["-y", "@stripe/mcp", "--tools=all"],
      "env": {
        "STRIPE_SECRET_KEY": "sk_live_SUA_CHAVE_AQUI"
      }
    }
  }
}
```

#### Firebase
1. Acesse https://console.firebase.google.com/project/ifrs16-app/settings/serviceaccounts/adminsdk
2. Clique em "Gerar nova chave privada"
3. Salve como `firebase-service-account.json` na raiz do projeto
4. Configure a variável de ambiente:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="./firebase-service-account.json"
```

#### Cloud SQL
1. Obtenha o IP do Cloud SQL no Console GCP
2. Configure a connection string:
```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-postgres",
        "postgresql://USER:PASSWORD@HOST:5432/ifrs16_licenses?sslmode=require"
      ]
    }
  }
}
```

## 📝 Uso Programático

### Stripe
```python
from mcp.stripe_mcp_server import StripeMCPServer
import asyncio

async def main():
    stripe = StripeMCPServer(api_key="sk_live_...")
    
    # Listar clientes
    customers = await stripe.list_customers(limit=10)
    print(customers)
    
    # Criar checkout
    checkout = await stripe.create_checkout_session(
        price_id="price_xxx",
        success_url="https://ifrs16-app.web.app/success",
        cancel_url="https://ifrs16-app.web.app/cancel"
    )
    print(checkout["url"])

asyncio.run(main())
```

### Firebase
```python
from mcp.firebase_mcp_server import FirebaseMCPServer
import asyncio

async def main():
    firebase = FirebaseMCPServer(project_id="ifrs16-app")
    
    # Listar coleções
    collections = await firebase.firestore_list_collections()
    print(collections)
    
    # Listar usuários
    users = await firebase.auth_list_users(limit=10)
    print(users)

asyncio.run(main())
```

### Cloud SQL
```python
from mcp.cloudsql_mcp_server import CloudSQLMCPServer
import asyncio

async def main():
    db = CloudSQLMCPServer(
        host="xxx.xxx.xxx.xxx",
        user="postgres",
        password="senha",
        database="ifrs16_licenses"
    )
    
    # Health check
    health = await db.health_check()
    print(health)
    
    # Listar licenças
    licenses = await db.get_licenses(status="active")
    print(licenses)
    
    # Query customizada
    result = await db.execute_query(
        "SELECT * FROM users WHERE email = $1",
        ["user@example.com"]
    )
    print(result)
    
    await db.close()

asyncio.run(main())
```

## 🔧 Configuração do Cursor/Windsurf

O arquivo `.cursor/mcp.json` configura os MCPs para uso no IDE:

```json
{
  "mcpServers": {
    "stripe": {
      "command": "npx",
      "args": ["-y", "@stripe/mcp", "--tools=all"],
      "env": {
        "STRIPE_SECRET_KEY": "sk_live_..."
      }
    },
    "firebase": {
      "command": "npx",
      "args": ["-y", "firebase-mcp"],
      "env": {
        "FIREBASE_PROJECT_ID": "ifrs16-app"
      }
    },
    "postgres": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-postgres",
        "postgresql://USER:PASS@HOST:5432/DB?sslmode=require"
      ]
    }
  }
}
```

## 📊 Tools Disponíveis

### Stripe Tools
| Tool | Descrição |
|------|-----------|
| `stripe_list_customers` | Lista clientes |
| `stripe_get_customer` | Busca cliente por ID |
| `stripe_create_customer` | Cria novo cliente |
| `stripe_list_subscriptions` | Lista assinaturas |
| `stripe_cancel_subscription` | Cancela assinatura |
| `stripe_list_invoices` | Lista faturas |
| `stripe_list_products` | Lista produtos |
| `stripe_list_prices` | Lista preços |
| `stripe_get_balance` | Saldo da conta |
| `stripe_create_checkout_session` | Cria checkout |

### Firebase Tools
| Tool | Descrição |
|------|-----------|
| `firebase_list_collections` | Lista coleções Firestore |
| `firebase_get_documents` | Lista documentos |
| `firebase_get_document` | Busca documento |
| `firebase_create_document` | Cria documento |
| `firebase_update_document` | Atualiza documento |
| `firebase_delete_document` | Deleta documento |
| `firebase_list_users` | Lista usuários Auth |
| `firebase_get_user` | Busca usuário |
| `firebase_create_user` | Cria usuário |
| `firebase_delete_user` | Deleta usuário |
| `firebase_list_files` | Lista arquivos Storage |

### Cloud SQL Tools
| Tool | Descrição |
|------|-----------|
| `cloudsql_execute_query` | Executa SQL |
| `cloudsql_list_tables` | Lista tabelas |
| `cloudsql_describe_table` | Estrutura da tabela |
| `cloudsql_select` | SELECT genérico |
| `cloudsql_insert` | INSERT |
| `cloudsql_update` | UPDATE |
| `cloudsql_delete` | DELETE |
| `cloudsql_get_licenses` | Lista licenças IFRS16 |
| `cloudsql_get_users` | Lista usuários |
| `cloudsql_health_check` | Verifica conexão |

## ⚠️ Segurança

- **NUNCA** commite credenciais no repositório
- Use variáveis de ambiente para chaves sensíveis
- O arquivo `.cursor/mcp.json` está no `.gitignore`
- Rotacione chaves regularmente

## 📁 Estrutura

```
mcp/
├── __init__.py              # Exports
├── stripe_mcp_server.py     # Servidor Stripe
├── firebase_mcp_server.py   # Servidor Firebase
├── cloudsql_mcp_server.py   # Servidor Cloud SQL
├── mcp_config_template.json # Template de config
├── requirements.txt         # Dependências Python
├── setup_mcps.ps1          # Script de instalação
└── README.md               # Esta documentação
```

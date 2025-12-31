# Comandos para Visualizar o Banco de Dados

## 🔍 Ver Usuários

### Opção 1: Script Python (Recomendado)
```bash
cd backend
python ver_usuarios.py
```

**Output exemplo:**
```
====================================================================================================
USUÁRIOS CADASTRADOS (1)
====================================================================================================

[1] Fernando Xavier
    ID: 547bc2d00e2244e49270a420bddcb088
    Email: fernando.xavier@forvismazars.com.br
    Ativo: Sim
    Email verificado: Não
    Criado em: 2025-12-07 23:21:01.957288
    Último login: 2025-12-07 23:21:09.990795

====================================================================================================
Total: 1 usuário(s)
====================================================================================================

[INFO] Assinaturas no banco: 0
[INFO] Licenças no banco: 3
```

---

## 📊 Outras Consultas Úteis

### Ver Licenças
Crie um arquivo `ver_licencas.py`:
```python
import sqlite3

conn = sqlite3.connect("ifrs16_licenses.db")
cursor = conn.cursor()

cursor.execute("""
    SELECT id, key, license_type, status, expires_at, created_at
    FROM licenses
    ORDER BY created_at DESC;
""")

print("\nLICENÇAS:")
for row in cursor.fetchall():
    print(f"  Chave: {row[1]}")
    print(f"  Tipo: {row[2]}")
    print(f"  Status: {row[3]}")
    print(f"  Expira em: {row[4]}")
    print()

conn.close()
```

Execute:
```bash
cd backend
python ver_licencas.py
```

---

### Ver Assinaturas
Crie um arquivo `ver_assinaturas.py`:
```python
import sqlite3

conn = sqlite3.connect("ifrs16_licenses.db")
cursor = conn.cursor()

cursor.execute("""
    SELECT s.id, s.plan_type, s.status, s.current_period_end, u.email
    FROM subscriptions s
    JOIN users u ON s.user_id = u.id
    ORDER BY s.created_at DESC;
""")

print("\nASSINATURAS:")
for row in cursor.fetchall():
    print(f"  Usuário: {row[4]}")
    print(f"  Plano: {row[1]}")
    print(f"  Status: {row[2]}")
    print(f"  Expira: {row[3]}")
    print()

conn.close()
```

Execute:
```bash
cd backend
python ver_assinaturas.py
```

---

### Ver Contratos
Crie um arquivo `ver_contratos.py`:
```python
import sqlite3

conn = sqlite3.connect("ifrs16_licenses.db")
cursor = conn.cursor()

cursor.execute("""
    SELECT c.name, c.status, c.categoria, u.email, c.created_at
    FROM contracts c
    JOIN users u ON c.user_id = u.id
    WHERE c.is_deleted = 0
    ORDER BY c.created_at DESC;
""")

print("\nCONTRATOS:")
for row in cursor.fetchall():
    print(f"  Nome: {row[0]}")
    print(f"  Usuário: {row[3]}")
    print(f"  Status: {row[1]}")
    print(f"  Categoria: {row[2]}")
    print(f"  Criado: {row[4]}")
    print()

conn.close()
```

Execute:
```bash
cd backend
python ver_contratos.py
```

---

## 🛠️ Ferramentas Gráficas (Opcional)

### DB Browser for SQLite (Recomendado)
1. Download: https://sqlitebrowser.org/
2. Instalar
3. Abrir: `backend/ifrs16_licenses.db`
4. Navegar pelas tabelas visualmente

### VS Code Extension
1. Instalar extensão: **SQLite Viewer**
2. Abrir arquivo: `backend/ifrs16_licenses.db`
3. Clicar com botão direito → "Open Database"

---

## 📋 Consultas SQL Diretas

Se você tiver SQLite instalado no sistema:

### Ver estrutura da tabela users
```bash
cd backend
sqlite3 ifrs16_licenses.db ".schema users"
```

### Ver todos os usuários
```bash
sqlite3 ifrs16_licenses.db "SELECT email, name, is_active FROM users;"
```

### Contar registros
```bash
sqlite3 ifrs16_licenses.db "SELECT COUNT(*) FROM users;"
sqlite3 ifrs16_licenses.db "SELECT COUNT(*) FROM licenses;"
sqlite3 ifrs16_licenses.db "SELECT COUNT(*) FROM subscriptions;"
```

---

## 🔧 Resetar Banco de Dados (CUIDADO!)

**ATENÇÃO:** Isso apaga TODOS os dados!

```bash
cd backend
rm ifrs16_licenses.db  # Deletar banco antigo
python -m alembic upgrade head  # Recriar estrutura
```

Ou usando o servidor (ele recria automaticamente em dev mode):
```bash
cd backend
rm ifrs16_licenses.db
python -m uvicorn app.main:app --reload
```

---

## 🗂️ Localização do Banco

**Desenvolvimento (SQLite):**
- Arquivo: `backend/ifrs16_licenses.db`
- Tipo: SQLite 3
- Acesso: Direto via filesystem

**Produção (PostgreSQL):**
- Host: Configurado em `DATABASE_URL` (.env)
- Acesso: Via cliente PostgreSQL (psql, pgAdmin, DBeaver)

---

## 📊 Status Atual do Banco

Execute `ver_usuarios.py` para ver:
- ✅ 1 usuário cadastrado
- ✅ 3 licenças no banco
- ✅ 0 assinaturas ativas

---

## 🚀 Atalhos Úteis

Adicione ao [ACESSO_RAPIDO.md](ACESSO_RAPIDO.md):

```bash
# Ver usuários
cd backend && python ver_usuarios.py

# Ver licenças
cd backend && python ver_licencas.py

# Ver assinaturas
cd backend && python ver_assinaturas.py

# Ver contratos
cd backend && python ver_contratos.py
```

---

**Scripts criados:**
- ✅ [ver_usuarios.py](backend/ver_usuarios.py) - Listar usuários
- 📝 ver_licencas.py - Criar se necessário
- 📝 ver_assinaturas.py - Criar se necessário
- 📝 ver_contratos.py - Criar se necessário

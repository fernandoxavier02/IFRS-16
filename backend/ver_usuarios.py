"""
Script simples para ver usuários do banco SQLite
"""
import sqlite3
from datetime import datetime

# Conectar ao banco SQLite
db_path = "ifrs16_licenses.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Verificar se a tabela users existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
    if not cursor.fetchone():
        print("[ERRO] Tabela 'users' não encontrada no banco de dados.")
        exit(1)

    # Listar colunas da tabela users
    cursor.execute("PRAGMA table_info(users);")
    colunas = cursor.fetchall()
    nomes_colunas = [col[1] for col in colunas]

    print(f"\n{'='*100}")
    print(f"COLUNAS DA TABELA USERS")
    print(f"{'='*100}")
    print(f"Colunas disponíveis: {', '.join(nomes_colunas)}\n")

    # Buscar todos os usuários
    query = "SELECT * FROM users ORDER BY created_at DESC;"
    cursor.execute(query)
    usuarios = cursor.fetchall()

    if not usuarios:
        print("[INFO] Nenhum usuário encontrado no banco de dados.\n")
        conn.close()
        exit(0)

    print(f"{'='*100}")
    print(f"USUÁRIOS CADASTRADOS ({len(usuarios)})")
    print(f"{'='*100}\n")

    for i, user in enumerate(usuarios, 1):
        user_dict = dict(zip(nomes_colunas, user))

        print(f"[{i}] {user_dict.get('name', 'N/A')}")
        print(f"    ID: {user_dict.get('id', 'N/A')}")
        print(f"    Email: {user_dict.get('email', 'N/A')}")

        if 'company_name' in user_dict and user_dict.get('company_name'):
            print(f"    Empresa: {user_dict['company_name']}")

        print(f"    Ativo: {'Sim' if user_dict.get('is_active') else 'Não'}")
        print(f"    Email verificado: {'Sim' if user_dict.get('email_verified') else 'Não'}")

        if 'password_must_change' in user_dict:
            print(f"    Precisa trocar senha: {'Sim' if user_dict.get('password_must_change') else 'Não'}")

        if 'stripe_customer_id' in user_dict and user_dict.get('stripe_customer_id'):
            print(f"    Stripe Customer ID: {user_dict['stripe_customer_id']}")

        if 'created_at' in user_dict and user_dict.get('created_at'):
            print(f"    Criado em: {user_dict['created_at']}")

        if 'last_login' in user_dict and user_dict.get('last_login'):
            print(f"    Último login: {user_dict['last_login']}")

        if 'password_changed_at' in user_dict and user_dict.get('password_changed_at'):
            print(f"    Senha alterada em: {user_dict['password_changed_at']}")

        print()

    print(f"{'='*100}")
    print(f"Total: {len(usuarios)} usuário(s)")
    print(f"{'='*100}\n")

    # Buscar assinaturas
    cursor.execute("SELECT COUNT(*) FROM subscriptions;")
    total_subs = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM licenses;")
    total_licenses = cursor.fetchone()[0]

    print(f"[INFO] Assinaturas no banco: {total_subs}")
    print(f"[INFO] Licenças no banco: {total_licenses}\n")

    conn.close()

except sqlite3.Error as e:
    print(f"[ERRO] Erro ao acessar banco de dados: {e}")
    exit(1)

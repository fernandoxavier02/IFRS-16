"""
Script para limpar TODOS os DADOS do banco de dados SQLite
Mantém a estrutura (tabelas) intacta, remove apenas os registros
ATENÇÃO: Esta ação é IRREVERSÍVEL!
"""
import sqlite3
import os

db_path = "ifrs16_licenses.db"

print("\n" + "="*80)
print("ATENÇÃO: Este script irá APAGAR TODOS OS REGISTROS do banco!")
print("="*80)
print(f"\nBanco de dados: {db_path}")
print("\nSerão deletados:")
print("  - Todos os usuários")
print("  - Todas as licenças")
print("  - Todas as assinaturas")
print("  - Todos os contratos")
print("  - Todos os dados relacionados")
print("\nA ESTRUTURA DAS TABELAS será MANTIDA.")
print("\n" + "="*80)

# Execução automática (sem confirmação interativa)
print("\n[INFO] Iniciando limpeza automática dos dados...\n")

try:
    # Verificar se o banco existe
    if not os.path.exists(db_path):
        print(f"\n[ERRO] Banco de dados '{db_path}' não encontrado.\n")
        exit(1)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Desabilitar foreign keys temporariamente
    cursor.execute("PRAGMA foreign_keys = OFF;")

    # Listar todas as tabelas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tabelas = [row[0] for row in cursor.fetchall()]

    print(f"\n[INFO] Encontradas {len(tabelas)} tabelas no banco de dados.")
    print(f"[INFO] Tabelas: {', '.join(tabelas)}\n")

    # Contar registros antes da limpeza
    totais_antes = {}
    for tabela in tabelas:
        cursor.execute(f"SELECT COUNT(*) FROM {tabela};")
        totais_antes[tabela] = cursor.fetchone()[0]

    print("="*80)
    print("REGISTROS ANTES DA LIMPEZA:")
    print("="*80)
    for tabela, total in totais_antes.items():
        print(f"  {tabela}: {total} registro(s)")

    # Deletar dados de todas as tabelas
    print("\n" + "="*80)
    print("INICIANDO LIMPEZA...")
    print("="*80 + "\n")

    for tabela in tabelas:
        try:
            cursor.execute(f"DELETE FROM {tabela};")
            registros_deletados = cursor.rowcount
            print(f"  ✓ {tabela}: {registros_deletados} registro(s) deletado(s)")
        except sqlite3.Error as e:
            print(f"  ✗ {tabela}: Erro ao deletar - {e}")

    # Commit das mudanças
    conn.commit()

    # Reabilitar foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Verificar registros após limpeza
    print("\n" + "="*80)
    print("REGISTROS APÓS LIMPEZA:")
    print("="*80)
    
    totais_depois = {}
    for tabela in tabelas:
        cursor.execute(f"SELECT COUNT(*) FROM {tabela};")
        totais_depois[tabela] = cursor.fetchone()[0]
        print(f"  {tabela}: {totais_depois[tabela]} registro(s)")

    # Vacuum para otimizar o banco
    print("\n[INFO] Otimizando banco de dados (VACUUM)...")
    cursor.execute("VACUUM;")
    
    conn.close()

    print("\n" + "="*80)
    print("✓ LIMPEZA CONCLUÍDA COM SUCESSO!")
    print("="*80)
    print("\nResumo:")
    print(f"  - Tabelas processadas: {len(tabelas)}")
    print(f"  - Total de registros deletados: {sum(totais_antes.values())}")
    print(f"  - Banco de dados otimizado")
    print("\n")

except sqlite3.Error as e:
    print(f"\n[ERRO] Erro ao acessar banco de dados: {e}\n")
    exit(1)
except Exception as e:
    print(f"\n[ERRO] Erro inesperado: {e}\n")
    exit(1)

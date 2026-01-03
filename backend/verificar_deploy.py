"""
Script para verificar se todos os arquivos necessarios foram incluidos no deploy
"""
import os
import sys

# Arquivos essenciais que DEVEM estar presentes
ARQUIVOS_ESSENCIAIS = [
    # Core da aplicacao
    'app/__init__.py',
    'app/main.py',
    'app/config.py',
    'app/database.py',
    'app/models.py',
    'app/schemas.py',
    'app/auth.py',
    'app/crud.py',
    
    # Routers principais
    'app/routers/__init__.py',
    'app/routers/auth.py',
    'app/routers/licenses.py',
    'app/routers/payments.py',
    'app/routers/admin.py',
    'app/routers/contracts.py',
    'app/routers/user_dashboard.py',
    'app/routers/economic_indexes.py',
    'app/routers/notifications.py',
    'app/routers/documents.py',
    
    # Services principais
    'app/services/__init__.py',
    'app/services/stripe_service.py',
    'app/services/email_service.py',
    'app/services/dashboard_service.py',
    'app/services/bcb_service.py',
    
    # Configuracao
    'requirements.txt',
    'Dockerfile',
]

# Verificar arquivos
print("=" * 70)
print("VERIFICACAO DE ARQUIVOS ESSENCIAIS PARA DEPLOY")
print("=" * 70)
print()

faltando = []
presentes = []

for arquivo in ARQUIVOS_ESSENCIAIS:
    caminho = os.path.join(os.path.dirname(__file__), arquivo)
    if os.path.exists(caminho):
        presentes.append(arquivo)
        print(f"OK: {arquivo}")
    else:
        faltando.append(arquivo)
        print(f"ERRO: {arquivo} NAO ENCONTRADO")

print()
print("=" * 70)
print(f"RESUMO: {len(presentes)}/{len(ARQUIVOS_ESSENCIAIS)} arquivos encontrados")
print("=" * 70)

if faltando:
    print()
    print("ARQUIVOS FALTANDO:")
    for f in faltando:
        print(f"  - {f}")
    sys.exit(1)
else:
    print()
    print("SUCESSO: Todos os arquivos essenciais estao presentes!")
    
    # Verificar se arquivo modificado recentemente esta presente
    arquivo_modificado = 'app/routers/auth.py'
    if os.path.exists(os.path.join(os.path.dirname(__file__), arquivo_modificado)):
        print(f"OK: Arquivo modificado ({arquivo_modificado}) esta presente")
        
        # Verificar se contem as mudancas recentes
        caminho_auth = os.path.join(os.path.dirname(__file__), arquivo_modificado)
        with open(caminho_auth, 'r', encoding='utf-8') as f:
            conteudo = f.read()
            if 'validate_license_by_user_token' in conteudo:
                print("OK: Funcao validate_license_by_user_token encontrada")
            else:
                print("ERRO: Funcao validate_license_by_user_token NAO encontrada")
                sys.exit(1)
                
            if 'traceback' in conteudo:
                print("OK: Tratamento de erros com traceback encontrado")
            else:
                print("AVISO: Tratamento de erros com traceback nao encontrado")
    else:
        print(f"ERRO: Arquivo modificado ({arquivo_modificado}) NAO encontrado")
        sys.exit(1)

print()
print("VERIFICACAO CONCLUIDA COM SUCESSO!")

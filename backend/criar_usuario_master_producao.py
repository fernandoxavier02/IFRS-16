
"""
Script para criar/verificar usuário master (superadmin) em PRODUÇÃO no CLOUD SQL
"""

import asyncio
import os
import sys
from datetime import datetime
from uuid import uuid4

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Adicionar path do app
sys.path.insert(0, os.path.dirname(__file__))

# Configurar DATABASE_URL de produção (Cloud SQL) via Environment Variable ou Hardcoded fallback
# Fallback usa a connection string com Proxy ou Public IP se a env var não estiver setada no contexto.
# Assumimos que vamos conectar via Cloud SQL Auth Proxy rodando localmente na porta 5432
# ou diretamente via IP público se permitido (menos seguro), mas o ideal é o proxy.
#
# SE ESTIVER RODANDO NO CLOUD RUN: Usar socket connection
# SE ESTIVER RODANDO LOCAL COM PROXY: Usar localhost:5433 (para nao conflitar com postgres local) ou similar
#
# Para este script funcionar localmente conectando no Cloud SQL, o Cloud SQL Auth Proxy deve estar rodando!
# Ex: ./cloud_sql_proxy -instances=ifrs16-app:us-central1:ifrs16-database=tcp:5433
#
# Se não usar proxy, não conecta sem IP Authorizado.

# Vamos assumir que o usuário vai rodar o proxy ou que tem acesso.
# Mas como estamos no ambiente "Agent", talvez seja melhor criar um script SQL e rodar via `gcloud sql connect`?
# SIM! É muito mais robusto usar `gcloud sql connect` do que tentar configurar proxy python aqui.

print("Este script python foi substituído pela abordagem via 'gcloud sql connect' + SQL direto.")
print("Por favor, ignore este arquivo e use o script PowerShell 'criar_usuario_master_cloud_sql.ps1'.")

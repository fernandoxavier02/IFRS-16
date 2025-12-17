#!/usr/bin/env python3
"""Script para atualizar DATABASE_URL no Cloud Run"""
import subprocess
import sys

password = "hEO#A2&x3'Sf0W/7Kt\"N"
database_url = f"postgresql://ifrs16_user:{password}@/ifrs16_licenses?host=/cloudsql/ifrs16-app:us-central1:ifrs16-database"

# Escapar para PowerShell
database_url_escaped = database_url.replace('"', '`"').replace('$', '`$')

cmd = [
    r"C:\Users\Mazars\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd",
    "run", "services", "update", "ifrs16-backend",
    "--update-env-vars", f"DATABASE_URL={database_url}",
    "--region", "us-central1",
    "--project", "ifrs16-app"
]

print(f"Atualizando DATABASE_URL...")
print(f"URL: {database_url[:50]}...")

result = subprocess.run(cmd, capture_output=True, text=True)
print(result.stdout)
if result.returncode != 0:
    print(f"ERRO: {result.stderr}", file=sys.stderr)
    sys.exit(result.returncode)

print("✅ DATABASE_URL atualizado com sucesso!")

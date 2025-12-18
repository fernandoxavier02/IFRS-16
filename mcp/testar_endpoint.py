import requests

# Testar endpoint de contratos diretamente
url = "https://ifrs16-backend-1051753255664.us-central1.run.app/api/contracts"

# Testar sem token (deve dar 401)
print("Testando sem token...")
response = requests.get(url)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:500] if response.text else 'vazio'}")

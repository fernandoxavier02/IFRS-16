# 🔥 Configurar MCP Firebase no Cursor

**MCP (Model Context Protocol)** permite que o Cursor interaja diretamente com o Firebase através de comandos.

---

## ✅ CONFIGURAÇÃO REALIZADA

O arquivo `.cursor/mcp.json` foi criado com a configuração do Firebase MCP.

---

## 📋 PRÓXIMOS PASSOS

### 1️⃣ Instalar Firebase CLI (se ainda não tiver)

```powershell
# Via npm (se tiver Node.js)
npm install -g firebase-tools

# Ou via Chocolatey
choco install firebase-tools

# Verificar instalação
firebase --version
```

### 2️⃣ Fazer Login no Firebase

```bash
cd "c:\Projetos\IFRS 16"
firebase login
```

Siga as instruções na tela para autenticar.

### 3️⃣ Inicializar Firebase no Projeto (se ainda não fez)

```bash
firebase init
```

**Selecionar:**
- ✅ Hosting
- ✅ Functions (opcional)
- ✅ Firestore (opcional, se não usar Cloud SQL)

### 4️⃣ Reiniciar o Cursor

Após configurar, **reinicie o Cursor** para que o MCP seja carregado.

---

## 🎯 O QUE O MCP FIREBASE PERMITE

Com o MCP Firebase configurado, você poderá:

- ✅ **Gerenciar projetos Firebase** via comandos
- ✅ **Deploy automático** do Hosting
- ✅ **Gerenciar Firestore** (se usar)
- ✅ **Configurar Functions** (se usar)
- ✅ **Gerenciar variáveis de ambiente**
- ✅ **Ver logs e status** dos serviços

---

## 🔧 CONFIGURAÇÃO ALTERNATIVA (Global)

Se quiser que o MCP Firebase esteja disponível em **todos os projetos**, edite:

**Windows:** `C:\Users\[SEU_USUARIO]\AppData\Roaming\Cursor\User\mcp.json`

```json
{
  "mcpServers": {
    "firebase": {
      "command": "npx",
      "args": ["-y", "firebase-tools@latest", "mcp"]
    }
  }
}
```

---

## 🧪 TESTAR MCP

Após reiniciar o Cursor, você pode testar pedindo:

- "Liste meus projetos Firebase"
- "Faça deploy do frontend no Firebase"
- "Mostre o status do Firebase Hosting"

---

## 📚 DOCUMENTAÇÃO

- Firebase MCP Docs: https://firebase.google.com/docs/ai-assistance/mcp-server
- Firebase CLI Docs: https://firebase.google.com/docs/cli

---

## 🆘 TROUBLESHOOTING

### MCP não aparece no Cursor
1. Verificar se `firebase-tools` está instalado globalmente
2. Verificar se `firebase login` foi executado
3. Reiniciar o Cursor completamente
4. Verificar se o arquivo `.cursor/mcp.json` está no lugar correto

### Erro ao executar comandos Firebase
- Verificar se está autenticado: `firebase login:list`
- Verificar se o projeto está inicializado: `firebase projects:list`

---

**Última atualização:** 11/12/2025

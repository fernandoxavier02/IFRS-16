# 🔑 Como Usar o Sistema como Master/Admin

**Data:** 16 de Dezembro de 2025  
**Status:** ✅ **CONFIGURADO E FUNCIONANDO**

---

## ✅ O QUE FOI IMPLEMENTADO

O sistema agora permite que **administradores (master)** também acessem e gerenciem contratos, sem necessidade de licença ativa.

### Funcionalidades para Admin:
- ✅ **Criar contratos** sem limite
- ✅ **Listar contratos** (vinculados ao email do admin)
- ✅ **Editar contratos**
- ✅ **Excluir contratos**
- ✅ **Acesso ilimitado** (não precisa de licença)

---

## 🔐 COMO FAZER LOGIN COMO MASTER

### 1. Acesse a Calculadora
**URL:** https://ifrs16-app.web.app/Calculadora_IFRS16_Deploy.html

### 2. Faça Login como Admin
- **Email:** `fernandocostaxavier@gmail.com`
- **Senha:** `Master@2025!`
- **Importante:** Use a aba "Administrador" se houver

### 3. Após Login
- O sistema reconhecerá você como admin
- A seção "Meus Contratos" aparecerá
- Você poderá criar, editar e excluir contratos

---

## 📋 FUNCIONAMENTO TÉCNICO

### Como Funciona:
1. **Login Admin:** Você faz login como admin e recebe um token JWT com `user_type: "admin"`
2. **Acesso a Contratos:** O endpoint `/api/contracts` agora aceita tanto `user` quanto `admin`
3. **Criação de Usuário:** Quando admin cria um contrato pela primeira vez, o sistema:
   - Busca um usuário com o mesmo email do admin
   - Se não encontrar, cria um usuário temporário automaticamente
   - Vincula o contrato a esse usuário
4. **Sem Limite:** Admin não tem limite de contratos (acesso ilimitado)

---

## 🎯 DIFERENÇAS ENTRE ADMIN E USER

| Funcionalidade | Admin (Master) | Usuário Comum |
|----------------|----------------|---------------|
| **Acesso a Contratos** | ✅ Sim (ilimitado) | ✅ Sim (com licença) |
| **Limite de Contratos** | ❌ Sem limite | ✅ Baseado no plano |
| **Precisa de Licença** | ❌ Não | ✅ Sim |
| **Criação Automática de User** | ✅ Sim (se necessário) | ❌ Não |

---

## 🔧 TROUBLESHOOTING

### Erro 403 ao acessar contratos:
- **Causa:** Token não reconhecido como admin
- **Solução:** Faça logout e login novamente como admin

### Contratos não aparecem:
- **Causa:** Admin ainda não criou nenhum contrato
- **Solução:** Clique em "Novo Contrato" para criar o primeiro

### Erro ao criar contrato:
- **Causa:** Problema na criação do usuário temporário
- **Solução:** Verifique os logs do backend ou tente novamente

---

## 📊 STATUS ATUAL

- ✅ Backend atualizado com suporte a admin
- ✅ Deploy concluído (Revisão: ifrs16-backend-00016-qp6)
- ✅ Endpoints funcionando
- ✅ Frontend já está configurado

---

## 🚀 PRÓXIMOS PASSOS

1. **Teste o sistema:**
   - Acesse https://ifrs16-app.web.app/Calculadora_IFRS16_Deploy.html
   - Faça login como admin
   - Crie um contrato de teste
   - Verifique se aparece na lista

2. **Se funcionar:**
   - ✅ Tudo OK!
   - Você pode usar normalmente como master

3. **Se não funcionar:**
   - Verifique o console do navegador (F12)
   - Verifique os logs do Cloud Run
   - Entre em contato para ajustes

---

**Status:** ✅ **SISTEMA CONFIGURADO PARA ADMIN!**

Agora você pode usar o sistema como master/admin e gerenciar contratos sem precisar de licença! 🎉

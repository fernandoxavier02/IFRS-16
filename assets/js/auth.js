// ============================================================
// FUNÇÕES DE AUTENTICAÇÃO E LICENCIAMENTO
// ============================================================

async function fazerLogin() {
    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value;
    const errorEl = document.getElementById('loginError');
    const btnText = document.getElementById('btnLoginText');
    const btnSpinner = document.getElementById('btnLoginSpinner');

    errorEl.classList.add('hidden');

    if (!email || !password) {
        errorEl.textContent = 'Preencha email e senha';
        errorEl.classList.remove('hidden');
        return;
    }

    btnText.textContent = 'Entrando...';
    btnSpinner.classList.remove('hidden');

    try {
        // 1. Fazer login
        const loginResponse = await fetch(`${CONFIG.API_URL}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const loginResult = await loginResponse.json();

        if (!loginResponse.ok) {
            errorEl.textContent = loginResult.detail || 'Email ou senha incorretos';
            errorEl.classList.remove('hidden');
            btnText.textContent = 'Entrar';
            btnSpinner.classList.add('hidden');
            return;
        }

        // 2. Salvar token do usuário (salvar em ambas as chaves para compatibilidade)
        userToken = loginResult.access_token;
        localStorage.setItem('ifrs16_user_token', userToken);
        localStorage.setItem('ifrs16_auth_token', userToken); // Também salvar com chave padrão
        localStorage.setItem('ifrs16_user_type', loginResult.user_type || 'user'); // Salvar tipo de usuário

        // 3. Buscar dados do usuário
        const userResponse = await fetch(`${CONFIG.API_URL}/api/auth/me`, {
            headers: { 'Authorization': `Bearer ${userToken}` }
        });
        if (userResponse.ok) {
            userData = await userResponse.json();
            localStorage.setItem('ifrs16_user_data', JSON.stringify(userData));
        }

        // 4. Buscar licença do usuário
        const licenseResponse = await fetch(`${CONFIG.API_URL}/api/auth/me/license`, {
            headers: { 'Authorization': `Bearer ${userToken}` }
        });

        // Após login bem-sucedido, sempre mostrar tela de ativação da chave
        // O usuário deve inserir a chave recebida no email
        mostrarTelaLicenca();

        // Mostrar mensagem de sucesso no login
        const licenseError = document.getElementById('licenseError');
        licenseError.textContent = '✅ Login realizado! Agora insira a chave de licença recebida no seu email.';
        licenseError.classList.remove('hidden');
        licenseError.classList.remove('text-rose-400');
        licenseError.classList.add('text-emerald-400');

    } catch (error) {
        console.error('Erro no login:', error);
        errorEl.textContent = 'Erro de conexão. Verifique sua internet.';
        errorEl.classList.remove('hidden');
    }

    btnText.textContent = 'Entrar';
    btnSpinner.classList.add('hidden');
}

async function validarLicenca() {
    const input = document.getElementById('licenseInput').value.toUpperCase().trim();
    const errorEl = document.getElementById('licenseError');
    const btnText = document.getElementById('btnValidarText');
    const btnSpinner = document.getElementById('btnValidarSpinner');

    // Resetar estado do erro
    errorEl.classList.add('hidden');
    errorEl.classList.remove('text-emerald-400');
    errorEl.classList.add('text-rose-400');
    document.getElementById('licenseInput').classList.remove('border-rose-500');

    if (!input) {
        errorEl.textContent = 'Digite uma chave de licença';
        errorEl.classList.remove('hidden');
        return;
    }

    btnText.textContent = 'Validando...';
    btnSpinner.classList.remove('hidden');

    try {
        const response = await fetch(`${CONFIG.API_URL}/api/validate-license`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key: input, machine_id: getMachineId(), app_version: CONFIG.VERSION })
        });
        const result = await response.json();

        if (response.ok && result.valid) {
            licenseToken = result.token;
            localStorage.setItem('ifrs16_license', input);
            localStorage.setItem('ifrs16_token', result.token);
            localStorage.setItem('ifrs16_customer_name', result.data.customer_name);
            ativarSistema(input, { nome: result.data.customer_name, expira: result.data.expires_at, tipo: result.data.license_type, features: result.data.features });
            iniciarMonitoramento();
        } else {
            errorEl.textContent = result.detail || result.message || 'Chave de licença inválida ou expirada';
            errorEl.classList.remove('hidden');
            document.getElementById('licenseInput').classList.add('border-rose-500');
        }
    } catch (error) {
        errorEl.textContent = 'Erro de conexão. Verifique sua internet e se o servidor está rodando.';
        errorEl.classList.remove('hidden');
    }

    btnText.textContent = 'Ativar Licença';
    btnSpinner.classList.add('hidden');
}

async function verificarSessaoSalva() {
    // 1. Verificar se é admin logado (acesso total sem licença)
    const adminToken = localStorage.getItem('ifrs16_auth_token') || localStorage.getItem('ifrs16_user_token');
    const userType = localStorage.getItem('ifrs16_user_type');

    if (adminToken && userType === 'admin') {
        try {
            // Verificar se o token de admin ainda é válido
            const response = await fetch(`${CONFIG.API_URL}/api/auth/admin/me`, {
                headers: { 'Authorization': `Bearer ${adminToken}` }
            });

            if (response.ok) {
                const adminData = await response.json();
                // Admin tem acesso total - ativar sistema sem licença
                licencaAtiva = 'ADMIN-ACCESS';
                dadosLicenca = {
                    nome: adminData.username || 'Administrador',
                    tipo: 'ENTERPRISE',
                    expira: null
                };
                mostrarConteudoPrincipal();
                document.getElementById('licensedTo').textContent = adminData.username || 'Administrador';
                document.getElementById('footerLicense').textContent = 'ADMIN';
                document.getElementById('licenseExpiry').textContent = 'Acesso Administrativo';
                calcular();
                console.log('✅ Acesso administrativo ativado');
                return true;
            }
        } catch (error) {
            console.warn('Erro ao verificar token admin:', error);
        }
    }

    // 2. Verificar se tem licença já ativada (chave + token de licença)
    const savedLicense = localStorage.getItem('ifrs16_license');
    const savedToken = localStorage.getItem('ifrs16_token');

    // Se tem licença salva, verificar se ainda é válida
    if (savedLicense && savedToken) {
        try {
            const response = await fetch(`${CONFIG.API_URL}/api/check-license`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${savedToken}` }
            });
            const result = await response.json();

            if (response.ok && result.valid) {
                licenseToken = savedToken;
                ativarSistema(savedLicense, {
                    nome: localStorage.getItem('ifrs16_customer_name') || 'Usuário Licenciado',
                    expira: result.expires_at
                });
                iniciarMonitoramento();
                return true;
            } else {
                // Licença inválida - limpar e pedir login novamente
                limparDadosSessao();
            }
        } catch (error) {
            // Modo offline - ativar mesmo assim se tem licença salva
            ativarSistema(savedLicense, {
                nome: localStorage.getItem('ifrs16_customer_name') || 'Usuário Licenciado (Offline)',
                expira: null
            });
            return true;
        }
    }

    return false;
}

function iniciarMonitoramento() {
    // Admin não precisa de monitoramento de licença
    const userType = localStorage.getItem('ifrs16_user_type');
    if (userType === 'admin') {
        console.log('🔒 Admin: Monitoramento de licença desabilitado (acesso total)');
        return;
    }

    if (checkInterval) clearInterval(checkInterval);

    // Verificação periódica da licença
    checkInterval = setInterval(async () => {
        try {
            const response = await fetch(`${CONFIG.API_URL}/api/check-license`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${licenseToken}` }
            });

            if (!response.ok) {
                const result = await response.json();
                clearInterval(checkInterval);
                bloquearSistema(result.message || 'Sua licença foi revogada ou expirou.');
                return;
            }

            const result = await response.json();
            if (!result.valid) {
                clearInterval(checkInterval);
                bloquearSistema(result.message || 'Sua licença não é mais válida.');
            }
        } catch (error) {
            console.warn('Erro ao verificar licença (offline?):', error);
        }
    }, CONFIG.CHECK_INTERVAL);

    console.log('🔒 Monitoramento de licença ativo (verificação a cada 5 min)');
}

function bloquearSistema(mensagem) {
    limparDadosSessao();
    mostrarTelaLogin();

    const errorEl = document.getElementById('loginError');
    errorEl.textContent = '🚫 ACESSO BLOQUEADO: ' + mensagem;
    errorEl.classList.remove('hidden');

    alert('🚫 ACESSO BLOQUEADO\n\n' + mensagem + '\n\nEntre em contato com o suporte se precisar de ajuda.');
    console.error('🚫 Sistema bloqueado:', mensagem);
}

function limparDadosSessao() {
    localStorage.removeItem('ifrs16_license');
    localStorage.removeItem('ifrs16_token');
    localStorage.removeItem('ifrs16_customer_name');
    localStorage.removeItem('ifrs16_user_token');
    localStorage.removeItem('ifrs16_user_data');

    licenseToken = null;
    userToken = null;
    userData = null;
    licencaAtiva = null;
    dadosLicenca = null;
    if (checkInterval) { clearInterval(checkInterval); checkInterval = null; }
}

function ativarSistema(chave, dados) {
    licencaAtiva = chave;
    dadosLicenca = dados;
    if (dados.nome) localStorage.setItem('ifrs16_customer_name', dados.nome);
    mostrarConteudoPrincipal();
    document.getElementById('licensedTo').textContent = dados.nome || 'Usuário Licenciado';
    document.getElementById('footerLicense').textContent = chave;
    if (dados.expira) {
        const dataExpira = new Date(dados.expira);
        document.getElementById('licenseExpiry').textContent = 'Válido até: ' + formatarData(dataExpira);
    }

    // Mostrar botão Admin se for admin
    const userType = localStorage.getItem('ifrs16_user_type');
    const adminLink = document.getElementById('adminPanelLink');
    if (userType === 'admin' && adminLink) {
        adminLink.classList.remove('hidden');
    }

    calcular();
}

function fazerLogout() {
    if (confirm('Tem certeza que deseja sair?')) {
        limparDadosSessao();
        mostrarTelaLogin();
        document.getElementById('loginEmail').value = '';
        document.getElementById('loginPassword').value = '';
        document.getElementById('loginError').classList.add('hidden');
    }
}

async function alterarSenha() {
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const errorEl = document.getElementById('passwordError');
    const successEl = document.getElementById('passwordSuccess');

    errorEl.classList.add('hidden');
    successEl.classList.add('hidden');

    if (!currentPassword || !newPassword || !confirmPassword) {
        errorEl.textContent = 'Preencha todos os campos';
        errorEl.classList.remove('hidden');
        return;
    }

    if (newPassword !== confirmPassword) {
        errorEl.textContent = 'As senhas não coincidem';
        errorEl.classList.remove('hidden');
        return;
    }

    if (newPassword.length < 8) {
        errorEl.textContent = 'A nova senha deve ter pelo menos 8 caracteres';
        errorEl.classList.remove('hidden');
        return;
    }

    if (!userToken) {
        errorEl.textContent = 'Sessão expirada. Faça login novamente.';
        errorEl.classList.remove('hidden');
        return;
    }

    try {
        const response = await fetch(`${CONFIG.API_URL}/api/auth/change-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${userToken}`
            },
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword
            })
        });
        const result = await response.json();

        if (response.ok) {
            successEl.textContent = 'Senha alterada com sucesso!';
            successEl.classList.remove('hidden');
            document.getElementById('currentPassword').value = '';
            document.getElementById('newPassword').value = '';
            document.getElementById('confirmPassword').value = '';
        } else {
            errorEl.textContent = result.detail || 'Erro ao alterar senha';
            errorEl.classList.remove('hidden');
        }
    } catch (error) {
        errorEl.textContent = 'Erro de conexão';
        errorEl.classList.remove('hidden');
    }
}

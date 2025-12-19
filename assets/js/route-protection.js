/**
 * Route Protection - Proteção de Rotas
 * Verifica autenticação JWT antes de permitir acesso a páginas protegidas
 */

(function() {
    'use strict';

    // Configuração
    const CONFIG = {
        tokenKey: 'ifrs16_auth_token',
        userTypeKey: 'ifrs16_user_type',
        loginPage: 'login.html',
        authChoicePage: 'auth-choice.html',
        protectedPages: [
            'dashboard.html',
            'Calculadora_IFRS16_Deploy.html'
        ]
    };

    /**
     * Verifica se a página atual é protegida
     */
    function isProtectedPage() {
        const currentPage = window.location.pathname.split('/').pop();
        return CONFIG.protectedPages.includes(currentPage);
    }

    /**
     * Verifica se o usuário está autenticado
     */
    function isAuthenticated() {
        const token = localStorage.getItem(CONFIG.tokenKey);
        return !!token;
    }

    /**
     * Obtém o tipo de usuário
     */
    function getUserType() {
        return localStorage.getItem(CONFIG.userTypeKey);
    }

    /**
     * Redireciona para página de login
     */
    function redirectToLogin() {
        console.warn('🔒 Acesso negado: Usuário não autenticado');
        window.location.href = CONFIG.authChoicePage;
    }

    /**
     * Valida o token JWT (verificação básica de formato)
     */
    function isValidTokenFormat(token) {
        if (!token) return false;
        
        // JWT tem 3 partes separadas por ponto
        const parts = token.split('.');
        if (parts.length !== 3) return false;
        
        try {
            // Tenta decodificar o payload (parte 2)
            const payload = JSON.parse(atob(parts[1]));
            
            // Verifica se tem expiração
            if (payload.exp) {
                const now = Math.floor(Date.now() / 1000);
                if (payload.exp < now) {
                    console.warn('🔒 Token expirado');
                    return false;
                }
            }
            
            return true;
        } catch (e) {
            console.error('🔒 Token inválido:', e);
            return false;
        }
    }

    /**
     * Limpa dados de autenticação
     */
    function clearAuth() {
        localStorage.removeItem(CONFIG.tokenKey);
        localStorage.removeItem(CONFIG.userTypeKey);
        localStorage.removeItem('ifrs16_user_token'); // Token antigo
    }

    /**
     * Verifica autenticação e protege a rota
     */
    function checkAuth() {
        // Se não é página protegida, permite acesso
        if (!isProtectedPage()) {
            return true;
        }

        // Verifica se está autenticado
        if (!isAuthenticated()) {
            redirectToLogin();
            return false;
        }

        // Valida formato do token
        const token = localStorage.getItem(CONFIG.tokenKey);
        if (!isValidTokenFormat(token)) {
            clearAuth();
            redirectToLogin();
            return false;
        }

        console.log('✅ Autenticação válida');
        return true;
    }

    /**
     * Adiciona informações do usuário no header (se existir)
     */
    function updateUserInfo() {
        const userType = getUserType();
        const userInfoElement = document.getElementById('userInfo');
        
        if (userInfoElement && userType) {
            const badge = userType === 'admin' ? '👑 Admin' : '👤 Usuário';
            userInfoElement.textContent = badge;
        }
    }

    /**
     * Função de logout global
     */
    window.logout = function() {
        if (confirm('Deseja realmente sair?')) {
            clearAuth();
            window.location.href = CONFIG.loginPage;
        }
    };

    /**
     * Inicialização
     */
    function init() {
        // Verifica autenticação
        if (!checkAuth()) {
            return;
        }

        // Atualiza informações do usuário
        updateUserInfo();

        // Log de debug
        console.log('🔐 Route Protection ativo');
        console.log('📄 Página:', window.location.pathname.split('/').pop());
        console.log('👤 Tipo:', getUserType() || 'Não definido');
    }

    // Executa quando o DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();

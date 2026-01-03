/**
 * Session Manager
 * Gerencia sessões de usuário e heartbeat para controle de acesso simultâneo
 */

class SessionManager {
    constructor() {
        this.heartbeatInterval = null;
        this.heartbeatIntervalMs = 5 * 60 * 1000; // 5 minutos
        this.sessionToken = null;
    }

    /**
     * Retorna a URL da API baseada no hostname
     */
    getApiUrl() {
        const hostname = window.location.hostname;

        if (
            hostname.includes('fxstudioai.com') ||
            hostname.includes('web.app') ||
            hostname.includes('firebaseapp.com')
        ) {
            return 'https://ifrs16-backend-ox4zylcs5a-rj.a.run.app';
        }

        return 'http://localhost:8000';
    }

    /**
     * Inicia o heartbeat da sessão
     * Deve ser chamado após login bem-sucedido
     */
    startHeartbeat() {
        // Obter session token do localStorage
        this.sessionToken = localStorage.getItem('ifrs16_session_token');

        if (!this.sessionToken) {
            console.warn('[SessionManager] Nenhum session token encontrado. Heartbeat não será iniciado.');
            return;
        }

        console.log('[SessionManager] Iniciando heartbeat da sessão...');

        // Limpar intervalo anterior se existir
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
        }

        // Executar heartbeat imediatamente
        this.sendHeartbeat();

        // Configurar intervalo
        this.heartbeatInterval = setInterval(() => {
            this.sendHeartbeat();
        }, this.heartbeatIntervalMs);
    }

    /**
     * Envia heartbeat para manter a sessão ativa
     */
    async sendHeartbeat() {
        const authToken = localStorage.getItem('ifrs16_auth_token');

        if (!authToken || !this.sessionToken) {
            console.warn('[SessionManager] Token de autenticação ou sessão não encontrado');
            this.stopHeartbeat();
            return;
        }

        try {
            const response = await fetch(`${this.getApiUrl()}/api/auth/sessions/heartbeat?session_token=${this.sessionToken}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                console.log('[SessionManager] Heartbeat enviado com sucesso:', data.last_activity);
            } else if (response.status === 401 || response.status === 404) {
                // Sessão expirada ou inativa
                const data = await response.json();
                console.error('[SessionManager] Sessão inválida:', data.detail);

                // Parar heartbeat e redirecionar para login
                this.stopHeartbeat();
                this.handleSessionExpired();
            } else {
                console.error('[SessionManager] Erro ao enviar heartbeat:', response.status);
            }
        } catch (error) {
            console.error('[SessionManager] Erro de conexão no heartbeat:', error);
        }
    }

    /**
     * Para o heartbeat
     */
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
            console.log('[SessionManager] Heartbeat interrompido');
        }
    }

    /**
     * Trata sessão expirada
     */
    handleSessionExpired() {
        alert('Sua sessão expirou ou foi iniciada em outro dispositivo. Você será redirecionado para o login.');

        // Limpar localStorage
        localStorage.removeItem('ifrs16_auth_token');
        localStorage.removeItem('ifrs16_user_token');
        localStorage.removeItem('ifrs16_session_token');
        localStorage.removeItem('ifrs16_user_data');
        localStorage.removeItem('ifrs16_license');
        localStorage.removeItem('ifrs16_token');
        localStorage.removeItem('ifrs16_customer_name');

        // Redirecionar para login
        setTimeout(() => {
            window.location.href = 'login.html';
        }, 2000);
    }

    /**
     * Encerra a sessão atual (logout)
     */
    async terminateSession() {
        const authToken = localStorage.getItem('ifrs16_auth_token');
        this.sessionToken = this.sessionToken || localStorage.getItem('ifrs16_session_token');

        if (!authToken || !this.sessionToken) {
            console.warn('[SessionManager] Nenhuma sessão ativa para encerrar');
            return;
        }

        try {
            const response = await fetch(`${this.getApiUrl()}/api/auth/sessions/terminate?session_token=${this.sessionToken}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                console.log('[SessionManager] Sessão encerrada com sucesso');
            } else {
                console.error('[SessionManager] Erro ao encerrar sessão:', response.status);
            }
        } catch (error) {
            console.error('[SessionManager] Erro de conexão ao encerrar sessão:', error);
        } finally {
            // Parar heartbeat
            this.stopHeartbeat();
        }
    }

    /**
     * Lista sessões ativas do usuário
     */
    async listActiveSessions() {
        const authToken = localStorage.getItem('ifrs16_auth_token');

        if (!authToken) {
            console.warn('[SessionManager] Token de autenticação não encontrado');
            return [];
        }

        try {
            const response = await fetch(`${this.getApiUrl()}/api/auth/sessions/active`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const data = await response.json();
                return data.sessions;
            } else {
                console.error('[SessionManager] Erro ao listar sessões:', response.status);
                return [];
            }
        } catch (error) {
            console.error('[SessionManager] Erro de conexão ao listar sessões:', error);
            return [];
        }
    }
}

// Instância global
const sessionManager = new SessionManager();

// Auto-iniciar heartbeat se houver sessão ativa
if (localStorage.getItem('ifrs16_session_token') && localStorage.getItem('ifrs16_auth_token')) {
    // Aguardar o DOM carregar
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            sessionManager.startHeartbeat();
        });
    } else {
        sessionManager.startHeartbeat();
    }
}

// Encerrar sessão ao fechar a aba/janela (opcional - pode ser comentado se preferir manter sessão)
// window.addEventListener('beforeunload', (e) => {
//     if (sessionManager.sessionToken) {
//         sessionManager.terminateSession();
//     }
// });

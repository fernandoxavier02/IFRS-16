/**
 * Testes para SessionManager (Frontend)
 *
 * Para executar:
 * npm install --save-dev jest @testing-library/dom jest-environment-jsdom
 * npm test
 */

// Mock do localStorage
const localStorageMock = (() => {
    let store = {};
    return {
        getItem: (key) => store[key] || null,
        setItem: (key, value) => { store[key] = value.toString(); },
        removeItem: (key) => { delete store[key]; },
        clear: () => { store = {}; }
    };
})();

global.localStorage = localStorageMock;

// Mock do fetch
global.fetch = jest.fn();

// Mock do window.location
delete global.window.location;
global.window = Object.create(window);
global.window.location = {
    href: '',
    hostname: 'localhost'
};

// Mock do alert
global.alert = jest.fn();

// Importar SessionManager
const fs = require('fs');
const path = require('path');

// Ler código do SessionManager
let sessionManagerCode = fs.readFileSync(
    path.join(__dirname, '..', 'assets', 'js', 'session-manager.js'),
    'utf8'
);

// Mock do document para evitar erros de auto-inicialização
global.document = {
    readyState: 'complete',
    addEventListener: jest.fn()
};

// Executar código que define a classe SessionManager
// Removemos as linhas que tentam auto-inicializar (linhas 199-220)
// e as linhas da instância global (linha 200)
const lines = sessionManagerCode.split('\n');
const classDefinition = lines.slice(0, 197).join('\n');

// Usar Function constructor para garantir que SessionManager seja global
// IMPORTANTE: Não passamos setTimeout/setInterval aqui para que os mocks do Jest funcionem
const defineSessionManager = new Function('window', 'localStorage', 'document', 'fetch', 'alert', 'console', `
    ${classDefinition}
    return SessionManager;
`);

// Executar e atribuir ao global
global.SessionManager = defineSessionManager(
    global.window,
    global.localStorage,
    global.document,
    global.fetch,
    global.alert,
    console
);


describe('SessionManager', () => {
    let sessionManager;

    beforeEach(() => {
        // Limpar mocks
        jest.clearAllMocks();
        localStorageMock.clear();

        // Criar nova instância
        sessionManager = new SessionManager();

        // Limpar intervalos
        if (sessionManager.heartbeatInterval) {
            clearInterval(sessionManager.heartbeatInterval);
        }
    });

    afterEach(() => {
        // Limpar intervalos ao final
        if (sessionManager.heartbeatInterval) {
            clearInterval(sessionManager.heartbeatInterval);
        }
    });

    // =================================================================
    // TESTES DE INICIALIZAÇÃO
    // =================================================================

    describe('Inicialização', () => {
        test('deve criar instância com propriedades corretas', () => {
            expect(sessionManager.heartbeatInterval).toBeNull();
            expect(sessionManager.heartbeatIntervalMs).toBe(5 * 60 * 1000);
            expect(sessionManager.sessionToken).toBeNull();
        });

        test('deve retornar URL da API correta para produção', () => {
            window.location.hostname = 'fxstudioai.com';
            const url = sessionManager.getApiUrl();
            expect(url).toBe('https://ifrs16-backend-1051753255664.us-central1.run.app');
        });

        test('deve retornar URL local para desenvolvimento', () => {
            window.location.hostname = 'localhost';
            const url = sessionManager.getApiUrl();
            expect(url).toBe('http://localhost:8000');
        });
    });

    // =================================================================
    // TESTES DE HEARTBEAT
    // =================================================================

    describe('startHeartbeat()', () => {
        test('não deve iniciar heartbeat se não houver session_token', () => {
            const consoleSpy = jest.spyOn(console, 'warn');

            sessionManager.startHeartbeat();

            expect(sessionManager.heartbeatInterval).toBeNull();
            expect(consoleSpy).toHaveBeenCalledWith(
                '[SessionManager] Nenhum session token encontrado. Heartbeat não será iniciado.'
            );
        });

        test('deve iniciar heartbeat se houver session_token', () => {
            localStorage.setItem('ifrs16_session_token', 'test-token-123');
            localStorage.setItem('ifrs16_auth_token', 'auth-token-123');

            // Mock do sendHeartbeat para não fazer requisição real
            sessionManager.sendHeartbeat = jest.fn();

            sessionManager.startHeartbeat();

            expect(sessionManager.sessionToken).toBe('test-token-123');
            expect(sessionManager.heartbeatInterval).not.toBeNull();
            expect(sessionManager.sendHeartbeat).toHaveBeenCalled();
        });

        test('deve limpar intervalo anterior antes de criar novo', () => {
            localStorage.setItem('ifrs16_session_token', 'test-token-123');
            sessionManager.sendHeartbeat = jest.fn();

            // Iniciar primeira vez
            sessionManager.startHeartbeat();
            const firstInterval = sessionManager.heartbeatInterval;

            // Iniciar segunda vez
            sessionManager.startHeartbeat();
            const secondInterval = sessionManager.heartbeatInterval;

            expect(firstInterval).not.toBe(secondInterval);
        });
    });

    describe('sendHeartbeat()', () => {
        beforeEach(() => {
            localStorage.setItem('ifrs16_session_token', 'test-session-token');
            localStorage.setItem('ifrs16_auth_token', 'test-auth-token');
            sessionManager.sessionToken = 'test-session-token';
        });

        test('deve enviar requisição POST com token correto', async () => {
            fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({ last_activity: '2025-12-31T22:00:00Z' })
            });

            await sessionManager.sendHeartbeat();

            expect(fetch).toHaveBeenCalledWith(
                'http://localhost:8000/api/auth/sessions/heartbeat?session_token=test-session-token',
                {
                    method: 'POST',
                    headers: {
                        'Authorization': 'Bearer test-auth-token',
                        'Content-Type': 'application/json'
                    }
                }
            );
        });

        test('deve logar sucesso quando heartbeat funciona', async () => {
            const consoleSpy = jest.spyOn(console, 'log');

            fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({ last_activity: '2025-12-31T22:00:00Z' })
            });

            await sessionManager.sendHeartbeat();

            expect(consoleSpy).toHaveBeenCalledWith(
                '[SessionManager] Heartbeat enviado com sucesso:',
                '2025-12-31T22:00:00Z'
            );
        });

        test('deve parar heartbeat e redirecionar em erro 401', async () => {
            const consoleErrorSpy = jest.spyOn(console, 'error');
            sessionManager.stopHeartbeat = jest.fn();
            sessionManager.handleSessionExpired = jest.fn();

            fetch.mockResolvedValueOnce({
                ok: false,
                status: 401,
                json: async () => ({ detail: 'Sessão expirada' })
            });

            await sessionManager.sendHeartbeat();

            expect(consoleErrorSpy).toHaveBeenCalledWith(
                '[SessionManager] Sessão inválida:',
                'Sessão expirada'
            );
            expect(sessionManager.stopHeartbeat).toHaveBeenCalled();
            expect(sessionManager.handleSessionExpired).toHaveBeenCalled();
        });

        test('deve parar heartbeat em erro 404', async () => {
            sessionManager.stopHeartbeat = jest.fn();
            sessionManager.handleSessionExpired = jest.fn();

            fetch.mockResolvedValueOnce({
                ok: false,
                status: 404,
                json: async () => ({ detail: 'Sessão não encontrada' })
            });

            await sessionManager.sendHeartbeat();

            expect(sessionManager.stopHeartbeat).toHaveBeenCalled();
            expect(sessionManager.handleSessionExpired).toHaveBeenCalled();
        });

        test('deve logar erro em falha de conexão', async () => {
            const consoleErrorSpy = jest.spyOn(console, 'error');

            fetch.mockRejectedValueOnce(new Error('Network error'));

            await sessionManager.sendHeartbeat();

            expect(consoleErrorSpy).toHaveBeenCalledWith(
                '[SessionManager] Erro de conexão no heartbeat:',
                expect.any(Error)
            );
        });

        test('não deve enviar heartbeat se não houver tokens', async () => {
            const consoleSpy = jest.spyOn(console, 'warn');
            sessionManager.stopHeartbeat = jest.fn();

            localStorage.removeItem('ifrs16_auth_token');
            localStorage.removeItem('ifrs16_session_token');
            sessionManager.sessionToken = null;

            await sessionManager.sendHeartbeat();

            expect(fetch).not.toHaveBeenCalled();
            expect(consoleSpy).toHaveBeenCalled();
            expect(sessionManager.stopHeartbeat).toHaveBeenCalled();
        });
    });

    describe('stopHeartbeat()', () => {
        test('deve limpar intervalo de heartbeat', () => {
            sessionManager.heartbeatInterval = setInterval(() => {}, 1000);

            sessionManager.stopHeartbeat();

            expect(sessionManager.heartbeatInterval).toBeNull();
        });

        test('não deve dar erro se não houver intervalo', () => {
            expect(() => sessionManager.stopHeartbeat()).not.toThrow();
        });

        test('deve logar que heartbeat foi interrompido', () => {
            const consoleSpy = jest.spyOn(console, 'log');
            sessionManager.heartbeatInterval = setInterval(() => {}, 1000);

            sessionManager.stopHeartbeat();

            expect(consoleSpy).toHaveBeenCalledWith(
                '[SessionManager] Heartbeat interrompido'
            );
        });
    });

    // =================================================================
    // TESTES DE SESSÃO EXPIRADA
    // =================================================================

    describe('handleSessionExpired()', () => {
        beforeEach(() => {
            jest.useFakeTimers();
            localStorage.setItem('ifrs16_auth_token', 'token');
            localStorage.setItem('ifrs16_session_token', 'session');
            localStorage.setItem('ifrs16_user_data', 'data');
            localStorage.setItem('ifrs16_license', 'license');
        });

        afterEach(() => {
            jest.useRealTimers();
        });

        test('deve mostrar alerta ao usuário', () => {
            sessionManager.handleSessionExpired();

            expect(alert).toHaveBeenCalledWith(
                'Sua sessão expirou ou foi iniciada em outro dispositivo. Você será redirecionado para o login.'
            );
        });

        test('deve limpar todos os dados do localStorage', () => {
            sessionManager.handleSessionExpired();

            expect(localStorage.getItem('ifrs16_auth_token')).toBeNull();
            expect(localStorage.getItem('ifrs16_session_token')).toBeNull();
            expect(localStorage.getItem('ifrs16_user_data')).toBeNull();
            expect(localStorage.getItem('ifrs16_license')).toBeNull();
        });

        test('deve redirecionar para login após 2 segundos', () => {
            sessionManager.handleSessionExpired();

            expect(window.location.href).toBe('');

            jest.advanceTimersByTime(2000);

            expect(window.location.href).toBe('login.html');
        });
    });

    // =================================================================
    // TESTES DE ENCERRAMENTO
    // =================================================================

    describe('terminateSession()', () => {
        beforeEach(() => {
            localStorage.setItem('ifrs16_session_token', 'test-session');
            localStorage.setItem('ifrs16_auth_token', 'test-auth');
            sessionManager.sessionToken = 'test-session';
        });

        test('deve enviar requisição POST para terminate', async () => {
            fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({ success: true })
            });

            await sessionManager.terminateSession();

            expect(fetch).toHaveBeenCalledWith(
                'http://localhost:8000/api/auth/sessions/terminate?session_token=test-session',
                {
                    method: 'POST',
                    headers: {
                        'Authorization': 'Bearer test-auth',
                        'Content-Type': 'application/json'
                    }
                }
            );
        });

        test('deve parar heartbeat após encerrar sessão', async () => {
            sessionManager.stopHeartbeat = jest.fn();

            fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({ success: true })
            });

            await sessionManager.terminateSession();

            expect(sessionManager.stopHeartbeat).toHaveBeenCalled();
        });

        test('deve logar sucesso ao encerrar sessão', async () => {
            const consoleSpy = jest.spyOn(console, 'log');

            fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({ success: true })
            });

            await sessionManager.terminateSession();

            expect(consoleSpy).toHaveBeenCalledWith(
                '[SessionManager] Sessão encerrada com sucesso'
            );
        });

        test('deve parar heartbeat mesmo em erro', async () => {
            sessionManager.stopHeartbeat = jest.fn();

            fetch.mockRejectedValueOnce(new Error('Network error'));

            await sessionManager.terminateSession();

            expect(sessionManager.stopHeartbeat).toHaveBeenCalled();
        });
    });

    // =================================================================
    // TESTES DE LISTAGEM
    // =================================================================

    describe('listActiveSessions()', () => {
        beforeEach(() => {
            localStorage.setItem('ifrs16_auth_token', 'test-auth');
        });

        test('deve retornar lista de sessões ativas', async () => {
            const mockSessions = {
                sessions: [
                    {
                        session_token: 'token1',
                        device_name: 'Windows PC',
                        ip_address: '192.168.1.1',
                        last_activity: '2025-12-31T22:00:00Z'
                    },
                    {
                        session_token: 'token2',
                        device_name: 'iPhone',
                        ip_address: '192.168.1.2',
                        last_activity: '2025-12-31T21:00:00Z'
                    }
                ],
                total: 2
            };

            fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => mockSessions
            });

            const sessions = await sessionManager.listActiveSessions();

            expect(sessions).toEqual(mockSessions.sessions);
            expect(sessions).toHaveLength(2);
        });

        test('deve retornar array vazio em erro', async () => {
            const consoleErrorSpy = jest.spyOn(console, 'error');

            fetch.mockResolvedValueOnce({
                ok: false,
                status: 500
            });

            const sessions = await sessionManager.listActiveSessions();

            expect(sessions).toEqual([]);
            expect(consoleErrorSpy).toHaveBeenCalled();
        });

        test('deve retornar array vazio sem token', async () => {
            const consoleSpy = jest.spyOn(console, 'warn');
            localStorage.removeItem('ifrs16_auth_token');

            const sessions = await sessionManager.listActiveSessions();

            expect(sessions).toEqual([]);
            expect(fetch).not.toHaveBeenCalled();
            expect(consoleSpy).toHaveBeenCalled();
        });
    });

    // =================================================================
    // TESTES DE INTEGRAÇÃO
    // =================================================================

    describe('Fluxo Completo', () => {
        test('deve gerenciar ciclo de vida completo da sessão', async () => {
            // Setup
            localStorage.setItem('ifrs16_session_token', 'session-123');
            localStorage.setItem('ifrs16_auth_token', 'auth-123');

            // Mock fetch para heartbeat bem-sucedido
            fetch.mockResolvedValue({
                ok: true,
                json: async () => ({ last_activity: new Date().toISOString() })
            });

            // 1. Iniciar heartbeat
            sessionManager.startHeartbeat();
            expect(sessionManager.heartbeatInterval).not.toBeNull();

            // 2. Aguardar primeiro heartbeat
            await new Promise(resolve => setTimeout(resolve, 100));
            expect(fetch).toHaveBeenCalled();

            // 3. Parar heartbeat
            sessionManager.stopHeartbeat();
            expect(sessionManager.heartbeatInterval).toBeNull();
        });
    });
});

// ============================================================
// CONFIGURAÇÃO DA API DE LICENCIAMENTO
// ============================================================

// Detecta automaticamente a URL da API baseado no ambiente
const getApiUrl = () => {
    const hostname = window.location.hostname;
    
    // Firebase Hosting (produção) - Backend no Cloud Run
    if (
        hostname.includes('fxstudioai.com') ||
        hostname.includes('web.app') ||
        hostname.includes('firebaseapp.com')
    ) {
        return 'https://ifrs16-backend-1051753255664.us-central1.run.app';
    }
    
    // Desenvolvimento local
    return 'http://localhost:8000';
};

const CONFIG = {
    VERSION: '1.1.0',
    BUILD: '2025.12.18',
    API_URL: getApiUrl(),
    URL_COMPRA: window.location.origin + '/pricing.html',
    CHECK_INTERVAL: 300000, // Verificar a cada 5 minutos (era 1 hora)
};

// Log da versão no console
console.log(`🧮 Calculadora IFRS 16 v${CONFIG.VERSION} (Build ${CONFIG.BUILD})`);
console.log(`📡 API: ${CONFIG.API_URL}`);

// Estado global
let licencaAtiva = null;
let dadosLicenca = null;
let licenseToken = null;
let userToken = null;
let userData = null;
let checkInterval = null;
let dadosCalculados = {};

// Variáveis globais para contratos (movido de contracts scripts)
let contractsData = [];
let currentContractId = null;
let economicIndexes = {};
let currentFilters = {
    name: '',
    code: '',
    startDate: '',
    endDate: ''
};

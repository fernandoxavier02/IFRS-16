// ============================================================
// FUNÇÕES DE UTILITÁRIOS E UI
// ============================================================

function getMachineId() {
    let machineId = localStorage.getItem('ifrs16_machine_id');
    if (!machineId) {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        ctx.textBaseline = 'top';
        ctx.font = '14px Arial';
        ctx.fillText('fingerprint', 2, 2);
        const fingerprint = canvas.toDataURL();
        const data = fingerprint + navigator.userAgent + screen.width + screen.height + (navigator.language || '') + new Date().getTimezoneOffset();
        let hash = 0;
        for (let i = 0; i < data.length; i++) {
            const char = data.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash;
        }
        machineId = 'IFRS16-' + Math.abs(hash).toString(36).toUpperCase().substring(0, 16);
        localStorage.setItem('ifrs16_machine_id', machineId);
    }
    return machineId;
}

function abrirCompra() { window.open(CONFIG.URL_COMPRA, '_blank'); }

function formatarData(data) { return data.toLocaleDateString('pt-BR'); }
function formatMoney(valor) { return valor.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
function formatPercent(valor, decimals = 2) { return valor.toLocaleString('pt-BR', { minimumFractionDigits: decimals, maximumFractionDigits: decimals }) + '%'; }
function formatDataMes(data) { return data.toLocaleDateString('pt-BR', { month: '2-digit', year: 'numeric' }); }

function mostrarTelaLogin() {
    document.getElementById('loginOverlay').classList.remove('hidden');
    document.getElementById('licenseOverlay').classList.add('hidden');
    document.getElementById('mainContent').classList.add('hidden');
    document.getElementById('settingsModal').classList.add('hidden');
}

function mostrarTelaLicenca() {
    document.getElementById('loginOverlay').classList.add('hidden');
    document.getElementById('licenseOverlay').classList.remove('hidden');
    document.getElementById('mainContent').classList.add('hidden');
    document.getElementById('settingsModal').classList.add('hidden');
}

function mostrarConteudoPrincipal() {
    document.getElementById('loginOverlay').classList.add('hidden');
    document.getElementById('licenseOverlay').classList.add('hidden');
    document.getElementById('mainContent').classList.remove('hidden');
    // Carregar contratos e índices quando o conteúdo principal for mostrado
    setTimeout(() => {
        if (typeof loadContracts === 'function') {
            loadContracts();
        }
        if (typeof loadEconomicIndexes === 'function') {
            loadEconomicIndexes();
        }
    }, 1000);
}

function toggleAjuda() {
    const box = document.getElementById('ajudaBox');
    const btn = document.getElementById('btnAjudaText');
    box.classList.toggle('hidden');
    btn.textContent = box.classList.contains('hidden') ? 'Ajuda' : 'Ocultar';
}

function mudarAba(aba) {
    ['resumo', 'fluxo', 'contabil', 'cplp', 'lancamentos'].forEach(a => {
        document.getElementById('aba-' + a).classList.remove('active');
        document.getElementById('conteudo-' + a).classList.add('hidden');
    });
    document.getElementById('aba-' + aba).classList.add('active');
    document.getElementById('conteudo-' + aba).classList.remove('hidden');
}

function abrirConfiguracoes() {
    // Preencher dados do modal
    const savedUserData = localStorage.getItem('ifrs16_user_data');
    if (savedUserData) {
        const user = JSON.parse(savedUserData);
        document.getElementById('settingsUserName').textContent = user.name || '-';
        document.getElementById('settingsUserEmail').textContent = user.email || '-';
    } else {
        document.getElementById('settingsUserName').textContent = dadosLicenca?.nome || '-';
        document.getElementById('settingsUserEmail').textContent = '-';
    }

    // Dados da licença
    document.getElementById('settingsLicenseKey').textContent = licencaAtiva || '-';
    document.getElementById('settingsLicenseType').textContent = dadosLicenca?.tipo?.toUpperCase() || '-';
    document.getElementById('settingsLicenseStatus').textContent = 'Ativa';
    document.getElementById('settingsLicenseExpiry').textContent = dadosLicenca?.expira
        ? formatarData(new Date(dadosLicenca.expira))
        : 'Sem expiração';

    // Limpar campos de senha
    document.getElementById('currentPassword').value = '';
    document.getElementById('newPassword').value = '';
    document.getElementById('confirmPassword').value = '';
    document.getElementById('passwordError').classList.add('hidden');
    document.getElementById('passwordSuccess').classList.add('hidden');

    // Mostrar modal
    document.getElementById('settingsModal').classList.remove('hidden');
}

function fecharConfiguracoes() {
    document.getElementById('settingsModal').classList.add('hidden');
}

// Inicialização de Event Listeners de UI
document.addEventListener('DOMContentLoaded', () => {
    // Fechar modal ao clicar fora
    document.getElementById('settingsModal').addEventListener('click', function (e) {
        if (e.target === this) fecharConfiguracoes();
    });

    // Enter nos campos de login
    document.getElementById('loginEmail')?.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') document.getElementById('loginPassword').focus();
    });
    document.getElementById('loginPassword')?.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') fazerLogin();
    });
    document.getElementById('licenseInput')?.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') validarLicenca();
    });

    // Cleanup ao fechar
    window.addEventListener('beforeunload', () => { if (checkInterval) clearInterval(checkInterval); });
});

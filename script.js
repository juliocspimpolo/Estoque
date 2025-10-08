// 🚨 SUBSTITUA ESTA URL PELA URL REAL DA SUA API DO APPS SCRIPT! 🚨
const API_URL = "https://script.google.com/macros/s/AKfycbwagG2QAzG7gk2BcZ6Xm8KEGkDunbMN3CD9JJA7iNqgE9cisgRJbTJZstk4T0IzIAjb/exec"; 

// =========================================================================
// VARIÁVEIS DO DOM (Gerais)
// =========================================================================
const loginForm = document.getElementById('login-form');
const loginScreen = document.getElementById('login-screen');
const mainContent = document.getElementById('main-content');
const mensagemErro = document.getElementById('mensagem-erro');
const btnLogin = document.getElementById('btn-login');
const welcomeMessage = document.getElementById('welcome-message');
const logoutButton = document.getElementById('logout-button');

// VARIÁVEIS DO DOM (Estoque)
const stockForm = document.getElementById('stock-form');
const btnMovimentar = document.getElementById('btn-movimentar');
const mensagemEstoque = document.getElementById('mensagem-estoque');

// Variável global para armazenar as informações do usuário logado
let usuarioLogado = null; 

// =========================================================================
// FUNÇÕES DE EXIBIÇÃO
// =========================================================================

function showScreen(isLoggedIn, userName, permissionLevel) {
    if (isLoggedIn) {
        loginScreen.style.display = 'none';
        mainContent.style.display = 'block';
        welcomeMessage.textContent = `Bem-vindo(a), ${userName} (${permissionLevel})`;
    } else {
        loginScreen.style.display = 'flex';
        mainContent.style.display = 'none';
    }
}

// Função utilitária para fazer requisição via IFrame (contorna o CORS)
function sendRequest(data, callback) {
    const urlComParametros = `${API_URL}?data=${encodeURIComponent(JSON.stringify(data))}`;
    
    const iframe = document.createElement('iframe');
    iframe.name = 'apps-script-iframe-' + data.action;
    iframe.style.display = 'none';

    iframe.onload = function() {
        try {
            const resultado = JSON.parse(iframe.contentWindow.document.body.innerText);
            callback(resultado);
        } catch (error) {
            callback({ resultado: 'Erro', mensagem: 'Erro de comunicação. Verifique a autorização do Apps Script.' });
            console.error('Erro ao processar resposta do iframe:', error);
        } finally {
            document.body.removeChild(iframe);
        }
    };

    document.body.appendChild(iframe);
    iframe.src = urlComParametros;
}


// =========================================================================
// LÓGICA DE LOGIN 
// =========================================================================

loginForm.addEventListener('submit', (e) => {
    e.preventDefault(); 
    
    const login = document.getElementById('login-usuario').value;
    const senha = document.getElementById('login-senha').value;
    mensagemErro.textContent = ''; 
    btnLogin.disabled = true;
    btnLogin.textContent = 'Verificando...';

    const dadosParaApi = {
        action: 'login',
        login: login,
        senha: senha
    };

    sendRequest(dadosParaApi, (resultado) => {
        if (resultado.resultado === 'Sucesso') {
            usuarioLogado = resultado.usuario;
            showScreen(true, usuarioLogado.nome, usuarioLogado.permissao);
            mensagemErro.textContent = 'Login realizado!';
            mensagemErro.style.color = 'green';
        } else {
            mensagemErro.textContent = resultado.mensagem || 'Erro desconhecido no login.';
            mensagemErro.style.color = 'red';
        }
        btnLogin.disabled = false;
        btnLogin.textContent = 'Entrar';
    });
});


// =========================================================================
// LÓGICA DE MOVIMENTAÇÃO DE ESTOQUE (ENTRADA/SAÍDA)
// =========================================================================

stockForm.addEventListener('submit', (e) => {
    e.preventDefault();
    
    if (!usuarioLogado) {
        mensagemEstoque.textContent = 'Erro: Faça login novamente.';
        return;
    }
    
    // Coleta dos dados
    const tipo = document.getElementById('movimento-tipo').value;
    const sku = document.getElementById('movimento-sku').value;
    const descricao = document.getElementById('movimento-descricao').value;
    const quantidade = document.getElementById('movimento-quantidade').value;
    const observacoes = document.getElementById('movimento-observacoes').value;
    
    // Prepara os dados
    const dadosParaApi = {
        action: 'addStock', // CHAMA A FUNÇÃO handleAddStock
        tipo: tipo,
        sku: sku,
        descricao: descricao,
        quantidade: quantidade,
        responsavel: usuarioLogado.login,
        observacoes: observacoes
    };
    
    mensagemEstoque.textContent = '';
    btnMovimentar.disabled = true;
    btnMovimentar.textContent = 'Registrando...';

    sendRequest(dadosParaApi, (resultado) => {
        if (resultado.resultado === 'Sucesso') {
            mensagemEstoque.textContent = 'Movimentação registrada com sucesso! (Verifique a planilha)';
            mensagemEstoque.style.color = 'green';
            stockForm.reset(); 
        } else {
            mensagemEstoque.textContent = resultado.mensagem || 'Erro ao registrar. Verifique o Apps Script.';
            mensagemEstoque.style.color = 'red';
        }
        btnMovimentar.disabled = false;
        btnMovimentar.textContent = 'Registrar Movimentação';
    });
});


// =========================================================================
// LÓGICA DE LOGOUT E INICIALIZAÇÃO
// =========================================================================

logoutButton.addEventListener('click', () => {
    usuarioLogado = null; 
    showScreen(false); 
    loginForm.reset(); 
    mensagemErro.textContent = '';
    mensagemErro.style.color = 'red';
});

document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => showScreen(false), 50); 
});

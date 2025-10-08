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

// Função para mostrar ou esconder as telas
function showScreen(isLoggedIn, userName, permissionLevel) {
    if (isLoggedIn) {
        loginScreen.style.display = 'none';
        mainContent.style.display = 'block';
        welcomeMessage.textContent = `Bem-vindo(a), ${userName} (${permissionLevel})`;
        
        // FUTURE: Aqui você faria a lógica de permissões visuais
        // if (permissionLevel === 'VIEW') { stockForm.style.display = 'none'; }
        
    } else {
        loginScreen.style.display = 'flex'; // Usamos flex para centralizar
        mainContent.style.display = 'none';
    }
}


// =========================================================================
// LÓGICA DE LOGIN (Via IFrame/GET para evitar CORS)
// =========================================================================

loginForm.addEventListener('submit', (e) => {
    e.preventDefault(); 
    
    // 1. Coleta e limpa
    const login = document.getElementById('login-usuario').value;
    const senha = document.getElementById('login-senha').value;
    mensagemErro.textContent = ''; 
    btnLogin.disabled = true;
    btnLogin.textContent = 'Verificando...';

    // 2. Prepara os dados
    const dadosParaApi = {
        action: 'login',
        login: login,
        senha: senha
    };

    // 3. Monta URL com dados serializados
    const urlComParametros = `${API_URL}?data=${encodeURIComponent(JSON.stringify(dadosParaApi))}`;
    
    // 4. Cria e anexa o IFrame
    const iframe = document.createElement('iframe');
    iframe.name = 'apps-script-iframe';
    iframe.style.display = 'none';

    // 5. Listener de resposta
    iframe.onload = function() {
        try {
            // A API retorna o JSON como texto puro no corpo do IFrame
            const resultado = JSON.parse(iframe.contentWindow.document.body.innerText);

            if (resultado.resultado === 'Sucesso') {
                usuarioLogado = resultado.usuario;
                
                showScreen(true, usuarioLogado.nome, usuarioLogado.permissao);
                mensagemErro.textContent = 'Login realizado!';
                mensagemErro.style.color = 'green';
            } else {
                mensagemErro.textContent = resultado.mensagem || 'Erro desconhecido no login.';
                mensagemErro.style.color = 'red';
            }
        } catch (error) {
             mensagemErro.textContent = 'Erro de comunicação. Verifique a autorização do Apps Script.';
             console.error('Erro ao processar resposta do iframe:', error);
        } finally {
            document.body.removeChild(iframe);
            btnLogin.disabled = false;
            btnLogin.textContent = 'Entrar';
        }
    };

    document.body.appendChild(iframe);
    iframe.src = urlComParametros; 
});


// =========================================================================
// LÓGICA DE MOVIMENTAÇÃO DE ESTOQUE (ENTRADA/SAÍDA)
// =========================================================================

stockForm.addEventListener('submit', (e) => {
    e.preventDefault();
    
    // Validação de usuário
    if (!usuarioLogado) {
        mensagemEstoque.textContent = 'Erro: Faça login novamente.';
        return;
    }
    
    // 1. Coleta os dados do formulário de estoque
    const tipo = document.getElementById('movimento-tipo').value;
    const sku = document.getElementById('movimento-sku').value;
    const descricao = document.getElementById('movimento-descricao').value;
    const quantidade = document.getElementById('movimento-quantidade').value;
    const observacoes = document.getElementById('movimento-observacoes').value;
    
    // 2. Prepara os dados para o Apps Script (com a action: 'addStock')
    const dadosParaApi = {
        action: 'addStock', // CHAMA A FUNÇÃO handleAddStock
        tipo: tipo,
        sku: sku,
        descricao: descricao,
        quantidade: quantidade,
        responsavel: usuarioLogado.login, // Pega o login do usuário logado
        observacoes: observacoes
    };
    
    // Reseta o estado do botão
    mensagemEstoque.textContent = '';
    btnMovimentar.disabled = true;
    btnMovimentar.textContent = 'Registrando...';

    // 3. Monta a URL (IFrame/GET)
    const urlComParametros = `${API_URL}?data=${encodeURIComponent(JSON.stringify(dadosParaApi))}`;
    
    const iframe = document.createElement('iframe');
    iframe.name = 'apps-script-stock-iframe';
    iframe.style.display = 'none';

    // 4. Listener de resposta
    iframe.onload = function() {
        try {
            const resultado = JSON.parse(iframe.contentWindow.document.body.innerText);

            if (resultado.resultado === 'Sucesso') {
                mensagemEstoque.textContent = 'Movimentação registrada com sucesso! (Verifique a planilha)';
                mensagemEstoque.style.color = 'green';
                stockForm.reset(); // Limpa o formulário
            } else {
                mensagemEstoque.textContent = resultado.mensagem || 'Erro ao registrar. Verifique o log de Execuções do Apps Script.';
                mensagemEstoque.style.color = 'red';
            }
        } catch (error) {
             mensagemEstoque.textContent = 'Erro de comunicação no retorno. Tente novamente.';
             console.error('Erro ao processar resposta do iframe (Estoque):', error);
        } finally {
            document.body.removeChild(iframe);
            btnMovimentar.disabled = false;
            btnMovimentar.textContent = 'Registrar Movimentação';
        }
    };

    document.body.appendChild(iframe);
    iframe.src = urlComParametros;
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

// Ao carregar a página, garante que a tela de login está visível
document.addEventListener('DOMContentLoaded', () => {
    // Isso é importante para que o IFrame do login não bloqueie o carregamento
    setTimeout(() => showScreen(false), 50); 
});

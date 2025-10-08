// 🚨 SUBSTITUA ESTA URL PELA URL REAL DA SUA API DO APPS SCRIPT! 🚨
const API_URL = "https://script.google.com/macros/s/AKfycbwagG2QAzG7gk2BcZ6Xm8KEGkDunbMN3CD9JJA7iNqgE9cisgRJbTJZstk4T0IzIAjb/exec"; 

// =========================================================================
// VARIÁVEIS DO DOM
// =========================================================================
const loginForm = document.getElementById('login-form');
const loginScreen = document.getElementById('login-screen');
const mainContent = document.getElementById('main-content');
const mensagemErro = document.getElementById('mensagem-erro');
const btnLogin = document.getElementById('btn-login');
const welcomeMessage = document.getElementById('welcome-message');
const logoutButton = document.getElementById('logout-button');

// Variável global para armazenar as informações do usuário logado
let usuarioLogado = null; 

// =========================================================================
// FUNÇÕES DE EXIBIÇÃO
// =========================================================================

// Função para mostrar ou esconder as telas
function showScreen(isLoggedIn, userName, permissionLevel) {
    if (isLoggedIn) {
        // Mostra o conteúdo principal e esconde o login
        loginScreen.style.display = 'none';
        mainContent.style.display = 'block';
        welcomeMessage.textContent = `Bem-vindo(a), ${userName} (${permissionLevel})`;
        
        // FUTURE: Aqui você faria a lógica para desabilitar botões se for VIEW-ONLY
        // if (permissionLevel === 'VIEW') { /* desabilita formulários */ }
        
    } else {
        // Mostra o login e esconde o conteúdo principal
        loginScreen.style.display = 'flex'; // Usamos flex para centralizar
        mainContent.style.display = 'none';
    }
}


// =========================================================================
// LÓGICA DE LOGIN (SUBMISSÃO DO FORMULÁRIO) - NOVA ABORDAGEM SEM FETCH/CORS
// =========================================================================

loginForm.addEventListener('submit', (e) => {
    e.preventDefault(); // Impede o envio tradicional do formulário
    
    // 1. Coleta os dados do formulário
    const login = document.getElementById('login-usuario').value;
    const senha = document.getElementById('login-senha').value;
    
    // Limpa a mensagem de erro anterior
    mensagemErro.textContent = ''; 
    btnLogin.disabled = true;
    btnLogin.textContent = 'Verificando...';

    // 2. Monta o objeto de dados a ser enviado
    const dadosParaApi = {
        action: 'login',
        login: login,
        senha: senha
    };

    // 3. Serializa os dados e constrói o URL de requisição
    // O Apps Script precisa que a requisição seja feita via GET para usar essa abordagem
    const urlComParametros = `${API_URL}?data=${encodeURIComponent(JSON.stringify(dadosParaApi))}`;
    
    // 4. Cria um IFrame temporário para fazer a requisição sem problemas de CORS
    const iframe = document.createElement('iframe');
    iframe.name = 'apps-script-iframe';
    iframe.style.display = 'none';

    // 5. Adiciona um listener para quando a resposta da API (via Apps Script) retornar
    iframe.onload = function() {
        try {
            // A API vai escrever o resultado em uma variável global temporária no Apps Script.
            // Aqui, o JS do nosso frontend vai ler essa variável.
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
             mensagemErro.textContent = 'Erro de comunicação no retorno. Verifique o console.';
             console.error('Erro ao processar resposta do iframe:', error);
        } finally {
            // Limpa o IFrame e restaura o botão
            document.body.removeChild(iframe);
            btnLogin.disabled = false;
            btnLogin.textContent = 'Entrar';
        }
    };

    document.body.appendChild(iframe);
    
    // 6. Faz a requisição como GET (dentro do IFrame)
    iframe.src = urlComParametros; 
});


// =========================================================================
// LÓGICA DE LOGOUT
// =========================================================================

logoutButton.addEventListener('click', () => {
    usuarioLogado = null; // Limpa as informações do usuário
    showScreen(false); // Volta para a tela de login
    // Limpar os campos do formulário para segurança
    loginForm.reset(); 
    mensagemErro.textContent = '';
    mensagemErro.style.color = 'red';
});

// Ao carregar a página, garante que a tela de login está visível
document.addEventListener('DOMContentLoaded', () => {
    showScreen(false);
});

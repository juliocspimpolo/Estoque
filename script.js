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
// LÓGICA DE LOGIN (SUBMISSÃO DO FORMULÁRIO)
// =========================================================================

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault(); // Impede o envio tradicional do formulário
    
    // 1. Coleta os dados do formulário
    const login = document.getElementById('login-usuario').value;
    const senha = document.getElementById('login-senha').value;
    
    // Limpa a mensagem de erro anterior
    mensagemErro.textContent = ''; 
    btnLogin.disabled = true;
    btnLogin.textContent = 'Verificando...';

    // 2. Monta o objeto de dados para o Apps Script
    const dadosParaApi = {
        action: 'login', // Diz ao Apps Script para rodar a função handleLogin
        login: login,
        senha: senha
    };

    try {
        // 3. Envia a requisição POST para a API do Apps Script
        const response = await fetch(API_URL, {
            method: 'POST',
            mode: 'cors',
            cache: 'no-cache',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dadosParaApi)
        });

        const resultado = await response.json();

        // 4. Trata a resposta da API
        if (resultado.resultado === 'Sucesso') {
            usuarioLogado = resultado.usuario; // Armazena o objeto do usuário
            
            // Redireciona para a tela principal
            showScreen(
                true, 
                usuarioLogado.nome, 
                usuarioLogado.permissao
            );
            
            mensagemErro.textContent = 'Login realizado!';
            mensagemErro.style.color = 'green';

        } else {
            // Se o login falhar
            mensagemErro.textContent = resultado.mensagem || 'Erro desconhecido no login.';
            mensagemErro.style.color = 'red';
        }
        
    } catch (error) {
        mensagemErro.textContent = 'Erro de conexão com o servidor. Tente novamente.';
        console.error('Erro na requisição:', error);
    } finally {
        // Restaura o botão após a tentativa
        btnLogin.disabled = false;
        btnLogin.textContent = 'Entrar';
    }
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
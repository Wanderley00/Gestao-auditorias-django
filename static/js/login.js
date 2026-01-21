document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('loginForm');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const passwordToggle = document.getElementById('passwordToggle');
    const loginButton = document.getElementById('loginButton');

    // Sai da função se o formulário não for encontrado, evitando erros.
    if (!form) return;

    // --- 1. Lógica para os Labels Flutuantes ---
    function checkValue(input) {
        if (input.value.trim() !== '') {
            input.classList.add('has-value');
        } else {
            input.classList.remove('has-value');
        }
    }

    [usernameInput, passwordInput].forEach(input => {
        if (input) {
            // Verifica o valor inicial (caso o navegador preencha automaticamente)
            checkValue(input);
            
            // Adiciona os "ouvintes" de eventos
            input.addEventListener('input', () => checkValue(input));
            input.addEventListener('blur', () => checkValue(input));
        }
    });

    // --- 2. Lógica para Mostrar/Ocultar Senha (O Ponto Principal da Correção) ---
    if (passwordToggle && passwordInput) {
        passwordToggle.addEventListener('click', () => {
            const isPassword = passwordInput.type === 'password';
            passwordInput.type = isPassword ? 'text' : 'password';

            const eyeIcon = passwordToggle.querySelector('.eye-icon');
            if (isPassword) {
                // Se a senha estava oculta, agora será mostrada. Usamos o ícone de "olho cortado".
                eyeIcon.innerHTML = `
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                    <line x1="1" y1="1" x2="23" y2="23"/>
                `;
            } else {
                // Se a senha estava visível, agora será ocultada. Usamos o ícone de "olho normal".
                eyeIcon.innerHTML = `
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                    <circle cx="12" cy="12" r="3"/>
                `;
            }
        });
    }

    // --- 3. Lógica do Botão de Login (efeito "loading") ---
    form.addEventListener('submit', function(e) {
        if (loginButton) {
            // Validação simples para não ativar o loading se os campos estiverem vazios
            if (usernameInput.value.trim() === '' || passwordInput.value.trim() === '') {
                return;
            }
            loginButton.classList.add('loading');
            loginButton.disabled = true;
        }
    });

});
class ModernLoginForm {
    constructor() {
        this.form = document.getElementById('loginForm');
        this.passwordToggle = document.getElementById('passwordToggle');
        this.loginButton = document.getElementById('loginButton');
        this.messagesContainer = document.getElementById('messagesContainer');
        
        this.init();
    }
    
    init() {
        this.setupFloatingLabels();
        this.setupPasswordToggle();
        this.setupFormSubmission();
        this.initializeExistingValues();
        this.setupFormAnimations();
        this.initializeAutoHideMessages();
        this.setupClientSideValidation();
    }
    
    initializeExistingValues() {
        const inputs = this.form.querySelectorAll('input[type="text"], input[type="password"]');
        inputs.forEach(input => {
            if (input.value.trim() !== '') {
                input.classList.add('has-value');
            }
        });
    }
    
    setupFloatingLabels() {
        const inputs = this.form.querySelectorAll('input[type="text"], input[type="password"]');
        
        inputs.forEach(input => {
            input.addEventListener('input', () => {
                if (input.value.trim() !== '') {
                    input.classList.add('has-value');
                } else {
                    input.classList.remove('has-value');
                }
            });
            
            input.addEventListener('blur', () => {
                if (input.value.trim() !== '') {
                    input.classList.add('has-value');
                } else {
                    input.classList.remove('has-value');
                }
            });

            input.addEventListener('focus', () => {
                input.parentElement.style.transform = 'scale(1.02)';
            });

            input.addEventListener('blur', () => {
                input.parentElement.style.transform = 'scale(1)';
            });
        });
    }
    
    setupPasswordToggle() {
        if (this.passwordToggle) {
            const passwordInput = this.form.querySelector('input[type="password"]');
            
            this.passwordToggle.addEventListener('click', () => {
                const type = passwordInput.type === 'password' ? 'text' : 'password';
                passwordInput.type = type;
                
                const eyeIcon = this.passwordToggle.querySelector('.eye-icon');
                if (type === 'text') {
                    eyeIcon.innerHTML = `
                        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                        <line x1="1" y1="1" x2="23" y2="23"/>
                    `;
                } else {
                    eyeIcon.innerHTML = `
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                        <circle cx="12" cy="12" r="3"/>
                    `;
                }
            });
        }
    }
    
    setupFormSubmission() {
        this.form.addEventListener('submit', (e) => {
            // Validação básica do lado cliente
            const username = this.form.querySelector('#username').value.trim();
            const password = this.form.querySelector('#password').value;
            
            if (!username || !password) {
                e.preventDefault();
                this.showMessage('error', 'Campos Obrigatórios', 'Por favor, preencha todos os campos.');
                return;
            }
            
            this.loginButton.classList.add('loading');
            this.loginButton.disabled = true;
            
            // Se houver erro de validação no servidor, o formulário será recarregado
            // e as mensagens de erro do Django aparecerão
        });
    }

    setupFormAnimations() {
        const formElements = this.form.querySelectorAll('.form-group, .login-btn');
        formElements.forEach((element, index) => {
            element.style.opacity = '0';
            element.style.transform = 'translateY(20px)';
            element.style.animation = `fadeInUp 0.6s ease-out ${index * 0.1}s forwards`;
        });
    }
    
    setupClientSideValidation() {
        const inputs = this.form.querySelectorAll('input[required]');
        
        inputs.forEach(input => {
            input.addEventListener('blur', () => {
                this.validateField(input);
            });
            
            input.addEventListener('input', () => {
                if (input.classList.contains('error')) {
                    this.validateField(input);
                }
            });
        });
    }
    
    validateField(input) {
        const fieldGroup = input.closest('.form-group');
        const existingError = fieldGroup.querySelector('.field-error');
        
        // Remove erro existente
        if (existingError) {
            existingError.remove();
        }
        
        input.classList.remove('error');
        
        // Validação
        if (!input.value.trim()) {
            this.showFieldError(input, `${input.previousElementSibling.textContent} é obrigatório`);
        } else if (input.type === 'email' && !this.isValidEmail(input.value)) {
            this.showFieldError(input, 'Digite um email válido');
        }
    }
    
    showFieldError(input, message) {
        input.classList.add('error');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error';
        errorDiv.textContent = message;
        
        input.parentElement.parentElement.appendChild(errorDiv);
    }
    
    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    initializeAutoHideMessages() {
        // Configurar auto-hide para mensagens existentes
        const existingMessages = document.querySelectorAll('.message[data-auto-hide]');
        existingMessages.forEach(message => {
            const timeout = parseInt(message.dataset.autoHide) || 5000;
            this.setupAutoHide(message, timeout);
        });
    }
    
    setupAutoHide(messageElement, timeout = 5000) {
        // Adicionar classe para animação da barra de progresso
        setTimeout(() => {
            messageElement.classList.add('auto-hide');
        }, 100);
        
        // Esconder a mensagem após o timeout
        setTimeout(() => {
            this.hideMessage(messageElement);
        }, timeout);
    }
    
    showMessage(type, title, text, autoHide = true) {
        const icons = {
            error: `<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2zm-1 15h2v-2h-2v2zm0-4h2V7h-2v6z"/>
                    </svg>`,
            success: `<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2zm-1.5 13L7 11.5l1.5-1.5L10 11.5 15.5 6 17 7.5 10.5 15z"/>
                      </svg>`,
            warning: `<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2L2 22h20L12 2zm-1 15h2v2h-2v-2zm0-6h2v4h-2v-4z"/>
                      </svg>`
        };
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message message-${type}`;
        
        messageDiv.innerHTML = `
            <div class="message-icon">
                ${icons[type] || icons.error}
            </div>
            <div class="message-content">
                <div class="message-title">${title}</div>
                <div class="message-text">${text}</div>
            </div>
            <button type="button" class="message-close" onclick="window.loginForm.closeMessage(this)">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M18 6L6 18M6 6l12 12"/>
                </svg>
            </button>
        `;
        
        const dynamicMessages = document.getElementById('dynamicMessages');
        dynamicMessages.appendChild(messageDiv);
        
        if (autoHide) {
            this.setupAutoHide(messageDiv, 5000);
        }
        
        return messageDiv;
    }
    
    hideMessage(messageElement) {
        messageElement.classList.add('hiding');
        setTimeout(() => {
            if (messageElement.parentNode) {
                messageElement.parentNode.removeChild(messageElement);
            }
        }, 300);
    }
    
    closeMessage(closeButton) {
        const message = closeButton.closest('.message');
        this.hideMessage(message);
    }
}

// Função global para fechar mensagem (chamada pelo onclick no HTML)
window.closeMessage = function(closeButton) {
    if (window.loginForm) {
        window.loginForm.closeMessage(closeButton);
    }
};

// Add CSS for animations and error states
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeInUp {
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        75% { transform: translateX(5px); }
    }

    .input-wrapper {
        transition: transform 0.2s ease;
    }
    
    .input-wrapper input.error {
        border-color: var(--error) !important;
        box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.1) !important;
    }
    
    .input-wrapper input.error + label {
        color: var(--error) !important;
    }
`;
document.head.appendChild(style);

document.addEventListener('DOMContentLoaded', () => {
    window.loginForm = new ModernLoginForm();
});

function closeToast(closeButton) {
    const toast = closeButton.closest('.toast');
    hideToast(toast);
}

function hideToast(toastElement) {
    toastElement.classList.add('hiding');
    setTimeout(() => {
        if (toastElement.parentNode) {
            toastElement.parentNode.removeChild(toastElement);
        }
    }, 400);
}

function showToast(type, title, message, autoHide = true, duration = 6000) {
    const icons = {
        error: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                  <line x1="12" y1="9" x2="12" y2="13"/>
                  <line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>`,
        success: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2zm-1.5 13L7 11.5l1.5-1.5L10 11.5 15.5 6 17 7.5 10.5 15z"/>
                  </svg>`,
        warning: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 2L2 22h20L12 2zm-1 15h2v2h-2v-2zm0-6h2v4h-2v-4z"/>
                  </svg>`
    };
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    toast.innerHTML = `
        <div class="toast-icon">
            ${icons[type] || icons.error}
        </div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button type="button" class="toast-close" onclick="closeToast(this)" aria-label="Fechar">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
        </button>
        <div class="toast-progress">
            <div class="progress-bar" style="animation-duration: ${duration}ms;"></div>
        </div>
    `;
    
    const container = document.getElementById('dynamicToasts') || document.getElementById('toastContainer');
    container.appendChild(toast);
    
    if (autoHide) {
        setTimeout(() => {
            hideToast(toast);
        }, duration);
    }
    
    return toast;
}

// Atualizar a função setupFormSubmission para usar toasts
function setupFormSubmission() {
    this.form.addEventListener('submit', (e) => {
        const username = this.form.querySelector('#username').value.trim();
        const password = this.form.querySelector('#password').value;
        
        if (!username || !password) {
            e.preventDefault();
            showToast('error', 'Campos Obrigatórios', 'Por favor, preencha todos os campos.');
            return;
        }
        
        this.loginButton.classList.add('loading');
        this.loginButton.disabled = true;
    });
}

// Inicializar auto-hide para toasts existentes
document.addEventListener('DOMContentLoaded', function() {
    const existingToasts = document.querySelectorAll('.toast[data-auto-hide]');
    existingToasts.forEach(toast => {
        const duration = parseInt(toast.dataset.autoHide) || 6000;
        setTimeout(() => {
            hideToast(toast);
        }, duration);
    });
    
    // Inicializar o formulário de login
    window.loginForm = new ModernLoginForm();
});
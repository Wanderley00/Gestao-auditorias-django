class ModernLoginForm {
    constructor() {
        this.form = document.getElementById('loginForm');
        this.passwordToggle = document.getElementById('passwordToggle');
        this.loginButton = document.getElementById('loginButton');
        
        this.init();
    }
    
    init() {
        this.setupFloatingLabels();
        this.setupPasswordToggle();
        this.setupFormSubmission();
        this.initializeExistingValues();
        this.setupFormAnimations();
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

            // Add focus animations
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
            this.loginButton.classList.add('loading');
            this.loginButton.disabled = true;
            
            // Add subtle shake animation if form validation fails
            setTimeout(() => {
                if (!this.form.checkValidity()) {
                    this.form.style.animation = 'shake 0.5s ease-in-out';
                    setTimeout(() => {
                        this.form.style.animation = '';
                    }, 500);
                }
            }, 100);
        });
    }

    setupFormAnimations() {
        // Stagger animation for form elements
        const formElements = this.form.querySelectorAll('.form-group, .login-btn');
        formElements.forEach((element, index) => {
            element.style.opacity = '0';
            element.style.transform = 'translateY(20px)';
            element.style.animation = `fadeInUp 0.6s ease-out ${index * 0.1}s forwards`;
        });
    }
}

// Add CSS for animations
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
`;
document.head.appendChild(style);

document.addEventListener('DOMContentLoaded', () => {
    new ModernLoginForm();
});
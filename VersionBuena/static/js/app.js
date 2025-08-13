document.addEventListener('DOMContentLoaded', () => {
    const signInForm = document.getElementById("login-form");
    const loginMessage = document.getElementById('login-message');
    const BACKEND_URL = 'http://127.0.0.1:5000';

    signInForm.addEventListener('submit', (event) => {
        event.preventDefault();

        const username = document.getElementById('signin-username').value;
        const password = document.getElementById('signin-password').value;
        loginMessage.textContent = '';

        fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password }),
            credentials: 'include'
        })
        .then(response => {
            if (!response.ok) return response.json().then(err => { throw err });
            return response.json();
        })
        .then(data => {
            if (data.redirect_url) {
                window.location.href = data.redirect_url;
            } else {
                loginMessage.textContent = data.message || 'Error desconocido.';
            }
        })
        .catch(error => {
            loginMessage.textContent = error.message || 'No se pudo conectar con el servidor.';
        });

        });
});

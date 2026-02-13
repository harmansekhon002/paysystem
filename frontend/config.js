// API Configuration
window.API_URL = 'https://paysystem-erxo.onrender.com/api';

// Local storage keys
const AUTH_TOKEN_KEY = 'payroll_auth_token';
const USER_KEY = 'payroll_user';

// Get stored token
function getAuthToken() {
    return localStorage.getItem(AUTH_TOKEN_KEY);
}

// Set token
function setAuthToken(token) {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
}

// Get stored user
function getStoredUser() {
    const user = localStorage.getItem(USER_KEY);
    return user ? JSON.parse(user) : null;
}

// Set user
function setStoredUser(user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
}

// Clear auth
function clearAuth() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
}

// Check if logged in
function isLoggedIn() {
    return !!getAuthToken();
}


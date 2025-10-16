/**
 * Authentication utilities
 */

// Check if user is logged in
function isAuthenticated() {
    return !!localStorage.getItem('token');
}

// Get current token
function getToken() {
    return localStorage.getItem('token');
}

// Get current username
function getUsername() {
    return localStorage.getItem('username');
}

// Logout
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    localStorage.removeItem('isAdmin');
    window.location.href = '/login';
}

// Check authentication on protected pages
async function checkAuth() {
    if (!isAuthenticated()) {
        window.location.href = '/login';
        return false;
    }
    
    // Verify token is still valid
    try {
        const response = await fetch('/api/users/me', {
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });
        
        if (!response.ok) {
            logout();
            return false;
        }
        
        const user = await response.json();
        localStorage.setItem('isAdmin', user.is_admin);
        
        // Update UI
        updateAuthUI(user);
        
        return true;
    } catch (error) {
        console.error('Auth check failed:', error);
        logout();
        return false;
    }
}

// Update UI based on authentication state
function updateAuthUI(user) {
    const navbar = document.getElementById('navbar');
    if (navbar) {
        navbar.style.display = 'block';
    }
    
    const usernameDisplay = document.getElementById('username-display');
    if (usernameDisplay) {
        usernameDisplay.textContent = user.username;
    }
    
    // Hide admin-only elements for non-admin users
    if (!user.is_admin) {
        document.querySelectorAll('.admin-only').forEach(el => {
            el.style.display = 'none';
        });
    }
}

// Initialize auth check on page load for protected pages
document.addEventListener('DOMContentLoaded', () => {
    const publicPages = ['/login', '/'];
    const currentPath = window.location.pathname;
    
    if (!publicPages.includes(currentPath)) {
        checkAuth();
    }
});


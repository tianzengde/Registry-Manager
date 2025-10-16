/**
 * API request utilities
 */

// Base API request function
async function apiRequest(url, options = {}) {
    const token = localStorage.getItem('token');
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` })
        }
    };
    
    const mergedOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    };
    
    try {
        const response = await fetch(url, mergedOptions);
        
        // Handle 401 Unauthorized
        if (response.status === 401) {
            logout();
            throw new Error('Unauthorized');
        }
        
        // Handle 403 Forbidden
        if (response.status === 403) {
            throw new Error('Forbidden: You don\'t have permission');
        }
        
        // Handle 404 Not Found
        if (response.status === 404) {
            throw new Error('Not found');
        }
        
        // Handle 204 No Content
        if (response.status === 204) {
            return null;
        }
        
        // Parse JSON response
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Request failed');
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// Convenience methods
const api = {
    get: (url) => apiRequest(url),
    
    post: (url, data) => apiRequest(url, {
        method: 'POST',
        body: JSON.stringify(data)
    }),
    
    put: (url, data) => apiRequest(url, {
        method: 'PUT',
        body: JSON.stringify(data)
    }),
    
    delete: (url) => apiRequest(url, {
        method: 'DELETE'
    })
};

// Export for use in other scripts
window.apiRequest = apiRequest;
window.api = api;


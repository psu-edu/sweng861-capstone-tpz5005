// Uses Vite environment variable, falling back to localhost
const BASE_URL = 'https://localhost:8000';

/**
 * Centralized API client wrapper around fetch
 */
/***********************************************/
export async function apiClient(endpoint, options = {}) {
/***********************************************/
    const customToken = localStorage.getItem('token');

    const config = {
        ...options,
        credentials: 'include', // Cookie credentials
        headers: {
            'Content-Type': 'application/json',
            ...(customToken ? { 'Authorization': `Bearer ${customToken}` } : {}),
            ...options.headers,
        },
    };

    // Centralized fetch
    const response = await fetch(`${BASE_URL}${endpoint}`, config);

    // Centralized Error handling
    // If its a 401 or 403
    if (response.status === 401 || response.status === 403) {
        // Dispatch event to clear auth state & notify App.js
        window.dispatchEvent(new CustomEvent('auth:unauthorized', { 
            detail: { status: response.status } 
        }));

        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Session expired or unauthorized.');
    }

    // If its something unexpected
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return response.json();
}
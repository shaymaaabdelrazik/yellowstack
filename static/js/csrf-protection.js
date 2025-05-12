// csrf-protection.js
// File for CSRF protection of AJAX requests

// Function to get CSRF token from meta tag or any element with id/name csrf_token
function getCsrfToken() {
    // Try to get from meta tag
    let token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    
    // If not in meta, try from hidden field
    if (!token) {
        token = document.querySelector('input[name="csrf_token"]')?.value;
    }
    
    // If not there either, try to find by ID
    if (!token) {
        token = document.getElementById('csrf_token')?.value;
    }
    
    return token;
}

// Setting up interceptor for all fetch requests
const originalFetch = window.fetch;
window.fetch = function(url, options = {}) {
    // If this is a POST, PUT, DELETE or PATCH request and X-CSRFToken header is not specified
    if (options.method && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(options.method.toUpperCase()) &&
        (!options.headers || !options.headers['X-CSRFToken'])) {
        
        const token = getCsrfToken();
        if (token) {
            // Create headers if they don't exist
            if (!options.headers) {
                options.headers = {};
            }
            
            // Add CSRF token to headers
            options.headers['X-CSRFToken'] = token;
        }
    }
    
    // Call original fetch with our settings
    return originalFetch(url, options);
};

// Adding CSRF token to XMLHttpRequest (for compatibility)
const originalXhrOpen = XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open = function(method, url) {
    const token = getCsrfToken();
    
    // Call original open first
    originalXhrOpen.apply(this, arguments);
    
    // Set handler to add CSRF token header before sending
    if (token && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(method.toUpperCase())) {
        // Use a more reliable way to add header
        const originalSend = this.send;
        this.send = function(data) {
            if (this.readyState === 1) { // OPENED
                try {
                    this.setRequestHeader('X-CSRFToken', token);
                } catch (e) {
                    console.warn('Could not set CSRF token for XHR: ', e);
                }
            }
            originalSend.apply(this, arguments);
        };
    }
};

// Adding CSRF token to forms
document.addEventListener('DOMContentLoaded', function() {
    // Get CSRF token
    const token = getCsrfToken();
    
    // If token exists, go through all forms and add it
    if (token) {
        document.querySelectorAll('form').forEach(form => {
            // If the form is submitted by POST method and does not contain a CSRF token
            if (form.method === 'post' && !form.querySelector('input[name="csrf_token"]')) {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'csrf_token';
                input.value = token;
                form.appendChild(input);
            }
        });
    }
    
    console.log('CSRF protection initialized');
});
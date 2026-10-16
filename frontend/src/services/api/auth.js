import { apiClient } from './client';

export const authService = {
    async signup(email, password) {
        // Email validation 
        if (!email || !email.includes('@')) {
            throw new Error('Введите корректный email');
        }
        
        // Generate a username from an email (everything before the @)
        const username = email.split('@')[0];
        
        // Additionally some change the username
        const sanitizedUsername = username
            .toLowerCase()                    // to avoid confusion with the register
            .replace(/[^a-z0-9_]/g, '_');     // replace everything except letters, numbers and _ with _
        
        // Send request (httpOnly cookies are set by the server)
        const response = await apiClient.post('/auth/signup', {
            email,
            username: sanitizedUsername,
            password
        });
        
        return response.data;
    },

    async signin(email, password) {
        const response = await apiClient.post('/auth/signin', { email, password });
        return response.data; 
    },

    // Refresh access token using the httpOnly refresh cookie
    async refresh() {
        const response = await apiClient.post('/auth/refresh');
        return response.data;
    },

    // Get the current authenticated user
    async me() {
        const response = await apiClient.get('/users/me');
        return response.data;
    },

    async logout() {
        await apiClient.post('/auth/logout');
    }
};

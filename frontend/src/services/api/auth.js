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
        
        // Send request
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

    async refresh(refreshToken) {
        const response = await apiClient.post('/auth/refresh', { refresh_token: refreshToken });
        return response.data; 
    },

    async logout() {
        await apiClient.post('/auth/logout');
    }
};

import { apiClient } from './client';

export const chatService = {
    // All chats of the current user
    async getMyChats() {
        const response = await apiClient.get('/chats/me');
        return response.data;
    },

    // Single chat
    async getChat(chatId) {
        const response = await apiClient.get(`/chats/${chatId}`);
        return response.data;
    },

    async createChat(data = {}) {
        const response = await apiClient.post('/chats/', data);
        return response.data;
    },

    // Toggle pinned state
    async pinChat(chatId) {
        const response = await apiClient.patch(`/chats/${chatId}/pin`);
        return response.data;
    },

    // Rename the chat (title)
    async renameChat(chatId, title) {
        const response = await apiClient.patch(`/chats/${chatId}/title`, { title });
        return response.data;
    },

    async deleteChat(chatId) {
        const response = await apiClient.delete(`/chats/${chatId}`);
        return response.data;
    },
};
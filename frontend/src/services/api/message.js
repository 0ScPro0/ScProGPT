import { apiClient } from './client';

export const messageService = {
    // History of messages in a chat
    async getChatMessages(chatId) {
        const response = await apiClient.get(`/chats/${chatId}/messages/`);
        return response.data;
    },
};
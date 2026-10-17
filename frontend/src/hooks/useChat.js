import { useState, useCallback, useRef } from 'react';
import { chatService } from '../services/api/chat';
import { messageService } from '../services/api/message';
import { useAuthStore } from '../stores/authStore';

/**
 * Chat state and sending logic (streaming SSE generation).
 *
 * - A chat is created lazily: the "New Chat" action only enters the
 *   new-chat mode (chatId = null); the backend chat is created when the
 *   user sends the first message.
 * - Sending a message: optimistic user bubble -> typing/streaming
 *   assistant bubble -> final message from the stream completion event.
 */
export const useChat = ({ chatId = null, onChatCreated = null } = {}) => {
    const [messages, setMessages] = useState([]);
    const [inputText, setInputText] = useState('');
    const [isAssistantTyping, setIsAssistantTyping] = useState(false);

    // Keep the latest chatId available inside the async send callback
    const chatIdRef = useRef(chatId);
    chatIdRef.current = chatId;

    // Streaming accumulator state
    const streamMessageIdRef = useRef(null);
    const streamTextRef = useRef('');
    const uidRef = useRef(0);

    const sendMessage = useCallback(async () => {
        const text = inputText.trim();
        if (!text || isAssistantTyping) return;

        setInputText('');
        setIsAssistantTyping(true);
        streamMessageIdRef.current = null;
        streamTextRef.current = '';

        let targetChatId = chatIdRef.current;
        let createdChat = null;

        try {
            // Lazily create the chat on the first message
            if (targetChatId == null) {
                const user = useAuthStore.getState().user;
                if (!user) return;

                const chat = await chatService.createChat({
                    user_id: user.id,
                    title: 'New chat',
                });
                targetChatId = chat.id;
                createdChat = chat;
            }

            // Optimistic user message + typing indicator
            setMessages((prev) => [
                ...prev,
                { id: `local-user-${Date.now()}`, role: 'user', text },
                {
                    id: `local-typing-${Date.now()}`,
                    role: 'assistant',
                    text: '• • •',
                    isTypingIndicator: true,
                },
            ]);

            // Stream the AI answer token by token
            await messageService.createAssistantMessageStream(
                targetChatId,
                { prompt: text },
                {
                    onChunk: (chunk) => {
                        streamTextRef.current += chunk;

                        // Create the streaming bubble once, outside the updater
                        let streamId = streamMessageIdRef.current;
                        if (!streamId) {
                            uidRef.current += 1;
                            streamId = `local-ai-${Date.now()}-${uidRef.current}`;
                            streamMessageIdRef.current = streamId;
                        }

                        console.log('[ui] chunk', streamId, chunk);
                        setMessages((prev) => {
                            const withoutTyping = prev.filter(
                                (m) => !m.isTypingIndicator
                            );
                            const exists = withoutTyping.some(
                                (m) => m.id === streamId
                            );
                            if (!exists) {
                                return [
                                    ...withoutTyping,
                                    {
                                        id: streamId,
                                        role: 'assistant',
                                        text: chunk,
                                    },
                                ];
                            }
                            return withoutTyping.map((m) =>
                                m.id === streamId
                                    ? { ...m, text: m.text + chunk }
                                    : m
                            );
                        });
                    },
                    onComplete: async (message) => {
                        console.log('[ui] complete', message.id, message.content);
                        setMessages((prev) => {
                            const streamId = streamMessageIdRef.current;
                            if (!streamId) return prev;
                            return prev.map((m) =>
                                m.id === streamId
                                    ? {
                                          ...m,
                                          id: message.id,
                                          text:
                                              message.content ||
                                              streamTextRef.current,
                                      }
                                    : m
                            );
                        });
                        streamMessageIdRef.current = null;

                        // New chat: switch to it after streaming — history
                        // reload (in Chat) will contain both messages.
                        if (createdChat) {
                            chatIdRef.current = createdChat.id;
                            if (onChatCreated) onChatCreated(createdChat);
                            return;
                        }

                        // Existing chat: reload history to guarantee the
                        // final answer is rendered even if live updates
                        // were somehow missed by the UI.
                        try {
                            const history = await messageService.getChatMessages(
                                targetChatId
                            );
                            setMessages(
                                (history || []).map((m) => ({
                                    id: m.id,
                                    role: m.role,
                                    text: m.content,
                                }))
                            );
                        } catch (e) {
                            console.error('[chat] reload history failed', e);
                        }
                    },
                    onError: (errorText) => {
                        setMessages((prev) =>
                            prev.filter((m) => !m.isTypingIndicator)
                        );
                        setMessages((prev) => [
                            ...prev,
                            {
                                id: `local-error-${Date.now()}`,
                                role: 'assistant',
                                text: `Error: ${errorText}`,
                            },
                        ]);
                        streamMessageIdRef.current = null;
                    },
                }
            );
        } catch (error) {
            // Network / unexpected error — drop the indicator only
            console.error('[chat] send failed', error);
            setMessages((prev) => prev.filter((m) => !m.isTypingIndicator));
        } finally {
            setIsAssistantTyping(false);
        }
    }, [inputText, isAssistantTyping, onChatCreated]);

    const handleKeyDown = useCallback(
        (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        },
        [sendMessage]
    );

    return {
        messages,
        setMessages,
        inputText,
        setInputText,
        sendMessage,
        handleKeyDown,
        isAssistantTyping,
    };
};
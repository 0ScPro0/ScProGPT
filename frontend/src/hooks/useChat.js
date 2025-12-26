import { useState, useCallback } from 'react';

export const useChat = () => {
    // Messages
    const [messages, setMessages] = useState([]);
    // Textarea input
    const [inputText, setInputText] = useState('');
    
    // Send message
    const sendMessage = useCallback(() => {
        if (!inputText.trim()) return;
        
        console.log('Отправляем:', inputText);
        
        // Create message from user
        const userMessage = {
            id: Date.now(), 
            speaker: "user",
            text: inputText,
        };
        
        // Add message to messages list
        setMessages(prev => [...prev, userMessage]);
        
        // Clear textarea input 
        setInputText('');
        
        // Bot answer
        setTimeout(() => {
            const botMessage = {
                id: Date.now() + 1,
                speaker: "assistant",
                text: 'Message handled, hello, user!',
            };
            setMessages(prev => [...prev, botMessage]);
        }, 1000);
        
    }, [inputText]); // Func depend from inputText

    // Handle enter
    const handleKeyDown = useCallback((e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            sendMessage();
        }
    }, [sendMessage]);

    // Returns
    return {
        messages,
        inputText,
        setInputText,
        sendMessage,
        handleKeyDown,
    };
};
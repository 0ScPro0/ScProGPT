import { useState, useCallback } from 'react';

export const useChat = () => {
    const [messages, setMessages] = useState([]);
    const [inputText, setInputText] = useState('');
    const [isAssistantTyping, setIsAssistantTyping] = useState(false);
    
    const sendMessage = useCallback(() => {
        if (!inputText.trim() || isAssistantTyping) return;
        
        // User message
        const userMessage = {
            id: Date.now(), 
            speaker: "user",
            text: inputText,
        };
        
        setMessages(prev => [...prev, userMessage]);
        setInputText('');
        
        // Show indicator
        setIsAssistantTyping(true);
        const typingIndicatorId = Date.now();
        
        const typingIndicator = {
            id: typingIndicatorId,
            speaker: "assistant",
            text: "• • •",
            isTypingIndicator: true,
        };
        
        setMessages(prev => [...prev, typingIndicator]);
        
        // Timeout before answer
        setTimeout(() => {
            // Clear indicator
            setMessages(prev => prev.filter(msg => msg.id !== typingIndicatorId));
            
            // Start type answer
            const responseText = `Hello! My name is ScProGPT. I'm an AI assistant that can help you with any question you need`;
            typeMessage(responseText);
            
        }, 800); // Timeout plug
        
    }, [inputText, isAssistantTyping]);
    
    const typeMessage = useCallback((text) => {
        const messageId = Date.now();
        let currentText = "";
        let charIndex = 0;
        
        // Create empty message
        const newMessage = {
            id: messageId,
            speaker: "assistant",
            text: currentText,
        };
        
        setMessages(prev => [...prev, newMessage]);
        
        // Type interval
        const interval = setInterval(() => {
            if (charIndex < text.length) {
                currentText += text[charIndex];
                charIndex++;
                
                // Update Message
                setMessages(prev => prev.map(msg => 
                    msg.id === messageId 
                        ? { ...msg, text: currentText }
                        : msg
                ));
            } else {
                clearInterval(interval);
                setIsAssistantTyping(false);
            }
        }, 5);
        
        return () => clearInterval(interval);
    }, []);

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
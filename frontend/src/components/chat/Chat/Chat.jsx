import styles from "./Chat.module.css"
import { InputField } from "../InputField"
import { MessageFromUser } from "../Message/MessageFromUser";
import { MessageFromAssistant } from "../Message/MessageFromAssistant";
import { useChat } from "../../../hooks/useChat"
import { useEffect, useRef } from "react";

export function Chat(){
    // useChat hook
    const {
        messages,
        inputText,
        setInputText,
        sendMessage,
        handleKeyDown,
    } = useChat()
    
    // Ref for scroll
    const messagesEndRef = useRef(null);
    
    // Auto scroll to bottom on new messages
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ 
            behavior: 'smooth',
            block: 'start'
        });
    }, [messages]);

    return (
        <div className={styles.chat}>
            {/* Message wrapper */}
            <div className={styles.messages_wrapper}>
                {messages.map((message) => {
                    if (message.speaker === "assistant") {
                        if (message.isTypingIndicator) {
                            return (
                                <MessageFromAssistant key={message.id}>
                                    <div className={styles.typing_indicator}>
                                        <div className={styles.typing_dots}>
                                            <span>•</span> <span>•</span> <span>•</span>
                                        </div>
                                    </div>
                                </MessageFromAssistant>
                            );
                        }
                        
                        // Если сообщение еще печатается
                        if (message.isTyping) {
                            return (
                                <MessageFromAssistant key={message.id}>
                                    {message.text}
                                    <span className={styles.typing_cursor} />
                                </MessageFromAssistant>
                            );
                        }
                        
                        // Готовое сообщение
                        return (
                            <MessageFromAssistant key={message.id}>
                                {message.text}
                            </MessageFromAssistant>
                        );
                    } 
                    
                    // Сообщение пользователя
                    return (
                        <MessageFromUser key={message.id}>
                            {message.text}
                        </MessageFromUser>
                    );
                })}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Field wrapper */}
            <div className={styles.input_field_wrapper}>
                <InputField 
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onSendClick={sendMessage}
                    onKeyDown={handleKeyDown}
                />
            </div>
        </div>
    )
}
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
                    if (message.speaker == "assistant") {
                        return (
                            <MessageFromAssistant key={message.id}>
                                {message.text}
                            </MessageFromAssistant>
                        );
                    } else if (message.speaker == "user") {
                        console.log(message.text);
                        return (
                            <MessageFromUser key={message.id}>
                                {message.text}
                            </MessageFromUser>
                        );
                    } else {
                        console.log(`Unknown speaker: ${message.id}`);
                        return (
                            <MessageFromUser key={message.id}>
                                {`Unknown speaker\n\n${message.text}`}
                            </MessageFromUser>
                        )
                    }
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
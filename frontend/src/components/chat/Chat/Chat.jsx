import { useEffect, useRef, useState } from "react"
import styles from "./Chat.module.css"
import { InputField } from "../InputField"
import { MessageFromUser } from "../Message/MessageFromUser";
import { MessageFromAssistant } from "../Message/MessageFromAssistant";
import { useChat } from "../../../hooks/useChat"
import { messageService } from "../../../services/api/message"

export function Chat({ collapsed = false, chatId = null, onChatCreated = null }){
    // useChat hook — sending logic lives here (lazy chat creation + AI reply)
    const {
        messages,
        setMessages,
        inputText,
        setInputText,
        sendMessage,
        handleKeyDown,
    } = useChat({ chatId, onChatCreated })

    const [loading, setLoading] = useState(false)

    // Ref for scroll
    const messagesEndRef = useRef(null);

    // Load chat history when a chat is selected
    useEffect(() => {
        let cancelled = false

        if (chatId == null) {
            setMessages([])
            setLoading(false)
            return () => { cancelled = true }
        }

        setLoading(true)
        messageService
            .getChatMessages(chatId)
            .then((history) => {
                if (cancelled) return
                setMessages(
                    (history || []).map((m) => ({
                        id: m.id,
                        role: m.role,
                        text: m.content,
                    }))
                )
            })
            .catch(() => {
                if (!cancelled) setMessages([])
            })
            .finally(() => {
                if (!cancelled) setLoading(false)
            })

        return () => { cancelled = true }
    }, [chatId])

    // Scroll chat to the bottom immediately when messages/history change
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({
            behavior: "auto",
            block: "start",
        });
    }, [messages, chatId]);

    return (
        <div className={styles.chat}>
            {/* Message wrapper */}
            <div className={styles.messages_wrapper}>
                {loading && (
                    <div className={styles.loading}>Loading history...</div>
                )}

                {!loading && messages.length === 0 && (
                    <div className={styles.empty_state}>
                        Select a chat from the sidebar or start a new conversation
                    </div>
                )}

                {messages.map((message) => {
                    if (message.role === "assistant") {
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
            <div className={`${styles.input_field_wrapper} ${collapsed ? styles.input_field_wrapper_collapsed : ""}`}>
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
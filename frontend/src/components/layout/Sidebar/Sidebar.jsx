import { useEffect, useState } from "react"
import styles from "./Sidebar.module.css"
import sidebar_icon from "../../../assets/images/sidebar/sidebar.svg"
import { Logo } from "../../ui/common/Logo"
import { ImageButton } from "../../ui/common/Button"
import { ChatButton } from "./ChatButton"
import { chatService } from "../../../services/api/chat"

export function Sidebar({ onToggle, activeChatId = null, onSelectChat }) {
    const [chats, setChats] = useState([])

    // Load the user's chat list on mount
    useEffect(() => {
        let cancelled = false

        chatService
            .getMyChats()
            .then((data) => {
                if (!cancelled) setChats(data)
            })
            .catch(() => {
                if (!cancelled) setChats([])
            })

        return () => {
            cancelled = true
        }
    }, [])

    return (
        <div className={styles.sidebar}>
            <div className={styles.top}>
                <Logo />
                <ImageButton
                    name="sidebar-button"
                    size="45px"
                    src={sidebar_icon}
                    img_size="26px"
                    onClick={onToggle}
                    style={{ marginLeft: "auto" }}
                />
            </div>

            <div className={styles.chat_list}>
                {chats.map((chat) => (
                    <ChatButton
                        key={chat.id}
                        title={chat.title}
                        active={chat.id === activeChatId}
                        onClick={() => onSelectChat && onSelectChat(chat.id)}
                    />
                ))}

                {chats.length === 0 && (
                    <p className={styles.empty_chats}>No chats yet</p>
                )}
            </div>
        </div>
    )
}
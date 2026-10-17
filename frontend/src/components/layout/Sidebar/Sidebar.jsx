import { useCallback, useEffect, useMemo, useState } from "react"
import styles from "./Sidebar.module.css"
import sidebar_icon from "../../../assets/images/sidebar/sidebar.svg"
import plus_icon from "../../../assets/images/sidebar/plus.svg"
import { Logo } from "../../ui/common/Logo"
import { ImageButton } from "../../ui/common/Button"
import { ChatButton } from "./ChatButton"
import { chatService } from "../../../services/api/chat"

export function Sidebar({ onToggle, activeChatId = null, onSelectChat, refreshChats = 0 }) {
    const [chats, setChats] = useState([])
    // Only one chat actions menu can be open at a time
    const [openMenuChatId, setOpenMenuChatId] = useState(null)

    const closeMenu = () => setOpenMenuChatId(null)

    const loadChats = useCallback(() => {
        chatService
            .getMyChats()
            .then((data) => setChats(data))
            .catch(() => setChats([]))
    }, [])

    // Load the user's chat list on mount / when the list is refreshed
    useEffect(() => {
        loadChats()
    }, [loadChats, refreshChats])

    // Split into pinned / history; most recently updated first
    const { pinned, history } = useMemo(() => {
        const byUpdatedDesc = (a, b) =>
            new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()

        return {
            pinned: chats.filter((c) => c.pinned).sort(byUpdatedDesc),
            history: chats.filter((c) => !c.pinned).sort(byUpdatedDesc),
        }
    }, [chats])

    // "New Chat" does NOT create a chat — it only switches to the
    // new-chat mode; the chat is created on the first message.
    const handleNewChat = () => {
        if (onSelectChat) onSelectChat(null, "New Chat")
    }

    const handlePin = async (chat) => {
        try {
            await chatService.pinChat(chat.id)
            loadChats()
        } catch (e) {
            // interceptor already handles auth errors
        }
    }

    const handleDelete = async (chat) => {
        try {
            await chatService.deleteChat(chat.id)
            if (chat.id === activeChatId && onSelectChat) {
                onSelectChat(null)
            }
            loadChats()
        } catch (e) {
            // ignore — error handling goes here later
        }
    }

    const handleRename = async (chat, newTitle) => {
        try {
            await chatService.renameChat(chat.id, newTitle)
            loadChats()
            // keep the header title in sync if this is the active chat
            if (onSelectChat) onSelectChat(chat.id, newTitle)
        } catch (e) {
            // ignore — error handling goes here later
        }
    }

    const renderChat = (chat) => (
        <ChatButton
            key={chat.id}
            title={chat.title}
            active={chat.id === activeChatId}
            onClick={() =>
                onSelectChat && onSelectChat(chat.id, chat.title)
            }
            menuOpen={chat.id === openMenuChatId}
            onMenuOpen={() => setOpenMenuChatId(chat.id)}
            onMenuClose={closeMenu}
            onPin={() => handlePin(chat)}
            onDelete={() => handleDelete(chat)}
            onRename={(newTitle) => handleRename(chat, newTitle)}
        />
    )

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

            <div className={styles.new_chat_wrapper}>
                <button
                    type="button"
                    className={`${styles.new_chat_button} ${activeChatId == null ? styles.new_chat_button_active : ""}`}
                    onClick={handleNewChat}
                >
                    <img src={plus_icon} alt="+" className={styles.new_chat_icon} />
                    New Chat
                </button>
            </div>

            <div className={styles.chat_list}>
                {pinned.length > 0 && (
                    <>
                        <div className={styles.section_label}>Pinned</div>
                        {pinned.map(renderChat)}
                    </>
                )}

                {history.length > 0 && (
                    <>
                        <div className={styles.section_label}>History</div>
                        {history.map(renderChat)}
                    </>
                )}

                {chats.length === 0 && (
                    <p className={styles.empty_chats}>No chats yet</p>
                )}
            </div>

            {/* Click-away overlay: closes the menu and prevents hover on rows */}
            {openMenuChatId != null && (
                <div className={styles.menu_overlay} onClick={closeMenu} />
            )}
        </div>
    )
}
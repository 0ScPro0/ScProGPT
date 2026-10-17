import { useState } from "react"
import styles from "./Home.module.css"
import { Header } from "../../components/layout/Header"
import { Sidebar } from "../../components/layout/Sidebar"
import { SidebarMinimized } from "../../components/layout/SidebarMinimized"
import { Chat } from "../../components/chat/Chat"

export function Home(){
    const [collapsed, setCollapsed] = useState(false)
    const [activeChatId, setActiveChatId] = useState(null)
    const [activeChatTitle, setActiveChatTitle] = useState("New Chat")
    // Bumped whenever a new chat appears so the Sidebar reloads the list
    const [chatsVersion, setChatsVersion] = useState(0)

    const handleSelectChat = (chatId, chatTitle) => {
        setActiveChatId(chatId)
        setActiveChatTitle(chatId == null ? "New Chat" : chatTitle || null)
    }

    const handleChatCreated = (chat) => {
        setActiveChatId(chat.id)
        setActiveChatTitle(chat.title)
        setChatsVersion((v) => v + 1)
    }

    return(
        <div className={`${styles.home} ${collapsed ? styles.home_collapsed : ""}`}>
            {collapsed ? (
                <SidebarMinimized onExpand={() => setCollapsed(false)} />
            ) : (
                <Sidebar
                    onToggle={() => setCollapsed(true)}
                    activeChatId={activeChatId}
                    onSelectChat={handleSelectChat}
                    refreshChats={chatsVersion}
                />
            )}
            <Header chatTitle={activeChatTitle}/>
            <main className={styles.main}>
                <Chat collapsed={collapsed} chatId={activeChatId} onChatCreated={handleChatCreated}/>
            </main>
        </div>
    )
}
import { useState } from "react"
import styles from "./Home.module.css"
import { Header } from "../../components/layout/Header"
import { Sidebar } from "../../components/layout/Sidebar"
import { SidebarMinimized } from "../../components/layout/SidebarMinimized"
import { Chat } from "../../components/chat/Chat"

export function Home(){
    const [collapsed, setCollapsed] = useState(false)

    return(
        <div className={`${styles.home} ${collapsed ? styles.home_collapsed : ""}`}>
            {collapsed ? (
                <SidebarMinimized onExpand={() => setCollapsed(false)} />
            ) : (
                <Sidebar onToggle={() => setCollapsed(true)} />
            )}
            <Header/>
            <main className={styles.main}>
                <Chat collapsed={collapsed}/>
            </main>
        </div>
    )
}
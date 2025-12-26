import styles from "./Home.module.css"
import { Header } from "../../components/layout/Header"
import { Sidebar } from "../../components/layout/Sidebar"
import { Chat } from "../../components/chat/Chat"

export function Home(){
    return(
        <div className={styles.home}>
            <Sidebar/>
            <Header/>
            <main className={styles.main}>
                <Chat/>
            </main>
        </div>
    )
}   
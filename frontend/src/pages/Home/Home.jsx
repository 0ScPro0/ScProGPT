import styles from "./Home.module.css"
import { Header } from "../../components/layout/Header"
import { Sidebar } from "../../components/layout/Sidebar"

export function Home(){
    return(
        <div className={styles.container}>
            <Sidebar/>
            <Header/>
            <main className={styles.main}>
                
            </main>
        </div>
    )
}   
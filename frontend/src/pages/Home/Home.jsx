//import { Header } from "../../components/layout/Header"
import { Sidebar } from "../../components/layout/Sidebar"
import styles from "./Home.module.css"

export function Home(){
    return(
        <> 
            <Sidebar/>
            <div className={styles.home}>
                
            </div>
        </>
    )
}
import styles from "./Header.module.css"
import { Topbar } from "./Topbar"

export function Header({ chatTitle = null }){
    return (
        <header className={styles.header}>
            <Topbar chatTitle={chatTitle} />
        </header>
    )
}
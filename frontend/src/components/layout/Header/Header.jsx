import styles from "./Header.module.css"
import { Topbar } from "./Topbar"

export function Header(){
    return (
        <header className={styles.header}>
            <Topbar />
        </header>
    )
}
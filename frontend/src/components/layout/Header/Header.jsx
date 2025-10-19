import styles from "./Header.module.css"
import { Logo } from "../../ui/common/Logo"

export function Header(){
    return(
        <>
            <header className={styles.header}>
                <Logo/>
            </header>
        </>
    )
}
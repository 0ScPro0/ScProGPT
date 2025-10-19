import styles from "./Sidebar.module.css"
import { Logo } from "../../ui/common/Logo"

export function Sidebar(){
    return(
        <>
            <div className={styles.sidebar}>
                <div className={styles.top}>
                    <Logo/>
                </div>
            </div>
        </>
    )
}
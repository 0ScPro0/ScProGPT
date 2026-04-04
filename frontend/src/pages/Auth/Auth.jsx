import styles from "./Auth.module.css"
import { TopbarAuth } from "../../components/layout/Header/TopbarAuth"
import { TextButton } from "../../components/ui/common/Button"

export function Auth(){
    return(
        <div className={styles.auth}>
            <TopbarAuth></TopbarAuth>
            <div className={styles.auth_box_wrapper}>
                <div className={styles.auth_box}>
                    
                </div>
            </div>
        </div>
    )
}   
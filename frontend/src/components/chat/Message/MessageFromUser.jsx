import styles from "./MessageFromUser.module.css"
import { Message } from "./Message"

export function MessageFromUser({children}){
    return (
        <div className={styles.message_from_user}>
            <Message>
                {children}
            </Message>
        </div>
    )
}
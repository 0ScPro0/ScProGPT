import styles from "./Message.module.css"
import { Message } from "./Message"

export function MessageFromAssistant({children}){
    return (
        <div className={styles.message_from_user}>
            <Message>
                {children}
            </Message>
        </div>
    )
}
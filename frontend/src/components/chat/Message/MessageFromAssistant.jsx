import styles from "./MessageFromAssistant.module.css"
import { Message } from "./Message"

export function MessageFromAssistant({children}){
    return (
        <div className={styles.message_from_assistant_wrapper}>
            <div className={styles.message_from_assistant}>
                <Message>
                    {children}
                </Message>
            </div>
        </div>
    )
}
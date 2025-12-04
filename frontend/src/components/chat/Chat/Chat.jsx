import styles from "./Chat.module.css"
import { InputField } from "../InputField"
import { MessageFromUser } from "../Message"
import { MessageFromAssistant } from "../Message"

export function Chat(){
    return (
        <div className={styles.chat}>
            <div className={styles.messages_wrapper}>
                <MessageFromUser>
                    Hello!
                </MessageFromUser>

                <MessageFromAssistant>
                    Hello! How can I help you?
                    I can help you with any question you need!
                </MessageFromAssistant>
            </div>
            <div className={styles.input_field_wrapper}>
                <InputField />
            </div>
        </div>
    )
}
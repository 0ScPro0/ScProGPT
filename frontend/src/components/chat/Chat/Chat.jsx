import styles from "./Chat.module.css"
import { InputField } from "../InputField"
import { MessageFromUser } from "../Message"
import { MessageFromAssistant } from "../Message"
import { MESSAGES } from "./mt"

export function Chat(){
    const messages = MESSAGES.map((item, index) => {
        if (item.speaker === "User") {
            return (
                <MessageFromUser key={index}>
                    {item.text}
                </MessageFromUser>
            )
        } else {
            return (
                <MessageFromAssistant key={index}>
                    {item.text}
                </MessageFromAssistant>
            )
        }
    });

    return (
        <div className={styles.chat}>
            <div className={styles.messages_wrapper}>
                {messages}
            </div>
            <div className={styles.input_field_wrapper}>
                <InputField />
            </div>
        </div>
    )
}
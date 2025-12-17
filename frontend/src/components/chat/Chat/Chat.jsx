import styles from "./Chat.module.css"
import { InputField } from "../InputField"

export function Chat(){
    return (
        <div className={styles.chat}>
            <div className={styles.messages_wrapper}>
            </div>
            <div className={styles.input_field_wrapper}>
                <InputField />
            </div>
        </div>
    )
}
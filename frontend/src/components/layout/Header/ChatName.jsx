import styles from "./ChatName.module.css"

export function ChatName({ children }){
    return (
        <div className={styles.chat_name}>
            {children}
        </div>
    )
}
import styles from "./ChatName.module.css"

export function ChatName({ children, style }){
    return (
        <div className={styles.chat_name} style={style}>
            {children}
        </div>
    )
}
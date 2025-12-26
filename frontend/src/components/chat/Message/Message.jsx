import styles from "./Message.module.css"

export function Message({id, speaker, children}){
    return (
        <div className={styles.message}>
            {children}
        </div>
    )
}
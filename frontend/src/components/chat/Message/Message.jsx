import styles from "./Message.module.css"

export function Message({children}){
    return (
        <div className={styles.message}>
            {children}
        </div>
    )
}
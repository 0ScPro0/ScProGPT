import styles from "./ChatButton.module.css"

export function ChatButton({ title, active = false, onClick }) {
    return (
        <button
            type="button"
            className={`${styles.chat_button} ${active ? styles.chat_button_active : ""}`}
            onClick={onClick}
        >
            {title || "New chat"}
        </button>
    )
}
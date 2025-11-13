import styles from "./Header.module.css"
import { ImageButton } from "../../ui/common/Button"

function ChatName({children}){
    return (
        <div className={styles.chat_name}>
            {children}
        </div>
    )
}

function Topbar(){

}

export function Header(){
    return(
        <>
            <header className={styles.header}>
            <ChatName>New Chat</ChatName>
            </header>
        </>
    )
}
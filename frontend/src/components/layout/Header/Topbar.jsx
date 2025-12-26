import styles from "./Topbar.module.css"

import moon_icon from "../../../assets/images/topbar/moon.svg"
import settings_icon from "../../../assets/images/topbar/settings.svg"
import user_icon from "../../../assets/images/topbar/user.svg"

import { useThemeStore } from "../../../stores/themeStore";

import { ImageButton } from "../../ui/common/Button"
import { ChatName } from "./ChatName"

export function Topbar({ 
    chatName = "New Chat", 
}){

    const { toggleTheme, currentTheme } = useThemeStore();

    return (
        <div className={styles.topbar}>
            <div className={styles.left}></div>
            <div className={styles.center}>
                <ChatName>{chatName}</ChatName>
            </div>
            <div className={styles.right}>
                <ImageButton
                    name="theme-button"
                    src={moon_icon} 
                    size={50} 
                    img_size={32}
                    onClick={toggleTheme}/>
                <ImageButton 
                    name="settings-button"
                    src={settings_icon} 
                    size={50} 
                    img_size={32}/>
                <ImageButton 
                    name="user-button"
                    src={user_icon} 
                    size={60} 
                    img_size={42}/>
            </div>
        </div>
    )
}
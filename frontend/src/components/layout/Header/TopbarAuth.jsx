import styles from "./Topbar.module.css"

import moon_icon from "../../../assets/images/topbar/moon.svg"
import settings_icon from "../../../assets/images/topbar/settings.svg"
import user_icon from "../../../assets/images/topbar/user.svg"

import { useThemeStore } from "../../../stores/themeStore";

import { ImageButton } from "../../ui/common/Button"
import { ChatName } from "./ChatName"

export function TopbarAuth(){

    const { toggleTheme, currentTheme } = useThemeStore();

    return (
        <div className={styles.topbar}>
            <div className={styles.left}></div>
            <div className={styles.center}>
                <ChatName style={{ fontSize: '32px' }}>
                    ScProGPT
                </ChatName>
            </div>
            <div className={styles.right} style={{ marginTop: '20px' }}>
                <ImageButton
                    name="theme-button"
                    src={moon_icon} 
                    size={50} 
                    img_size={32}
                    onClick={toggleTheme}
                />
            </div>
        </div>
    )
}
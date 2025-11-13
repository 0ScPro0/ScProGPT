import styles from "./Sidebar.module.css"
import sidebar_icon from "../../../assets/images/sidebar/SidebarWhite.svg"
import plus_icon from "../../../assets/images/sidebar/PlusBlack.svg"
import { Logo } from "../../ui/common/Logo"
import { ImageButton } from "../../ui/common/Button"

export function Sidebar(){
    return(
        <>
            <div className={styles.sidebar}>
                <div className={styles.top}>
                    <Logo/>
                    <ImageButton 
                        size="45px"
                        src={sidebar_icon}
                        width="26px"
                        height="26px"
                    />
                </div>
            </div>
        </>
    )
}
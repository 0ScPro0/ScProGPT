import styles from "./Sidebar.module.css"
import sidebar_icon from "../../../assets/images/sidebar/sidebar.svg"
//import plus_icon from "../../../assets/images/sidebar/plus.svg"
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
                        img_size="26px"
                    />
                </div>
            </div>
        </>
    )
}
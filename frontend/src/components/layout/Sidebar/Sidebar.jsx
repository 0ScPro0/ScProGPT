import styles from "./Sidebar.module.css"
import sidebar_icon from "../../../assets/images/sidebar/SidebarWhite.svg"
import plus_icon from "../../../assets/images/sidebar/PlusBlack.svg"
import { Logo } from "../../ui/common/Logo"
import { Button } from "../../ui/common/Button"

export function Sidebar(){
    return(
        <>
            <div className={styles.sidebar}>
                <div className={styles.top}>
                    <Logo/>
                    <Button 
                        style={{width: "45px", height: "45px"}}
                    >
                        <img width="26px" src={sidebar_icon} alt=""/>
                    </Button>
                    
                </div>
            </div>
        </>
    )
}
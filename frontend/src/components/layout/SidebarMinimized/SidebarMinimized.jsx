import styles from "./SidebarMinimized.module.css"
import sidebar_icon from "../../../assets/images/sidebar/sidebar.svg"
import { Logo } from "../../ui/common/Logo"
import { ImageButton } from "../../ui/common/Button"

/**
 * Narrow collapsed variant of the Sidebar: the full logo and the toggle
 * button stay unchanged (same top bar as the expanded sidebar), only the
 * panel loses its body; a bottom border line separates it from content.
 */
export function SidebarMinimized({ onExpand }) {
    return (
        <div className={styles.sidebar}>
            <div className={styles.top}>
                <Logo />
                <ImageButton
                    name="sidebar-button"
                    size="45px"
                    src={sidebar_icon}
                    img_size="26px"
                    onClick={onExpand}
                    style={{ marginLeft: "auto" }}
                />
            </div>
        </div>
    )
}
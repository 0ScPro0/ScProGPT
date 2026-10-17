import { useEffect, useRef, useState } from "react"
import styles from "./ChatButton.module.css"

/**
 * Chat row in the sidebar: click selects the chat; hovering reveals the
 * "⋯" actions button, which opens a popup with Edit / Pin / Delete.
 * Edit turns the title into an inline input (Enter applies, Esc cancels).
 */
export function ChatButton({
    title,
    active = false,
    onClick,
    menuOpen = false,
    onMenuOpen,
    onMenuClose,
    onPin,
    onDelete,
    onRename,
}) {
    const rowRef = useRef(null)
    const inputRef = useRef(null)
    const [menuPos, setMenuPos] = useState(null)
    const [editing, setEditing] = useState(false)
    const [draft, setDraft] = useState(title || "")

    // Position the popup fixed to the screen so it is always on top and
    // never clipped by the scrollable chat list.
    useEffect(() => {
        if (menuOpen && rowRef.current) {
            const rect = rowRef.current.getBoundingClientRect()
            setMenuPos({
                top: rect.bottom,
                right: window.innerWidth - rect.right + 8,
            })
        } else {
            setMenuPos(null)
        }
    }, [menuOpen])

    // Focus the title input when edit mode starts
    useEffect(() => {
        if (editing && inputRef.current) {
            inputRef.current.focus()
            inputRef.current.select()
        }
    }, [editing])

    const handleSelect = () => {
        if (editing) return
        if (menuOpen && onMenuClose) onMenuClose()
        if (onClick) onClick()
    }

    const toggleMenu = (e) => {
        e.stopPropagation()
        if (menuOpen) {
            if (onMenuClose) onMenuClose()
        } else if (onMenuOpen) {
            onMenuOpen()
        }
    }

    const startEdit = (e) => {
        e.stopPropagation()
        if (onMenuClose) onMenuClose()
        setDraft(title || "")
        setEditing(true)
    }

    const commitEdit = () => {
        const value = draft.trim()
        if (value.length >= 1 && value.length <= 200) {
            if (onRename) onRename(value)
        }
        setEditing(false)
    }

    const cancelEdit = () => {
        setEditing(false)
        setDraft(title || "")
    }

    const handleKeyDown = (e) => {
        if (e.key === "Enter") {
            e.preventDefault()
            if (e.currentTarget.value.trim()) {
                commitEdit()
            } else {
                cancelEdit()
            }
        } else if (e.key === "Escape") {
            e.preventDefault()
            cancelEdit()
        }
        e.stopPropagation()
    }

    const runAction = (fn) => (e) => {
        e.stopPropagation()
        if (onMenuClose) onMenuClose()
        if (fn) fn()
    }

    return (
        <div
            ref={rowRef}
            className={`${styles.row} ${active ? styles.row_active : ""} ${
                menuOpen ? styles.row_menu_open : ""
            }`}
            onClick={handleSelect}
        >
            {editing ? (
                <input
                    ref={inputRef}
                    className={styles.title_input}
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    onKeyDown={handleKeyDown}
                    onBlur={cancelEdit}
                    onClick={(e) => e.stopPropagation()}
                    maxLength={200}
                    placeholder="Chat name"
                    aria-label="Chat name"
                />
            ) : (
                <span className={styles.title}>{title || "New chat"}</span>
            )}

            <button
                type="button"
                className={`${styles.more} ${menuOpen ? styles.more_open : ""}`}
                onClick={toggleMenu}
                aria-label="Chat actions"
                aria-expanded={menuOpen}
            >
                ⋯
            </button>

            {menuOpen && menuPos && (
                <div
                    className={styles.menu}
                    style={{
                        position: "fixed",
                        top: menuPos.top + 4,
                        right: menuPos.right,
                        zIndex: 1200,
                    }}
                    onClick={(e) => e.stopPropagation()}
                    role="menu"
                >
                    <button
                        type="button"
                        className={`${styles.menu_item} ${styles.menu_item_action}`}
                        onClick={startEdit}
                        role="menuitem"
                    >
                        <svg
                            className={styles.menu_item_icon}
                            width="16"
                            height="16"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            aria-hidden="true"
                        >
                            <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" />
                            <path d="m15 5 4 4" />
                        </svg>
                        <span>Edit</span>
                    </button>
                    <button
                        type="button"
                        className={`${styles.menu_item} ${styles.menu_item_action}`}
                        onClick={runAction(onPin)}
                        role="menuitem"
                    >
                        <svg
                            className={styles.menu_item_icon}
                            width="16"
                            height="16"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            aria-hidden="true"
                        >
                            <path d="M12 17v5" />
                            <path d="M9 10.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24V16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V6h1a2 2 0 0 0 0-4H8a2 2 0 0 0 0 4h1z" />
                        </svg>
                        <span>Pin</span>
                    </button>
                    <button
                        type="button"
                        className={`${styles.menu_item} ${styles.menu_item_action}`}
                        onClick={runAction(onDelete)}
                        role="menuitem"
                    >
                        <svg
                            className={styles.menu_item_icon}
                            width="16"
                            height="16"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            aria-hidden="true"
                        >
                            <path d="M3 6h18" />
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" />
                            <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                            <line x1="10" y1="11" x2="10" y2="17" />
                            <line x1="14" y1="11" x2="14" y2="17" />
                        </svg>
                        <span>Delete</span>
                    </button>
                </div>
            )}
        </div>
    )
}
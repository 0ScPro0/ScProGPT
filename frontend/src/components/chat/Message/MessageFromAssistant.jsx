import styles from "./MessageFromAssistant.module.css"
import { Message } from "./Message"
import { MarkdownContent } from "./MarkdownContent"

export function MessageFromAssistant({children}){

    // Plain text (assistant answer / history) is rendered as Markdown;
    // React elements (typing indicators etc.) are passed through as-is.
    const isMarkdown = typeof children === "string"

    return (
        <div className={styles.message_from_assistant_wrapper}>
            <div className={styles.message_from_assistant}>
                <Message>
                    {isMarkdown ? <MarkdownContent>{children}</MarkdownContent> : children}
                </Message>
            </div>
        </div>
    )
}
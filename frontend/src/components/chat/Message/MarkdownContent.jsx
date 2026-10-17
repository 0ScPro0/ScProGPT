import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
// Code highlighting theme
import "highlight.js/styles/github-dark.css";
import styles from "./MarkdownContent.module.css";

/**
 * Renders assistant messages as Markdown (GFM) with code highlighting.
 */
export function MarkdownContent({ children }) {
    return (
        <div className={styles.markdown}>
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeHighlight]}
                components={{
                    a: (props) => (
                        <a {...props} target="_blank" rel="noopener noreferrer" />
                    ),
                }}
            >
                {children}
            </ReactMarkdown>
        </div>
    );
}
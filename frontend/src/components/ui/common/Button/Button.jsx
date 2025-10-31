import styles from "./Button.module.css"

export function Button({children, onClick, ...props}) {

    const handleClick = (event) => {
            console.log("pressed");
            props.onClick?.(event);
    };

    return (
        <div 
            className={styles.button} 
            role="button"
            onClick={handleClick}
            {...props}
        >
            {children}
        </div>
    )
}
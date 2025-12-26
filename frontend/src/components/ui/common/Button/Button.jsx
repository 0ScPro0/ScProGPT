import styles from "./Button.module.css";

export function Button({name, size, children, onClick, style, ...props}) {

    const handleClick = (event) => {
        console.log(`${name} was pressed`);
        onClick?.(event);
    };

    const buttonStyle = size ? {
        width: size,
        height: size,
        ...style
    } : style;

    return (
        <div 
            className={styles.button} 
            role="button"
            style={buttonStyle}
            onClick={handleClick}
            {...props}
        >
            {children}
        </div>
    )
}

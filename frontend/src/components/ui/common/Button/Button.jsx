import styles from "./Button.module.css"

export function Button({children, style, onClick, ...props}) {

    const handleClick = (event) => {
            console.log("pressed");
            props.onClick?.(event);
    };

    return (
        <div 
            className={styles.button} 
            style={style}
            role="button"
            onClick={handleClick}
            {...props}
        >
            {children}
        </div>
    )
}

//const Button = ({children = "Click me", ...props}) => {
//    const handleClick = (event) => {
//        console.log("pressed");
//        props.onClick?.(event);
//  };
//
//  return (
//    <button onClick={handleClick} {...props}>
//        {children}
//    </button>
//  );
//};
//
//export default Button;
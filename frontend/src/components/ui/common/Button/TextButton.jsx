import { Button } from "./Button";

export function TextButton({font, fontSize, children, style, ...props}) {
    const textStyle = {
        fontFamily: font,
        fontSize: fontSize,
        ...style
    };

    return (
        <Button {...props} style={textStyle}>
            {children}
        </Button>
    )
}
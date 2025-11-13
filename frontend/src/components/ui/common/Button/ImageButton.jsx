import { Button } from "./Button";

export function ImageButton({src, width, height, size, children, ...props}) {
    return (
        <Button size={size} {...props}>
            <img 
                src={src} 
                width={width} 
                height={height} 
                alt="button icon"
                style={{ display: 'block' }}
            />
            {children}
        </Button>
    )
}
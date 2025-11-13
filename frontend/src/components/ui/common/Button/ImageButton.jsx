import { Button } from "./Button";

export function ImageButton({src, size, img_size, children, ...props}) {
    return (
        <Button size={size} {...props}>
            <img 
                src={src} 
                width={img_size} 
                height={img_size} 
                alt="button icon"
                style={{ display: 'block' }}
            />
            {children}
        </Button>
    )
}
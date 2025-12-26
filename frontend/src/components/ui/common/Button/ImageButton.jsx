import { Button } from "./Button";

// ImageButton.jsx
export function ImageButton({ 
    src, 
    size, 
    img_size,
    img_width,
    img_height,
    children, 
    img_style = {},
    img_class_name = '', 
    onClick,
    ...props 
}) {

    const width = (img_size !== undefined ? img_size : img_width);
    const height = (img_size !== undefined ? img_size : img_height);
    
    return (
        <Button size={size} onClick={onClick} {...props}>
            <img 
                src={src} 
                width={width} 
                height={height} 
                alt="ico"
                style={{ 
                    display: 'block',
                    ...img_style  
                }}
                className={img_class_name}
            />
            {children}
        </Button>
    );
}
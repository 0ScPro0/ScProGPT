// InputField.jsx
import { useState, useRef, useEffect } from 'react';
import styles from "./InputField.module.css"

export function InputField() {
    const [value, setValue] = useState('');
    const textareaRef = useRef(null);
    
    // Авто-высота textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
        }
    }, [value]);
    
    const handleInput = (e) => {
        setValue(e.target.value);
    };
    
    return (
        <div className={styles.input_field_wrapper}>
            <textarea 
                ref={textareaRef}
                className={styles.input_field}
                value={value}
                onChange={handleInput}
                name="input_field" 
                placeholder="Message to ScProGPT..." 
                rows="1"
            />
        </div>
    )
}
// InputField.jsx
import { useState, useRef, useEffect } from "react";
import { ImageButton } from "../../ui/common/Button/ImageButton";
import send_icon from "../../../assets/images/input_field/send.svg"
import styles from "./InputField.module.css"

export function InputField({
    value,
    onChange,
    onSendClick,
    onKeyDown
}) {

    const textareaRef = useRef(null);
    
    // Textarea auto height
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
        }
    }, [value]);
    
    return (
        <div className={styles.input_field_wrapper}>
            <textarea 
                ref={textareaRef}
                className={styles.input_field}
                value={value}
                onChange={onChange}
                onKeyDown={onKeyDown}
                name="input_field" 
                placeholder="Message to ScProGPT..." 
                rows="1"
            />
            <div className={styles.send_button_wrapper}>
                <ImageButton
                    name="send-button"
                    src={send_icon}
                    size="52px"
                    img_size="35px"
                    img_style={{ marginLeft: '6px' }}
                    onClick={onSendClick}
                />
            </div>
        </div>
    )
}
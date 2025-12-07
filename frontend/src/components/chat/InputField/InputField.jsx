import styles from "./InputField.module.css"

export function InputField(){
    return (
        <div className={styles.input_field_wrapper}>
            <input 
                className={styles.input_field}
                type="text" 
                name="input_field" 
                placeholder="Message to ScProGPT..." 
            />
        </div>
    )
}
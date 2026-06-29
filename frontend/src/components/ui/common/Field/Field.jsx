import styles from "./Field.module.css"

export function Field({ label, type = "text", value, onChange, placeholder, name, icon, onIconClick, style, ...props }) {
    return (
        <div className={styles.field} style={style}>
            {label && <label className={styles.label} htmlFor={name}>{label}</label>}
            <div className={styles.input_wrapper}>
                <input
                    id={name}
                    className={styles.input}
                    type={type}
                    value={value}
                    onChange={onChange}
                    placeholder={placeholder}
                    name={name}
                    {...props}
                />
                {icon && (
                    <span className={styles.icon} onClick={onIconClick}>
                        {icon}
                    </span>
                )}
            </div>
        </div>
    )
}
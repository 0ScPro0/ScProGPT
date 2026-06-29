import { useState } from "react"
import styles from "./Auth.module.css"
import { TopbarAuth } from "../../components/layout/Header/TopbarAuth"

export function Auth() {
    const [activeTab, setActiveTab] = useState("signin")
    const [showPassword, setShowPassword] = useState(false)
    const [showRepeatPassword, setShowRepeatPassword] = useState(false)
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")
    const [repeatPassword, setRepeatPassword] = useState("")
    const [rememberMe, setRememberMe] = useState(false)

    const isSignIn = activeTab === "signin"

    return (
        <div className={styles.auth}>
            <TopbarAuth/>

            {/* Card */}
            <div className={styles.container}>
                <div className={styles.card}>
                    {/* Tabs */}
                    <div className={styles.tabs}>
                        <div
                            className={`${styles.tab} ${isSignIn ? styles.tab_active : ""}`}
                            onClick={() => setActiveTab("signin")}
                        >
                            Sign In
                        </div>
                        <div className={styles.tab_divider}></div>
                        <div
                            className={`${styles.tab} ${!isSignIn ? styles.tab_active : ""}`}
                            onClick={() => setActiveTab("signup")}
                        >
                            Sign Up
                        </div>
                    </div>

                    {/* Email */}
                    <div className={styles.form_group}>
                        <label className={styles.form_label}>Email</label>
                        <input
                            type="email"
                            className={styles.form_input}
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="your@email.com"
                        />
                    </div>

                    {/* Password */}
                    <div className={styles.form_group}>
                        <label className={styles.form_label}>Password</label>
                        <div className={styles.password_wrapper}>
                            <input
                                type={showPassword ? "text" : "password"}
                                className={styles.form_input}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                            />
                            <button
                                type="button"
                                className={styles.password_toggle}
                                onClick={() => setShowPassword(!showPassword)}
                            >
                                <svg className={styles.eye_icon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    {showPassword ? (
                                        <>
                                            <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
                                            <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
                                            <line x1="1" y1="1" x2="23" y2="23" />
                                            <path d="M14.12 14.12a3 3 0 1 1-4.24-4.24" />
                                        </>
                                    ) : (
                                        <>
                                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                                            <circle cx="12" cy="12" r="3" />
                                        </>
                                    )}
                                </svg>
                            </button>
                        </div>
                    </div>

                    {/* Repeat Password (only for Sign Up) */}
                    {!isSignIn && (
                        <div className={styles.form_group}>
                            <label className={styles.form_label}>Repeat password</label>
                            <div className={styles.password_wrapper}>
                                <input
                                    type={showRepeatPassword ? "text" : "password"}
                                    className={styles.form_input}
                                    value={repeatPassword}
                                    onChange={(e) => setRepeatPassword(e.target.value)}
                                    placeholder="••••••••"
                                />
                                <button
                                    type="button"
                                    className={styles.password_toggle}
                                    onClick={() => setShowRepeatPassword(!showRepeatPassword)}
                                >
                                    <svg className={styles.eye_icon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        {showRepeatPassword ? (
                                            <>
                                                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
                                                <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
                                                <line x1="1" y1="1" x2="23" y2="23" />
                                                <path d="M14.12 14.12a3 3 0 1 1-4.24-4.24" />
                                            </>
                                        ) : (
                                            <>
                                                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                                                <circle cx="12" cy="12" r="3" />
                                            </>
                                        )}
                                    </svg>
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Remember Me (only for Sign In) */}
                    {isSignIn && (
                        <div className={styles.remember_me}>
                            <input
                                type="checkbox"
                                id="remember"
                                checked={rememberMe}
                                onChange={(e) => setRememberMe(e.target.checked)}
                            />
                            <label htmlFor="remember">Remember me</label>
                        </div>
                    )}

                    {/* Submit Button */}
                    <button
                        type="button"
                        className={styles.btn_signin}
                        onClick={() => console.log(`${isSignIn ? "Sign In" : "Sign Up"} clicked`)}
                    >
                        {isSignIn ? "Sign In" : "Sign Up"}
                    </button>

                    {/* Divider */}
                    <div className={styles.divider}>
                        {isSignIn ? "Or Sign In with..." : "Or Sign Up with..."}
                    </div>

                    {/* Social Icons */}
                    <div className={styles.social_icons}>
                        <div className={styles.social_icon} onClick={() => console.log("GitHub sign in")}>
                            <svg viewBox="0 0 24 24" fill="currentColor">
                                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                            </svg>
                        </div>
                        <div className={styles.social_icon} onClick={() => console.log("Google sign in")}>
                            <svg viewBox="0 0 24 24">
                                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
                                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                            </svg>
                        </div>
                        <div className={styles.social_icon} onClick={() => console.log("Yandex sign in")}>
                            <svg viewBox="0 0 1000 1000" width="100%" height="100%">
                                <circle cx="500" cy="500" r="498" fill="#FC3F3F" />
                                <path fill="#FFFFFF" d="M 630 200 L 500 200 C 400 200 330 260 330 370 C 330 445 370 492 425 518 L 302 800 L 385 800 L 510 519 L 560 519 L 560 800 L 635 800 L 635 200 Z M 560 270 L 560 455 L 500 455 C 440 455 405 420 405 360 C 405 300 440 270 500 270 L 560 270 Z" />
                            </svg>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
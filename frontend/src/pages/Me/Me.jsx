import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../../stores/authStore";

export function Me() {
    const navigate = useNavigate();
    const user = useAuthStore((state) => state.user);
    const logout = useAuthStore((state) => state.logout);

    const handleLogout = async () => {
        await logout();
        navigate("/signin");
    };

    return (
        <div style={{ maxWidth: 480, margin: "80px auto", padding: "0 16px", textAlign: "center" }}>
            <h1 style={{ marginBottom: 24 }}>Profile</h1>

            {user ? (
                <div style={{ marginBottom: 32 }}>
                    <p><strong>Username:</strong> {user.username}</p>
                    <p><strong>Email:</strong> {user.email}</p>
                </div>
            ) : (
                <p>User info is unavailable.</p>
            )}

            <button
                type="button"
                onClick={handleLogout}
                style={{
                    padding: "12px 24px",
                    fontSize: 16,
                    cursor: "pointer",
                    borderRadius: 10,
                    border: "1px solid",
                }}
            >
                Logout
            </button>
        </div>
    );
}
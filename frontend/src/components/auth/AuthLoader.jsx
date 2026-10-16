import { useEffect, useState } from "react";
import { useAuthStore } from "../../stores/authStore";

/**
 * Restores the session on app start / page reload.
 *
 * 1. Refreshes the access token using the httpOnly refresh cookie.
 * 2. Loads the current user and fills the auth store.
 *
 * Children (routes) are rendered only after the check completes,
 * so ProtectedRoute never redirects before the session is applied.
 */
export function AuthLoader({ children }) {
    const [loading, setLoading] = useState(true);
    const refreshSession = useAuthStore((state) => state.refreshSession);
    const loadCurrentUser = useAuthStore((state) => state.loadCurrentUser);

    useEffect(() => {
        let cancelled = false;

        const boot = async () => {
            if (cancelled) return;

            // Apply httpOnly cookies: refresh token (if present) then user
            await refreshSession();
            await loadCurrentUser();

            if (!cancelled) setLoading(false);
        };

        boot();

        return () => {
            cancelled = true;
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    if (loading) {
        return null; // brief boot screen while the session is being checked
    }

    return <>{children}</>;
}
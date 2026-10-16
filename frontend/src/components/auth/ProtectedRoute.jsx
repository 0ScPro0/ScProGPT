import { Navigate } from "react-router-dom";
import { useAuthStore } from "../../stores/authStore";

/**
 * Guards a route: unauthenticated users are redirected to /auth.
 */
export function ProtectedRoute({ children }) {
    const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

    if (!isAuthenticated) {
        return <Navigate to="/auth" replace />;
    }

    return <>{children}</>;
}
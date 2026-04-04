import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

export function useAuthInit() {
    const navigate = useNavigate();
    const { refreshToken, isAuthenticated, refreshAccessToken } = useAuthStore();

    useEffect(() => {
        const initAuth = async () => {
            if (refreshToken) {
                // Try to refresh token
                const success = await refreshAccessToken();
                if (!success) {
                    // Refresh token is exprited, send user to the signin
                    navigate('/auth');
                }
            } else {
                // User has no token
                navigate('/auth');
            }
        };

        initAuth();
    }, []);
}
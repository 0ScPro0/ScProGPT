import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

export function useAuthInit() {
    const navigate = useNavigate();
    const loadCurrentUser = useAuthStore((state) => state.loadCurrentUser);

    useEffect(() => {
        const initAuth = async () => {
            const ok = await loadCurrentUser();
            if (!ok) {
                // No valid session (cookies missing/expired) → signin page
                navigate('/auth');
            }
        };

        initAuth();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);
}
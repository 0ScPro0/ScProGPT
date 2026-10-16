import { create } from 'zustand';
import { authService } from '../services/api/auth';

// JWT tokens are stored in httpOnly cookies by the backend, so this
// store keeps only the client-side auth state (no tokens exposed to JS).
export const useAuthStore = create((set) => ({
    isAuthenticated: false,
    user: null,

    setAuth: (user) => set({ isAuthenticated: true, user }),

    clearAuth: () => set({ isAuthenticated: false, user: null }),

    // Restore session on app start: call /users/me (browser sends cookies)
    loadCurrentUser: async () => {
        try {
            const user = await authService.me();
            set({ isAuthenticated: true, user });
            return true;
        } catch (error) {
            set({ isAuthenticated: false, user: null });
            return false;
        }
    },

    // Refresh the access token via httpOnly refresh cookie
    refreshSession: async () => {
        try {
            await authService.refresh();
            return true;
        } catch (error) {
            set({ isAuthenticated: false, user: null });
            return false;
        }
    },

    logout: async () => {
        try {
            await authService.logout();
        } catch (error) {
            // ignore network errors — clear local state anyway
        }
        set({ isAuthenticated: false, user: null });
    },
}));
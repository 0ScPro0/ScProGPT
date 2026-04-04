import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { authService } from '../services/api/auth';

export const useAuthStore = create(
    persist(
        (set, get) => ({
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,

            setTokens: (access, refresh) => {
                set({ accessToken: access, refreshToken: refresh, isAuthenticated: true });
            },

            clearTokens: () => {
                set({ accessToken: null, refreshToken: null, isAuthenticated: false });
            },

            refreshAccessToken: async () => {
                const { refreshToken } = get();
                if (!refreshToken) return null;

                try {
                    const data = await authService.refresh(refreshToken);
                    set({ accessToken: data.access_token });
                    return data.access_token;
                } catch (error) {
                    set({ isAuthenticated: false, accessToken: null, refreshToken: null });
                    return null;
                }
            },
            
            getAccessToken: () => get().accessToken,
        }),
        {
            name: 'auth-storage',
            partialize: (state) => ({ refreshToken: state.refreshToken })
        }
    )
);
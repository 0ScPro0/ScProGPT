import { useAuthStore } from '../../stores/authStore';

// Add accessToken to each request
export function setupInterceptors(apiClient) {
    apiClient.interceptors.request.use((config) => {
        const { accessToken } = useAuthStore.getState();
        if (accessToken) {
            config.headers.Authorization = `Bearer ${accessToken}`;
        }
        return config;
    });

    // If 401, we try to refresh the token.
    apiClient.interceptors.response.use(
        (response) => response,
        async (error) => {
            const originalRequest = error.config;
            if (error.response?.status === 401 && !originalRequest._retry) {
                originalRequest._retry = true;
                const { refreshAccessToken } = useAuthStore.getState();
                const newAccessToken = await refreshAccessToken();
                if (newAccessToken) {
                    originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
                    return apiClient(originalRequest);
                }
            }
            const { clearTokens } = useAuthStore.getState();
            clearTokens();
            window.location.href = '/auth';
            return Promise.reject(error);
        }
    );
}

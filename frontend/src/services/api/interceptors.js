import { useAuthStore } from '../../stores/authStore';

// Tokens are stored in httpOnly cookies and are attached to every
// request automatically by the browser (withCredentials: true),
// so there is no need to add an Authorization header manually.
export function setupInterceptors(apiClient) {
    apiClient.interceptors.request.use((config) => config);

    // On 401, try to refresh the access token using the httpOnly
    // refresh cookie; if it fails, log the user out.
    apiClient.interceptors.response.use(
        (response) => response,
        async (error) => {
            const originalRequest = error.config;
            const isRefreshCall =
                originalRequest?.url?.includes('/auth/refresh');
            const status = error.response?.status;

            if (status === 401 && !originalRequest._retry && !isRefreshCall) {
                originalRequest._retry = true;
                try {
                    await apiClient.post('/auth/refresh');
                    return apiClient(originalRequest);
                } catch (refreshError) {
                    // Refresh failed — fall through to logout below.
                }
            }

            if (status === 401) {
                const { logout } = useAuthStore.getState();
                logout();
                if (window.location.pathname !== '/auth') {
                    window.location.href = '/auth';
                }
            }

            return Promise.reject(error);
        }
    );
}

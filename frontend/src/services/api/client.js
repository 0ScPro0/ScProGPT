import axios from 'axios';
import './interceptors';
import { setupInterceptors } from './interceptors';

// Relative base URL: in development the CRA dev server proxies /api/*
// to the backend (see "proxy" in package.json), so the browser and the
// API share one origin and httpOnly cookies work with SameSite=Lax.
const apiClient = axios.create({
    baseURL: '/api/v1',
    headers: { 'Content-Type': 'application/json' },
    // Send credentials (httpOnly auth cookies) with every request
    withCredentials: true
});

export { apiClient };

setupInterceptors(apiClient);
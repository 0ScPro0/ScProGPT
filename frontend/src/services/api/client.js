import axios from 'axios';
import './interceptors';
import { setupInterceptors } from './interceptors';

const apiClient = axios.create({
    baseURL: 'http://127.0.0.1:8000/api/v1',
    headers: { 'Content-Type': 'application/json' }
});

export { apiClient };

setupInterceptors(apiClient);
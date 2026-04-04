import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

// Получаем тему из localStorage синхронно
const getStoredTheme = () => {
    try {
        // Используем правильный ключ - 'theme' (как в вашем store)
        const storage = localStorage.getItem('theme');
        if (storage) {
            return storage; // В вашем store сохраняется просто строка 'light' или 'dark'
        }
    } catch (e) {
        console.error('Failed to get stored theme', e);
    }
    return 'light'; // тема по умолчанию (согласно вашему store)
};

// Устанавливаем тему ДО рендера
const theme = getStoredTheme();
document.documentElement.setAttribute('data-theme', theme);

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
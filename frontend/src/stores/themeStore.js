import { create } from 'zustand';

// Инициализация темы из localStorage
const getInitialTheme = () => {
    if (typeof window !== 'undefined') {
        return localStorage.getItem('theme') || 'light';
    }
    return 'dark';
};

export const useThemeStore = create((set) => ({
    currentTheme: getInitialTheme(),
    toggleTheme: () => set((state) => {
        const newTheme = state.currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        return { currentTheme: newTheme };
    }),
}));
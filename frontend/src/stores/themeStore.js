import { create } from 'zustand';

// localStorage theme init
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
        localStorage.setItem('theme', newTheme);
        return { currentTheme: newTheme };
    }),
}));
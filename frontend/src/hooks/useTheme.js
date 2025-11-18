import { useEffect } from 'react';
import { useThemeStore } from '../stores/themeStore';

export function useThemeInit() {
    const { currentTheme } = useThemeStore();
    
    useEffect(() => {
        document.documentElement.setAttribute('data-theme', currentTheme);
    }, [currentTheme]);
}
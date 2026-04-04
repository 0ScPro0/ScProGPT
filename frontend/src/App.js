import { Home } from "./pages/Home";
import { Auth } from "./pages/Auth"
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { useThemeInit } from './hooks/useTheme';
import { useAuthInit } from "./hooks/useAuth";

function AppContent() {
    //useAuthInit(); 
    return (
        <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/auth" element={<Auth />} />
        </Routes>
    );
}

function App() {
    useThemeInit();
    return (
        <>
            <BrowserRouter>
                <AppContent/>
            </BrowserRouter>
        </>
    );
}

export default App;

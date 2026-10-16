import { Home } from "./pages/Home";
import { Auth } from "./pages/Auth";
import { Me } from "./pages/Me";
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { useThemeInit } from './hooks/useTheme';
import { AuthLoader, ProtectedRoute } from "./components/auth";

function App() {
    useThemeInit();
    return (
        <>
            <BrowserRouter>
                <AuthLoader>
                    <Routes>
                        <Route path="/" element={
                            <ProtectedRoute>
                                <Home />
                            </ProtectedRoute>
                        } />
                        <Route path="/auth" element={<Auth />} />
                        <Route
                            path="/me"
                            element={
                                <ProtectedRoute>
                                    <Me />
                                </ProtectedRoute>
                            }
                        />
                    </Routes>
                </AuthLoader>
            </BrowserRouter>
        </>
    );
}

export default App;

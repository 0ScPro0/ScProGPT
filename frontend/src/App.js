import { Home } from "./pages/Home";
import { useThemeInit } from './hooks/useTheme';

function App() {
    useThemeInit();
    return (
        <>
            <Home></Home>
        </>
    );
}

export default App;

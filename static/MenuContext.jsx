
const { useState, createContext, useContext } = React;

const MenuContext = createContext();

window.MenuProvider = function MenuProvider({ children }) {
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    const toggleMenu = () => {
        setIsMenuOpen(!isMenuOpen);
    };

    const closeMenu = () => {
        setIsMenuOpen(false);
    };

    const value = {
        isMenuOpen,
        toggleMenu,
        closeMenu
    };

    return React.createElement(MenuContext.Provider, { value }, children);
};

window.useMenu = function useMenu() {
    const context = useContext(MenuContext);
    if (!context) {
        throw new Error('useMenu must be used within a MenuProvider');
    }
    return context;
};

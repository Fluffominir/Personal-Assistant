
import React, { useState, createContext, useContext } from 'react'

const MenuContext = createContext()

export function MenuProvider({ children }) {
    const [isMenuOpen, setIsMenuOpen] = useState(false)

    const toggleMenu = () => {
        setIsMenuOpen(!isMenuOpen)
    }

    const closeMenu = () => {
        setIsMenuOpen(false)
    }

    const value = {
        isMenuOpen,
        toggleMenu,
        closeMenu
    }

    return React.createElement(MenuContext.Provider, { value }, children)
}

export function useMenu() {
    const context = useContext(MenuContext)
    if (!context) {
        throw new Error('useMenu must be used within a MenuProvider')
    }
    return context
}

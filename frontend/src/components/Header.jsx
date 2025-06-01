
import React from 'react'
import { useMenu } from './MenuContext'
import './Header.css'

function Header() {
    const { toggleMenu } = useMenu()

    return React.createElement('header', {
        className: 'header'
    }, [
        React.createElement('div', {
            key: 'menu-button',
            className: 'menu-button',
            onClick: toggleMenu
        }, '☰'),
        React.createElement('h1', {
            key: 'title',
            className: 'header-title'
        }, 'ATLAS'),
        React.createElement('div', {
            key: 'spacer',
            className: 'header-spacer'
        })
    ])
}

export default Header

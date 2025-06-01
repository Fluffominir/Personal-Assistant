
window.MobileFooter = function MobileFooter() {
    const { toggleMenu } = window.useMenu();

    return React.createElement('div', {
        className: 'mobile-footer'
    }, 
        React.createElement('button', {
            className: 'mobile-hamburger',
            onClick: toggleMenu,
            'aria-label': 'Open menu'
        }, 
            React.createElement('div', { className: 'mobile-hamburger-line' }),
            React.createElement('div', { className: 'mobile-hamburger-line' }),
            React.createElement('div', { className: 'mobile-hamburger-line' })
        )
    );
};

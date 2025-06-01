
window.SideDrawer = function SideDrawer() {
    const { isMenuOpen, closeMenu } = window.useMenu();

    const menuItems = [
        'Rocket Launch Studio',
        'Connections',
        'Status',
        'Health'
    ];

    const handleItemClick = (item) => {
        console.log(`Menu item clicked: ${item}`);
        closeMenu();
    };

    const handleOverlayClick = (e) => {
        if (e.target === e.currentTarget) {
            closeMenu();
        }
    };

    if (!isMenuOpen) return null;

    return React.createElement('div', {
        className: 'side-drawer-overlay',
        onClick: handleOverlayClick
    }, 
        React.createElement('div', {
            className: `side-drawer ${isMenuOpen ? 'open' : ''}`
        }, 
            menuItems.map((item, index) => 
                React.createElement('div', {
                    key: item,
                    className: 'side-drawer-item',
                    onClick: () => handleItemClick(item)
                }, item)
            )
        )
    );
};

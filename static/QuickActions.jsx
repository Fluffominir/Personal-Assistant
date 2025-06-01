
const { useState } = React;

window.QuickActions = function QuickActions() {
    const actionItems = [
        { title: "AI Training Session", icon: "cube" },
        { title: "Brainstorm Session", icon: "brain" },
        { title: "Schedule Review", icon: "calendar" },
        { title: "Project Update", icon: "folder" },
        { title: "Team Check-in", icon: "users" },
        { title: "Creative Brief", icon: "lightbulb" }
    ];

    const handleActionClick = (title) => {
        console.log(title);
    };

    const getIconElement = (iconName) => {
        const iconMap = {
            cube: "🎲",
            brain: "🧠", 
            calendar: "📅",
            folder: "📁",
            users: "👥",
            lightbulb: "💡"
        };
        return iconMap[iconName] || "⚡";
    };

    return React.createElement('section', {
        className: 'quick-actions-section'
    }, [
        React.createElement('div', {
            key: 'actions-grid',
            className: 'quick-actions-grid'
        }, actionItems.map((item, index) => 
            React.createElement('button', {
                key: index,
                className: 'quick-action-pill',
                onClick: () => handleActionClick(item.title)
            }, [
                React.createElement('span', {
                    key: 'icon',
                    className: 'quick-action-pill-icon'
                }, getIconElement(item.icon)),
                React.createElement('span', {
                    key: 'title',
                    className: 'quick-action-pill-title'
                }, item.title)
            ])
        ))
    ]);
};

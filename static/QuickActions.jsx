
// eslint-disable-next-line no-undef
const { useState, useEffect } = React;

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

    const getIconClass = (iconName) => {
        const iconMap = {
            cube: "fas fa-cube",
            brain: "fas fa-brain", 
            calendar: "fas fa-calendar",
            folder: "fas fa-folder",
            users: "fas fa-users",
            lightbulb: "fas fa-lightbulb"
        };
        return iconMap[iconName] || "fas fa-circle";
    };

    return React.createElement('div', {
        className: 'quick-actions-grid'
    }, actionItems.map((item, index) => 
        React.createElement('button', {
            key: index,
            className: 'quick-action-pill',
            onClick: () => handleActionClick(item.title)
        }, [
            React.createElement('i', {
                key: 'icon',
                className: getIconClass(item.icon)
            }),
            React.createElement('span', {
                key: 'text'
            }, item.title)
        ])
    ));
};
// eslint-disable-next-line no-undef
const { useState, useEffect } = React;

function QuickActions() {
  const actions = [
    { label: "Email", icon: "📧" },
    { label: "Calendar", icon: "📅" },
    { label: "Notes", icon: "📝" },
    { label: "Tasks", icon: "✅" }
  ];

  return (
    React.createElement("section", { className: "quick-actions container" },
      React.createElement("h3", { className: "section-title" }, "Quick Actions"),
      React.createElement("div", { className: "actions-grid" },
        actions.map((action) =>
          React.createElement("button", {
            key: action.label,
            className: "action-btn",
            onClick: () => console.log(`${action.label} clicked`)
          },
            React.createElement("span", { className: "action-icon" }, action.icon),
            React.createElement("span", { className: "action-label" }, action.label)
          )
        )
      )
    )
  );
}

window.QuickActions = QuickActions;

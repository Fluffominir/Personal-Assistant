const { useState, useEffect } = React;

function QuickActions() {
  const actions = [
    { label: "Email", icon: "📧" },
    { label: "Calendar", icon: "📅" },
    { label: "Notes", icon: "📝" },
    { label: "Tasks", icon: "✅" }
  ];

  return (
    React.createElement("section", { className: "quick-actions" },
      actions.map(a =>
        React.createElement("button", {
          key: a.label,
          className: "pill-btn"
        }, `${a.icon} ${a.label}`)
      )
    )
  );
}

window.QuickActions = QuickActions;
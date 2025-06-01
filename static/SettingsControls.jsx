// eslint-disable-next-line no-undef
const { useState, useEffect } = React;

function SettingsControls() {
  return (
    <div className="settings-wrap">
      <button className="settings-btn" title="Settings">⚙️</button>
      <button className="settings-btn" title="Sync">⟳</button>
    </div>
  );
}

window.SettingsControls = SettingsControls;
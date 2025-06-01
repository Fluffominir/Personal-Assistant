const { useState } = React;
export default function SideDrawer() {
  const [open, setOpen] = useState(false);
  const items = ["Rocket Launch Studio", "Connections", "Status", "Health"];

  return (
    <>
      <button
        aria-label="Menu"
        className="menu-btn"
        onClick={() => setOpen(!open)}
      >
        ☰
      </button>

      <aside className={`drawer ${open ? "open" : ""}`}>
        {items.map((i) => (
          <a key={i} className="drawer-link" href="#">{i}</a>
        ))}
      </aside>

      {open && <div className="scrim" onClick={() => setOpen(false)} />}
    </>
  );
}
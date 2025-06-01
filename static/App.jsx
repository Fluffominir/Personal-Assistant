
const { useState, useEffect } = React;

function Header({ eventCount }) {
  const now = new Date();
  const time = now.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  const date = now.toLocaleDateString([], { weekday: "short", month: "short", day: "numeric" });

  return (
    <header className="header-bar">
      <div className="greeting">
        <h2>Hello, Michael,</h2>
        <span>{time} | {date}</span>
      </div>

      <div className="badges">
        <div className="weather-badge">70°F</div>
        <button className="event-badge"
                onClick={()=>document.getElementById("agenda-section")
                                 ?.scrollIntoView({behavior:"smooth"})}>
          {eventCount}
        </button>
      </div>
    </header>
  );
}



function QuickActions() {
  const actions = ["New Event", "New Task", "Add Contact", "Brainstorm"];
  return (
    <div className="quick-actions container">
      {actions.map((a) => (
        <div key={a} className="quick-action-item">{a}</div>
      ))}
    </div>
  );
}

function AgendaColumn() {
  const events = [
    "9 AM – Team Stand-up",
    "11 AM – Client Meeting",
    "3 PM – Project Review",
  ];
  return (
    <div className="column-card agenda-column" id="agenda-section">
      <h3 className="column-title">Agenda</h3>
      {events.map((e) => (
        <div key={e} className="event-item">{e}</div>
      ))}
    </div>
  );
}

function TodoColumn() {
  const todos = [
    "Finish project report",
    "Email budget sheet",
    "Call Alice",
  ];
  return (
    <div className="column-card todo-column">
      <h3 className="column-title">To-Do</h3>
      {todos.map((t) => (
        <div key={t} className="todo-item">🔲 {t}</div>
      ))}
    </div>
  );
}

function App() {
  /* Placeholder event count = agenda length */
  const [events] = useState([1,2,3]); 

  return (
    <>
      {React.createElement(window.SideDrawer)}
      <Header eventCount={events.length} />
      <div className="container">
        {React.createElement(window.AskAtlas)}
        {React.createElement(window.QuickActions)}
      </div>
      <section className="main-columns container">
        <AgendaColumn />
        <TodoColumn />
      </section>
      {React.createElement(window.SettingsControls)}
      {React.createElement(window.MobileFooter)}
    </>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);

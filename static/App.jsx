
import SideDrawer       from "/static/SideDrawer.jsx";
import SettingsControls from "/static/SettingsControls.jsx";
import MobileFooter     from "/static/MobileFooter.jsx";
import "/static/styles/SideDrawer.css";
import "/static/styles/MobileFooter.css";

const { useState, useEffect } = React;

function Header({ eventCount }) {
  const now = new Date();
  const time = now.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  const date = now.toLocaleDateString([], { weekday: "short", month: "short", day: "numeric" });

  return (
    <div className="header-bar container">
      <div>
        <h2 style={{margin:0,fontWeight:700}}>Hello, Michael,</h2>
        <span style={{fontSize:14}}>{time} | {date}</span>
      </div>

      <div style={{display:"flex",gap:16,alignItems:"center"}}>
        {/* Weather badge placeholder */}
        <div className="weather-badge">70°F</div>
        {/* agenda count badge */}
        <span className="event-badge" title="Show Today's Agenda" onClick={()=>{
          document.getElementById("agenda-section")?.scrollIntoView({behavior:"smooth"});
        }}>{eventCount}</span>
      </div>
    </div>
  );
}

function AskAtlas() {
  return (
    <div className="ask-section container">
      <input
        className="ask-input"
        placeholder="Ask me anything…"
        aria-label="Ask ATLAS"
      />
    </div>
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
      <SideDrawer />
      <Header eventCount={events.length} />
      <AskAtlas />
      <QuickActions />
      <section className="main-columns container">
        <AgendaColumn />
        <TodoColumn />
      </section>
      <SettingsControls />
      <MobileFooter />
    </>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);

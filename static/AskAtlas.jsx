
const { useState } = React;

function AskAtlas() {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      console.log('Asking ATLAS:', query);
      // TODO: Integrate with ATLAS chat functionality
      setQuery('');
    }
  };

  return (
    React.createElement('form', {
      className: 'ask-wrap',
      onSubmit: handleSubmit
    }, [
      React.createElement('input', {
        key: 'input',
        className: 'ask-input',
        placeholder: 'Ask about your projects, schedule, personal or business insights…',
        value: query,
        onChange: (e) => setQuery(e.target.value)
      }),
      React.createElement('button', {
        key: 'button',
        className: 'ask-btn',
        type: 'submit'
      }, 'Ask ▾')
    ])
  );
}

window.AskAtlas = AskAtlas;

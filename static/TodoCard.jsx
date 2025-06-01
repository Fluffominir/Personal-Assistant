window.TodoCard = function TodoCard({ items = [] }) {
    const [todos, setTodos] = React.useState(items);
    const [archived, setArchived] = React.useState([]);

    React.useEffect(() => {
        setTodos(items);
    }, [items]);

    const handleToggleTodo = (index) => {
        setTodos(prevTodos => 
            prevTodos.map((todo, i) => 
                i === index ? { ...todo, completed: !todo.completed } : todo
            )
        );

        // If item was just completed, archive it after 2 seconds
        if (!todos[index].completed) {
            setTimeout(() => {
                setTodos(prevTodos => {
                    const todoToArchive = prevTodos[index];
                    const newTodos = prevTodos.filter((_, i) => i !== index);
                    setArchived(prevArchived => [...prevArchived, todoToArchive]);
                    return newTodos;
                });
            }, 2000);
        }
    };

    return React.createElement('div', {
        className: 'todo-card'
    }, [
        React.createElement('div', {
            key: 'header',
            className: 'todo-card-header'
        }, 'To-Do List'),
        React.createElement('div', {
            key: 'body',
            className: 'todo-card-body'
        }, todos.length > 0 ? todos.map((item, index) => 
            React.createElement('div', {
                key: index,
                className: `todo-item-row ${item.completed ? 'completed' : ''}`
            }, [
                React.createElement('div', {
                    key: 'checkbox',
                    className: `todo-checkbox ${item.completed ? 'checked' : ''}`,
                    onClick: () => handleToggleTodo(index)
                }, item.completed ? '✓' : ''),
                React.createElement('div', {
                    key: 'details',
                    className: 'todo-details'
                }, [
                    React.createElement('div', {
                        key: 'title',
                        className: 'todo-title'
                    }, item.title),
                    item.location && React.createElement('div', {
                        key: 'location',
                        className: 'todo-location'
                    }, item.location)
                ])
            ])
        ) : React.createElement('div', {
            className: 'todo-empty'
        }, 'No tasks remaining'))
    ]);
};
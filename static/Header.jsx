
const { useState, useEffect } = React;

window.Header = function Header() {
    const [currentTime, setCurrentTime] = useState('');

    useEffect(() => {
        const updateTime = () => {
            const now = new Date();
            const timeStr = now.toLocaleTimeString('en-US', { 
                hour: 'numeric', 
                minute: '2-digit',
                hour12: true 
            });
            const dateStr = now.toLocaleDateString('en-US', { 
                weekday: 'short', 
                month: 'short', 
                day: 'numeric' 
            });
            setCurrentTime(`${timeStr} | ${dateStr}`);
        };

        updateTime();
        const interval = setInterval(updateTime, 1000);

        return () => clearInterval(interval);
    }, []);

    return React.createElement('header', {
        'data-testid': 'header'
    }, [
        React.createElement('h1', { key: 'greeting' }, 'Hello, Michael,'),
        React.createElement('span', { 
            key: 'time',
            className: 'time' 
        }, currentTime),
        React.createElement('div', {
            key: 'weather',
            className: 'pill weather'
        }, [
            '70°F',
            React.createElement('br', { key: 'br' }),
            'Duluth, GA'
        ]),
        React.createElement('div', {
            key: 'notif', 
            className: 'pill notif'
        }, '3')
    ]);
};

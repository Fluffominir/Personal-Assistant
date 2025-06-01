
const { useState, useEffect } = React;

window.TodayBanner = function TodayBanner() {
    const [currentDate, setCurrentDate] = useState('');
    const [agendaItems, setAgendaItems] = useState([
        { time: '9:00 AM', event: 'Team Standup' },
        { time: '2:00 PM', event: 'Client Review Meeting' }
    ]);

    useEffect(() => {
        const updateDate = () => {
            const now = new Date();
            const dateStr = now.toLocaleDateString('en-US', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            });
            setCurrentDate(dateStr);
        };

        updateDate();
        // Update at midnight
        const now = new Date();
        const msUntilMidnight = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1, 0, 0, 0, 0) - now;
        const timeout = setTimeout(() => {
            updateDate();
            setInterval(updateDate, 24 * 60 * 60 * 1000); // Update every 24 hours
        }, msUntilMidnight);

        return () => clearTimeout(timeout);
    }, []);

    return React.createElement('section', {
        className: 'today-banner'
    }, [
        React.createElement('div', {
            key: 'banner-container',
            className: 'today-banner-container'
        }, [
            React.createElement('div', {
                key: 'date-strip',
                className: 'today-date-strip'
            }, currentDate),
            React.createElement('div', {
                key: 'agenda-content',
                className: 'today-agenda-content'
            }, agendaItems.map((item, index) => 
                React.createElement('div', {
                    key: index,
                    className: 'today-agenda-item'
                }, [
                    React.createElement('span', {
                        key: 'time',
                        className: 'today-agenda-time'
                    }, item.time),
                    React.createElement('span', {
                        key: 'event',
                        className: 'today-agenda-event'
                    }, item.event)
                ])
            ))
        ])
    ]);
};

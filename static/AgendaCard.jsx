
const AgendaCard = function AgendaCard({ items = [] }) {
    return React.createElement('div', {
        className: 'agenda-card'
    }, [
        React.createElement('div', {
            key: 'header',
            className: 'agenda-card-header'
        }, 'Today\'s Agenda'),
        React.createElement('div', {
            key: 'body',
            className: 'agenda-card-body'
        }, items.length > 0 ? items.map((item, index) => 
            React.createElement('div', {
                key: index,
                className: 'agenda-item-row'
            }, [
                React.createElement('div', {
                    key: 'time',
                    className: 'agenda-time'
                }, item.time),
                React.createElement('div', {
                    key: 'details',
                    className: 'agenda-details'
                }, [
                    React.createElement('div', {
                        key: 'title',
                        className: 'agenda-title'
                    }, item.title),
                    item.location && React.createElement('div', {
                        key: 'location',
                        className: 'agenda-location'
                    }, item.location)
                ])
            ])
        ) : React.createElement('div', {
            className: 'agenda-empty'
        }, 'No events scheduled'))
    ]);
};

window.AgendaCard = AgendaCard;

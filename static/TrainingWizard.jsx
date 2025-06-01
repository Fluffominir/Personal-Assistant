window.TrainingWizard = function TrainingWizard({ isOpen, onClose }) {
    const [currentStep, setCurrentStep] = React.useState(1);
    const [formData, setFormData] = React.useState({});
    const totalSteps = 4;

    const handleNext = () => {
        if (currentStep < totalSteps) {
            setCurrentStep(currentStep + 1);
        }
    };

    const handlePrevious = () => {
        if (currentStep > 1) {
            setCurrentStep(currentStep - 1);
        }
    };

    const handleSubmit = () => {
        console.log('Training completed with data:', formData);
        onClose();
    };

    const renderStep = () => {
        switch (currentStep) {
            case 1:
                return React.createElement('div', null, [
                    React.createElement('h2', { key: 'title' }, 'Welcome to ATLAS Training'),
                    React.createElement('p', { key: 'desc' }, 'Let\'s help ATLAS learn about your preferences.')
                ]);
            case 2:
                return React.createElement('div', null, [
                    React.createElement('h2', { key: 'title' }, 'Personal Information'),
                    React.createElement('p', { key: 'desc' }, 'Tell us about yourself.')
                ]);
            case 3:
                return React.createElement('div', null, [
                    React.createElement('h2', { key: 'title' }, 'Work Preferences'),
                    React.createElement('p', { key: 'desc' }, 'How do you like to work?')
                ]);
            case 4:
                return React.createElement('div', null, [
                    React.createElement('h2', { key: 'title' }, 'Final Setup'),
                    React.createElement('p', { key: 'desc' }, 'Almost done!')
                ]);
            default:
                return React.createElement('div', null, 'Step not found');
        }
    };

    if (!isOpen) return null;

    return React.createElement('div', {
        className: 'training-wizard-overlay'
    }, React.createElement('div', {
        className: 'training-wizard-modal'
    }, [
        React.createElement('div', {
            key: 'header',
            className: 'training-wizard-header'
        }, [
            React.createElement('h1', { key: 'title' }, 'ATLAS Training'),
            React.createElement('button', {
                key: 'close',
                className: 'close-btn',
                onClick: onClose
            }, '×')
        ]),

        React.createElement('div', {
            key: 'progress',
            className: 'progress-bar'
        }, React.createElement('div', {
            className: 'progress-fill',
            style: { width: `${(currentStep / totalSteps) * 100}%` }
        })),

        React.createElement('div', {
            key: 'content',
            className: 'training-wizard-content'
        }, renderStep()),

        React.createElement('div', {
            key: 'footer',
            className: 'training-wizard-footer'
        }, [
            React.createElement('button', {
                key: 'prev',
                className: 'wizard-btn secondary',
                onClick: handlePrevious,
                disabled: currentStep === 1
            }, 'Previous'),

            currentStep < totalSteps ? 
                React.createElement('button', {
                    key: 'next',
                    className: 'wizard-btn primary',
                    onClick: handleNext
                }, 'Next') :
                React.createElement('button', {
                    key: 'submit',
                    className: 'wizard-btn primary',
                    onClick: handleSubmit
                }, 'Complete Training')
        ])
    ]));
};


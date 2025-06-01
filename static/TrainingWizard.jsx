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

function TrainingWizard({ isOpen, onClose }) {
    const [currentStep, setCurrentStep] = useState(1);
    const [formData, setFormData] = useState({
        name: '',
        role: '',
        workStyle: '',
        priorities: '',
        communicationStyle: '',
        tools: ''
    });
    const [errors, setErrors] = useState({});
    const [touched, setTouched] = useState({});

    const totalSteps = 4;

    const validateStep = (step) => {
        const newErrors = {};

        switch (step) {
            case 1:
                if (!formData.name.trim()) newErrors.name = 'Name is required';
                if (!formData.role.trim()) newErrors.role = 'Role is required';
                break;
            case 2:
                if (!formData.workStyle.trim()) newErrors.workStyle = 'Work style is required';
                if (!formData.priorities.trim()) newErrors.priorities = 'Priorities are required';
                break;
            case 3:
                if (!formData.communicationStyle.trim()) newErrors.communicationStyle = 'Communication style is required';
                break;
            case 4:
                if (!formData.tools.trim()) newErrors.tools = 'Tools information is required';
                break;
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleNext = () => {
        if (validateStep(currentStep)) {
            setCurrentStep(prev => Math.min(prev + 1, totalSteps));
        } else {
            // Mark fields as touched to show errors
            const stepFields = getStepFields(currentStep);
            const newTouched = { ...touched };
            stepFields.forEach(field => {
                newTouched[field] = true;
            });
            setTouched(newTouched);
        }
    };

    const handlePrevious = () => {
        setCurrentStep(prev => Math.max(prev - 1, 1));
    };

    const getStepFields = (step) => {
        switch (step) {
            case 1: return ['name', 'role'];
            case 2: return ['workStyle', 'priorities'];
            case 3: return ['communicationStyle'];
            case 4: return ['tools'];
            default: return [];
        }
    };

    const handleInputChange = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }));

        // Clear error when user starts typing
        if (errors[field]) {
            setErrors(prev => ({ ...prev, [field]: '' }));
        }

        // Mark field as touched
        setTouched(prev => ({ ...prev, [field]: true }));
    };

    const handleSubmit = async () => {
        if (validateStep(currentStep)) {
            try {
                const response = await fetch('/api/training', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });

                if (response.ok) {
                    alert('Training data saved successfully!');
                    onClose();
                } else {
                    alert('Failed to save training data');
                }
            } catch (error) {
                console.error('Training submission error:', error);
                alert('Error saving training data');
            }
        }
    };

    const renderStep = () => {
        switch (currentStep) {
            case 1:
                return React.createElement('div', null, [
                    React.createElement('h2', { key: 'title' }, 'Personal Information'),
                    React.createElement('p', { key: 'desc' }, 'Tell me about yourself so I can assist you better.'),

                    React.createElement('div', { key: 'name-group', className: 'form-group' }, [
                        React.createElement('label', { key: 'name-label' }, 'Full Name'),
                        React.createElement('input', {
                            key: 'name-input',
                            type: 'text',
                            className: `form-input ${errors.name && touched.name ? 'error' : ''}`,
                            value: formData.name,
                            onChange: (e) => handleInputChange('name', e.target.value),
                            placeholder: 'Enter your full name'
                        }),
                        errors.name && touched.name && React.createElement('span', {
                            key: 'name-error',
                            className: 'error-message'
                        }, errors.name)
                    ]),

                    React.createElement('div', { key: 'role-group', className: 'form-group' }, [
                        React.createElement('label', { key: 'role-label' }, 'Professional Role'),
                        React.createElement('input', {
                            key: 'role-input',
                            type: 'text',
                            className: `form-input ${errors.role && touched.role ? 'error' : ''}`,
                            value: formData.role,
                            onChange: (e) => handleInputChange('role', e.target.value),
                            placeholder: 'e.g., Video Producer, Business Owner'
                        }),
                        errors.role && touched.role && React.createElement('span', {
                            key: 'role-error',
                            className: 'error-message'
                        }, errors.role)
                    ])
                ]);

            case 2:
                return React.createElement('div', null, [
                    React.createElement('h2', { key: 'title' }, 'Work Style & Priorities'),
                    React.createElement('p', { key: 'desc' }, 'Help me understand how you work best.'),

                    React.createElement('div', { key: 'style-group', className: 'form-group' }, [
                        React.createElement('label', { key: 'style-label' }, 'Work Style'),
                        React.createElement('textarea', {
                            key: 'style-input',
                            className: `form-input ${errors.workStyle && touched.workStyle ? 'error' : ''}`,
                            value: formData.workStyle,
                            onChange: (e) => handleInputChange('workStyle', e.target.value),
                            placeholder: 'Describe your work style, preferences, and approach',
                            rows: 3
                        }),
                        errors.workStyle && touched.workStyle && React.createElement('span', {
                            key: 'style-error',
                            className: 'error-message'
                        }, errors.workStyle)
                    ]),

                    React.createElement('div', { key: 'priorities-group', className: 'form-group' }, [
                        React.createElement('label', { key: 'priorities-label' }, 'Current Priorities'),
                        React.createElement('textarea', {
                            key: 'priorities-input',
                            className: `form-input ${errors.priorities && touched.priorities ? 'error' : ''}`,
                            value: formData.priorities,
                            onChange: (e) => handleInputChange('priorities', e.target.value),
                            placeholder: 'What are your main goals and priorities right now?',
                            rows: 3
                        }),
                        errors.priorities && touched.priorities && React.createElement('span', {
                            key: 'priorities-error',
                            className: 'error-message'
                        }, errors.priorities)
                    ])
                ]);

            case 3:
                return React.createElement('div', null, [
                    React.createElement('h2', { key: 'title' }, 'Communication Preferences'),
                    React.createElement('p', { key: 'desc' }, 'How would you like me to communicate with you?'),

                    React.createElement('div', { key: 'comm-group', className: 'form-group' }, [
                        React.createElement('label', { key: 'comm-label' }, 'Communication Style'),
                        React.createElement('textarea', {
                            key: 'comm-input',
                            className: `form-input ${errors.communicationStyle && touched.communicationStyle ? 'error' : ''}`,
                            value: formData.communicationStyle,
                            onChange: (e) => handleInputChange('communicationStyle', e.target.value),
                            placeholder: 'e.g., Direct and concise, detailed explanations, casual tone, etc.',
                            rows: 4
                        }),
                        errors.communicationStyle && touched.communicationStyle && React.createElement('span', {
                            key: 'comm-error',
                            className: 'error-message'
                        }, errors.communicationStyle)
                    ])
                ]);

            case 4:
                return React.createElement('div', null, [
                    React.createElement('h2', { key: 'title' }, 'Tools & Systems'),
                    React.createElement('p', { key: 'desc' }, 'What tools and systems do you use regularly?'),

                    React.createElement('div', { key: 'tools-group', className: 'form-group' }, [
                        React.createElement('label', { key: 'tools-label' }, 'Tools & Software'),
                        React.createElement('textarea', {
                            key: 'tools-input',
                            className: `form-input ${errors.tools && touched.tools ? 'error' : ''}`,
                            value: formData.tools,
                            onChange: (e) => handleInputChange('tools', e.target.value),
                            placeholder: 'List the tools, software, and systems you use for work and personal tasks',
                            rows: 4
                        }),
                        errors.tools && touched.tools && React.createElement('span', {
                            key: 'tools-error',
                            className: 'error-message'
                        }, errors.tools)
                    ])
                ]);

            default:
                return null;
        }
    };

    if (!isOpen) return null;

    return React.createElement('div', {
        className: 'training-wizard-overlay',
        onClick: (e) => {
            if (e.target === e.currentTarget) onClose();
        }
    }, React.createElement('div', {
        className: 'training-wizard-modal'
    }, [
        React.createElement('div', {
            key: 'header',
            className: 'training-wizard-header'
        }, [
            React.createElement('div', { key: 'title-section' }, [
                React.createElement('h1', { key: 'title' }, 'ATLAS Training Session'),
                React.createElement('p', { key: 'subtitle' }, `Step ${currentStep} of ${totalSteps}`)
            ]),
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
            key: 'indicators',
            className: 'step-indicators'
        }, Array.from({ length: totalSteps }, (_, i) => 
            React.createElement('div', {
                key: i,
                className: `step-indicator ${i + 1 <= currentStep ? 'active' : ''}`
            }, i + 1)
        )),

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
}

window.TrainingWizard = TrainingWizard;
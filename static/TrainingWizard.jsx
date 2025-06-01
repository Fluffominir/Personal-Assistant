
const { useState, useEffect } = React;

// Simple useForm hook implementation
function useForm(initialValues, validationRules = {}) {
    const [values, setValues] = useState(initialValues);
    const [errors, setErrors] = useState({});
    const [touched, setTouched] = useState({});

    const validate = (fieldName, value) => {
        const rules = validationRules[fieldName];
        if (!rules) return '';

        if (rules.required && (!value || value.toString().trim() === '')) {
            return rules.message || 'This field is required';
        }

        if (rules.minLength && value.toString().length < rules.minLength) {
            return `Minimum ${rules.minLength} characters required`;
        }

        return '';
    };

    const setValue = (name, value) => {
        setValues(prev => ({ ...prev, [name]: value }));
        
        if (touched[name]) {
            const error = validate(name, value);
            setErrors(prev => ({ ...prev, [name]: error }));
        }
    };

    const setTouched = (name) => {
        setTouched(prev => ({ ...prev, [name]: true }));
        const error = validate(name, values[name]);
        setErrors(prev => ({ ...prev, [name]: error }));
    };

    const isValid = () => {
        const newErrors = {};
        Object.keys(validationRules).forEach(field => {
            const error = validate(field, values[field]);
            if (error) newErrors[field] = error;
        });
        
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    return {
        values,
        errors,
        touched,
        setValue,
        setTouched,
        isValid,
        setValues
    };
}

// Simple Framer Motion alternative using CSS transitions
function AnimatedStep({ children, direction, isActive }) {
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        if (isActive) {
            setMounted(true);
        }
    }, [isActive]);

    if (!isActive) return null;

    return React.createElement('div', {
        className: `training-step ${mounted ? 'active' : ''} direction-${direction}`,
        style: {
            opacity: mounted ? 1 : 0,
            transform: mounted ? 'translateX(0)' : `translateX(${direction === 'right' ? '50px' : '-50px'})`,
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
        }
    }, children);
}

function TrainingWizard({ isOpen, onClose }) {
    const [currentStep, setCurrentStep] = useState(0);
    const [direction, setDirection] = useState('right');
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Step 1: Personal Preferences
    const personalForm = useForm({
        communication_style: '',
        reminder_frequency: '',
        preferred_tone: ''
    }, {
        communication_style: { required: true, message: 'Please select a communication style' },
        reminder_frequency: { required: true, message: 'Please select reminder frequency' },
        preferred_tone: { required: true, message: 'Please select preferred tone' }
    });

    // Step 2: Workflows
    const workflowForm = useForm({
        morning_routine: '',
        task_organization: '',
        break_preferences: ''
    }, {
        morning_routine: { required: true, message: 'Please describe your morning routine' },
        task_organization: { required: true, message: 'Please select task organization preference' }
    });

    // Step 3: Goals
    const goalsForm = useForm({
        primary_goals: '',
        success_metrics: '',
        focus_areas: ''
    }, {
        primary_goals: { required: true, minLength: 10, message: 'Please describe your goals (minimum 10 characters)' },
        success_metrics: { required: true, message: 'Please describe how you measure success' }
    });

    const steps = [
        {
            title: 'Personal Preferences',
            subtitle: 'Help me understand how you like to work and communicate',
            form: personalForm,
            component: PersonalPreferencesStep
        },
        {
            title: 'Workflow Preferences',
            subtitle: 'Tell me about your daily routines and task management style',
            form: workflowForm,
            component: WorkflowStep
        },
        {
            title: 'Goals & Objectives',
            subtitle: 'What are you trying to achieve? How can I help you succeed?',
            form: goalsForm,
            component: GoalsStep
        },
        {
            title: 'Confirmation',
            subtitle: 'Review your preferences and complete the training',
            form: null,
            component: ConfirmationStep
        }
    ];

    const nextStep = () => {
        const currentForm = steps[currentStep].form;
        if (currentForm && !currentForm.isValid()) {
            return;
        }

        if (currentStep < steps.length - 1) {
            setDirection('right');
            setCurrentStep(prev => prev + 1);
        }
    };

    const prevStep = () => {
        if (currentStep > 0) {
            setDirection('left');
            setCurrentStep(prev => prev - 1);
        }
    };

    const handleSubmit = async () => {
        setIsSubmitting(true);
        
        try {
            const trainingData = {
                personal_preferences: personalForm.values,
                workflow_preferences: workflowForm.values,
                goals: goalsForm.values,
                completed_at: new Date().toISOString()
            };

            const response = await fetch('/api/profile/training', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(trainingData)
            });

            if (response.ok) {
                alert('Training completed successfully! ATLAS will now better understand your preferences.');
                onClose();
                resetForms();
            } else {
                throw new Error('Failed to save training data');
            }
        } catch (error) {
            console.error('Error saving training:', error);
            alert('Failed to save training data. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

    const resetForms = () => {
        setCurrentStep(0);
        personalForm.setValues({
            communication_style: '',
            reminder_frequency: '',
            preferred_tone: ''
        });
        workflowForm.setValues({
            morning_routine: '',
            task_organization: '',
            break_preferences: ''
        });
        goalsForm.setValues({
            primary_goals: '',
            success_metrics: '',
            focus_areas: ''
        });
    };

    if (!isOpen) return null;

    const currentStepData = steps[currentStep];

    return React.createElement('div', {
        className: 'training-wizard-overlay',
        onClick: (e) => e.target.className === 'training-wizard-overlay' && onClose()
    }, React.createElement('div', {
        className: 'training-wizard-modal'
    }, [
        // Header
        React.createElement('div', {
            key: 'header',
            className: 'training-wizard-header'
        }, [
            React.createElement('div', {
                key: 'title-section',
                className: 'title-section'
            }, [
                React.createElement('h2', { key: 'title' }, currentStepData.title),
                React.createElement('p', { key: 'subtitle' }, currentStepData.subtitle)
            ]),
            React.createElement('button', {
                key: 'close',
                className: 'close-btn',
                onClick: onClose
            }, '×')
        ]),

        // Progress bar
        React.createElement('div', {
            key: 'progress',
            className: 'progress-bar'
        }, React.createElement('div', {
            className: 'progress-fill',
            style: { width: `${((currentStep + 1) / steps.length) * 100}%` }
        })),

        // Step indicator
        React.createElement('div', {
            key: 'indicators',
            className: 'step-indicators'
        }, steps.map((step, index) => 
            React.createElement('div', {
                key: index,
                className: `step-indicator ${index <= currentStep ? 'active' : ''}`
            }, index + 1)
        )),

        // Content
        React.createElement('div', {
            key: 'content',
            className: 'training-wizard-content'
        }, React.createElement(AnimatedStep, {
            direction,
            isActive: true
        }, React.createElement(currentStepData.component, {
            form: currentStepData.form,
            personalData: personalForm.values,
            workflowData: workflowForm.values,
            goalsData: goalsForm.values
        }))),

        // Footer
        React.createElement('div', {
            key: 'footer',
            className: 'training-wizard-footer'
        }, [
            React.createElement('button', {
                key: 'prev',
                className: 'wizard-btn secondary',
                onClick: prevStep,
                disabled: currentStep === 0,
                style: { visibility: currentStep === 0 ? 'hidden' : 'visible' }
            }, 'Previous'),
            
            currentStep === steps.length - 1 ? 
                React.createElement('button', {
                    key: 'submit',
                    className: 'wizard-btn primary',
                    onClick: handleSubmit,
                    disabled: isSubmitting
                }, isSubmitting ? 'Saving...' : 'Complete Training') :
                React.createElement('button', {
                    key: 'next',
                    className: 'wizard-btn primary',
                    onClick: nextStep
                }, 'Next')
        ])
    ]));
}

// Step Components
function PersonalPreferencesStep({ form }) {
    const { values, errors, setValue, setTouched } = form;

    return React.createElement('div', { className: 'wizard-step' }, [
        React.createElement('div', {
            key: 'communication',
            className: 'form-group'
        }, [
            React.createElement('label', { key: 'label' }, 'How do you prefer to receive information?'),
            React.createElement('select', {
                key: 'input',
                className: `form-input ${errors.communication_style ? 'error' : ''}`,
                value: values.communication_style,
                onChange: (e) => setValue('communication_style', e.target.value),
                onBlur: () => setTouched('communication_style')
            }, [
                React.createElement('option', { key: 'default', value: '' }, 'Select communication style'),
                React.createElement('option', { key: 'direct', value: 'direct' }, 'Direct and concise'),
                React.createElement('option', { key: 'detailed', value: 'detailed' }, 'Detailed explanations'),
                React.createElement('option', { key: 'structured', value: 'structured' }, 'Step-by-step structure'),
                React.createElement('option', { key: 'conversational', value: 'conversational' }, 'Conversational and friendly')
            ]),
            errors.communication_style && React.createElement('span', {
                key: 'error',
                className: 'error-message'
            }, errors.communication_style)
        ]),

        React.createElement('div', {
            key: 'reminders',
            className: 'form-group'
        }, [
            React.createElement('label', { key: 'label' }, 'How often would you like reminders and check-ins?'),
            React.createElement('select', {
                key: 'input',
                className: `form-input ${errors.reminder_frequency ? 'error' : ''}`,
                value: values.reminder_frequency,
                onChange: (e) => setValue('reminder_frequency', e.target.value),
                onBlur: () => setTouched('reminder_frequency')
            }, [
                React.createElement('option', { key: 'default', value: '' }, 'Select frequency'),
                React.createElement('option', { key: 'minimal', value: 'minimal' }, 'Minimal - only when I ask'),
                React.createElement('option', { key: 'daily', value: 'daily' }, 'Daily check-ins'),
                React.createElement('option', { key: 'frequent', value: 'frequent' }, 'Multiple times per day'),
                React.createElement('option', { key: 'proactive', value: 'proactive' }, 'Proactive suggestions')
            ]),
            errors.reminder_frequency && React.createElement('span', {
                key: 'error',
                className: 'error-message'
            }, errors.reminder_frequency)
        ]),

        React.createElement('div', {
            key: 'tone',
            className: 'form-group'
        }, [
            React.createElement('label', { key: 'label' }, 'What tone works best for you?'),
            React.createElement('select', {
                key: 'input',
                className: `form-input ${errors.preferred_tone ? 'error' : ''}`,
                value: values.preferred_tone,
                onChange: (e) => setValue('preferred_tone', e.target.value),
                onBlur: () => setTouched('preferred_tone')
            }, [
                React.createElement('option', { key: 'default', value: '' }, 'Select tone'),
                React.createElement('option', { key: 'professional', value: 'professional' }, 'Professional and formal'),
                React.createElement('option', { key: 'friendly', value: 'friendly' }, 'Friendly and supportive'),
                React.createElement('option', { key: 'encouraging', value: 'encouraging' }, 'Encouraging and motivating'),
                React.createElement('option', { key: 'neutral', value: 'neutral' }, 'Neutral and matter-of-fact')
            ]),
            errors.preferred_tone && React.createElement('span', {
                key: 'error',
                className: 'error-message'
            }, errors.preferred_tone)
        ])
    ]);
}

function WorkflowStep({ form }) {
    const { values, errors, setValue, setTouched } = form;

    return React.createElement('div', { className: 'wizard-step' }, [
        React.createElement('div', {
            key: 'morning',
            className: 'form-group'
        }, [
            React.createElement('label', { key: 'label' }, 'Describe your ideal morning routine'),
            React.createElement('textarea', {
                key: 'input',
                className: `form-input ${errors.morning_routine ? 'error' : ''}`,
                value: values.morning_routine,
                onChange: (e) => setValue('morning_routine', e.target.value),
                onBlur: () => setTouched('morning_routine'),
                placeholder: 'e.g., I like to start with coffee, review my calendar, and prioritize tasks...',
                rows: 3
            }),
            errors.morning_routine && React.createElement('span', {
                key: 'error',
                className: 'error-message'
            }, errors.morning_routine)
        ]),

        React.createElement('div', {
            key: 'organization',
            className: 'form-group'
        }, [
            React.createElement('label', { key: 'label' }, 'How do you prefer to organize tasks?'),
            React.createElement('select', {
                key: 'input',
                className: `form-input ${errors.task_organization ? 'error' : ''}`,
                value: values.task_organization,
                onChange: (e) => setValue('task_organization', e.target.value),
                onBlur: () => setTouched('task_organization')
            }, [
                React.createElement('option', { key: 'default', value: '' }, 'Select organization style'),
                React.createElement('option', { key: 'priority', value: 'priority' }, 'By priority (high/medium/low)'),
                React.createElement('option', { key: 'time', value: 'time' }, 'By time/deadlines'),
                React.createElement('option', { key: 'project', value: 'project' }, 'By project/category'),
                React.createElement('option', { key: 'energy', value: 'energy' }, 'By energy level required'),
                React.createElement('option', { key: 'kanban', value: 'kanban' }, 'Kanban style (to-do/doing/done)')
            ]),
            errors.task_organization && React.createElement('span', {
                key: 'error',
                className: 'error-message'
            }, errors.task_organization)
        ]),

        React.createElement('div', {
            key: 'breaks',
            className: 'form-group'
        }, [
            React.createElement('label', { key: 'label' }, 'When do you prefer to take breaks?'),
            React.createElement('textarea', {
                key: 'input',
                className: 'form-input',
                value: values.break_preferences,
                onChange: (e) => setValue('break_preferences', e.target.value),
                placeholder: 'e.g., Every 90 minutes, after completing tasks, when I feel overwhelmed...',
                rows: 2
            })
        ])
    ]);
}

function GoalsStep({ form }) {
    const { values, errors, setValue, setTouched } = form;

    return React.createElement('div', { className: 'wizard-step' }, [
        React.createElement('div', {
            key: 'goals',
            className: 'form-group'
        }, [
            React.createElement('label', { key: 'label' }, 'What are your primary goals right now?'),
            React.createElement('textarea', {
                key: 'input',
                className: `form-input ${errors.primary_goals ? 'error' : ''}`,
                value: values.primary_goals,
                onChange: (e) => setValue('primary_goals', e.target.value),
                onBlur: () => setTouched('primary_goals'),
                placeholder: 'Describe your main objectives, both personal and professional...',
                rows: 4
            }),
            errors.primary_goals && React.createElement('span', {
                key: 'error',
                className: 'error-message'
            }, errors.primary_goals)
        ]),

        React.createElement('div', {
            key: 'metrics',
            className: 'form-group'
        }, [
            React.createElement('label', { key: 'label' }, 'How do you measure success?'),
            React.createElement('textarea', {
                key: 'input',
                className: `form-input ${errors.success_metrics ? 'error' : ''}`,
                value: values.success_metrics,
                onChange: (e) => setValue('success_metrics', e.target.value),
                onBlur: () => setTouched('success_metrics'),
                placeholder: 'What indicators tell you that you\'re making progress?',
                rows: 3
            }),
            errors.success_metrics && React.createElement('span', {
                key: 'error',
                className: 'error-message'
            }, errors.success_metrics)
        ]),

        React.createElement('div', {
            key: 'focus',
            className: 'form-group'
        }, [
            React.createElement('label', { key: 'label' }, 'What areas need the most focus and improvement?'),
            React.createElement('textarea', {
                key: 'input',
                className: 'form-input',
                value: values.focus_areas,
                onChange: (e) => setValue('focus_areas', e.target.value),
                placeholder: 'Areas where you\'d like ATLAS to help you improve...',
                rows: 3
            })
        ])
    ]);
}

function ConfirmationStep({ personalData, workflowData, goalsData }) {
    return React.createElement('div', { className: 'wizard-step confirmation-step' }, [
        React.createElement('div', { key: 'summary', className: 'training-summary' }, [
            React.createElement('h3', { key: 'title' }, 'Training Summary'),
            React.createElement('p', { key: 'intro' }, 'Please review your preferences before completing the training:'),
            
            React.createElement('div', { key: 'personal', className: 'summary-section' }, [
                React.createElement('h4', { key: 'title' }, 'Personal Preferences'),
                React.createElement('ul', { key: 'list' }, [
                    React.createElement('li', { key: 'comm' }, `Communication: ${personalData.communication_style}`),
                    React.createElement('li', { key: 'remind' }, `Reminders: ${personalData.reminder_frequency}`),
                    React.createElement('li', { key: 'tone' }, `Tone: ${personalData.preferred_tone}`)
                ])
            ]),

            React.createElement('div', { key: 'workflow', className: 'summary-section' }, [
                React.createElement('h4', { key: 'title' }, 'Workflow Preferences'),
                React.createElement('ul', { key: 'list' }, [
                    React.createElement('li', { key: 'morning' }, `Morning routine: ${workflowData.morning_routine.substring(0, 50)}...`),
                    React.createElement('li', { key: 'org' }, `Task organization: ${workflowData.task_organization}`)
                ])
            ]),

            React.createElement('div', { key: 'goals', className: 'summary-section' }, [
                React.createElement('h4', { key: 'title' }, 'Goals & Objectives'),
                React.createElement('ul', { key: 'list' }, [
                    React.createElement('li', { key: 'primary' }, `Primary goals: ${goalsData.primary_goals.substring(0, 50)}...`),
                    React.createElement('li', { key: 'metrics' }, `Success metrics: ${goalsData.success_metrics.substring(0, 50)}...`)
                ])
            ])
        ]),

        React.createElement('div', { key: 'next-steps', className: 'next-steps' }, [
            React.createElement('h4', { key: 'title' }, 'What happens next?'),
            React.createElement('ul', { key: 'list' }, [
                React.createElement('li', { key: 'adapt' }, 'ATLAS will adapt its responses to match your preferences'),
                React.createElement('li', { key: 'suggest' }, 'You\'ll receive personalized suggestions and reminders'),
                React.createElement('li', { key: 'improve' }, 'The system will continue learning from your interactions'),
                React.createElement('li', { key: 'update' }, 'You can update these preferences anytime in Settings')
            ])
        ])
    ]);
}

window.TrainingWizard = TrainingWizard;

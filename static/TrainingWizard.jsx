const { useState, useEffect } = React;

// Custom hook for form management
function useForm(initialValues, validations = {}) {
    const [values, setValues] = React.useState(initialValues);
    const [errors, setErrors] = React.useState({});
    const [touched, setTouched] = React.useState({});

    const validate = (name, value) => {
        const rules = validations[name];
        if (!rules) return '';

        if (rules.required && (!value || value.trim() === '')) {
            return rules.message || `${name} is required`;
        }

        if (rules.minLength && value && value.length < rules.minLength) {
            return rules.message || `${name} must be at least ${rules.minLength} characters`;
        }

        return '';
    };

    const setValue = (name, value) => {
        setValues(prev => ({ ...prev, [name]: value }));

        // Validate on change if field has been touched
        if (touched[name]) {
            const error = validate(name, value);
            setErrors(prev => ({ ...prev, [name]: error }));
        }
    };

    const setFieldTouched = (name) => {
        setTouched(prev => ({ ...prev, [name]: true }));

        // Validate when field is touched
        const error = validate(name, values[name]);
        setErrors(prev => ({ ...prev, [name]: error }));
    };

    const validateAll = () => {
        const newErrors = {};
        let hasErrors = false;

        Object.keys(validations).forEach(name => {
            const error = validate(name, values[name]);
            if (error) {
                newErrors[name] = error;
                hasErrors = true;
            }
        });

        setErrors(newErrors);
        setTouched(Object.keys(validations).reduce((acc, key) => {
            acc[key] = true;
            return acc;
        }, {}));

        return !hasErrors;
    };

    const reset = () => {
        setValues(initialValues);
        setErrors({});
        setTouched({});
    };

    return {
        values,
        errors,
        touched,
        setValue,
        setTouched: setFieldTouched,
        validateAll,
        reset
    };
}

// Personal Preferences Step
function PersonalStep({ form }) {
    return React.createElement('div', { className: 'wizard-step' }, [
        React.createElement('h3', { 
            key: 'title',
            style: { marginBottom: '25px', fontSize: '1.4rem', fontWeight: '700' }
        }, 'Personal Preferences'),

        React.createElement('div', { key: 'comm-group', className: 'form-group' }, [
            React.createElement('label', { key: 'label' }, 'How do you prefer to communicate?'),
            React.createElement('select', {
                key: 'select',
                className: `form-input ${form.errors.communication_style ? 'error' : ''}`,
                value: form.values.communication_style,
                onChange: (e) => form.setValue('communication_style', e.target.value),
                onBlur: () => form.setTouched('communication_style')
            }, [
                React.createElement('option', { key: 'default', value: '' }, 'Select communication style'),
                React.createElement('option', { key: 'direct', value: 'direct' }, 'Direct and concise'),
                React.createElement('option', { key: 'detailed', value: 'detailed' }, 'Detailed explanations'),
                React.createElement('option', { key: 'conversational', value: 'conversational' }, 'Conversational and friendly'),
                React.createElement('option', { key: 'professional', value: 'professional' }, 'Formal and professional')
            ]),
            form.errors.communication_style && React.createElement('span', {
                key: 'error',
                className: 'error-message'
            }, form.errors.communication_style)
        ]),

        React.createElement('div', { key: 'reminder-group', className: 'form-group' }, [
            React.createElement('label', { key: 'label' }, 'How often would you like reminders?'),
            React.createElement('select', {
                key: 'select',
                className: `form-input ${form.errors.reminder_frequency ? 'error' : ''}`,
                value: form.values.reminder_frequency,
                onChange: (e) => form.setValue('reminder_frequency', e.target.value),
                onBlur: () => form.setTouched('reminder_frequency')
            }, [
                React.createElement('option', { key: 'default', value: '' }, 'Select reminder frequency'),
                React.createElement('option', { key: 'minimal', value: 'minimal' }, 'Minimal - only important items'),
                React.createElement('option', { key: 'moderate', value: 'moderate' }, 'Moderate - daily check-ins'),
                React.createElement('option', { key: 'frequent', value: 'frequent' }, 'Frequent - throughout the day'),
                React.createElement('option', { key: 'custom', value: 'custom' }, 'Custom schedule')
            ]),
            form.errors.reminder_frequency && React.createElement('span', {
                key: 'error',
                className: 'error-message'
            }, form.errors.reminder_frequency)
        ]),

        React.createElement('div', { key: 'tone-group', className: 'form-group' }, [
            React.createElement('label', { key: 'label' }, 'What tone do you prefer for AI responses?'),
            React.createElement('select', {
                key: 'select',
                className: `form-input ${form.errors.preferred_tone ? 'error' : ''}`,
                value: form.values.preferred_tone,
                onChange: (e) => form.setValue('preferred_tone', e.target.value),
                onBlur: () => form.setTouched('preferred_tone')
            }, [
                React.createElement('option', { key: 'default', value: '' }, 'Select preferred tone'),
                React.createElement('option', { key: 'encouraging', value: 'encouraging' }, 'Encouraging and supportive'),
                React.createElement('option', { key: 'neutral', value: 'neutral' }, 'Neutral and informative'),
                React.createElement('option', { key: 'playful', value: 'playful' }, 'Playful and casual'),
                React.createElement('option', { key: 'serious', value: 'serious' }, 'Serious and focused')
            ]),
            form.errors.preferred_tone && React.createElement('span', {
                key: 'error',
                className: 'error-message'
            }, form.errors.preferred_tone)
        ])
    ]);
}

// Workflow Preferences Step
function WorkflowStep({ form }) {
    return React.createElement('div', { className: 'wizard-step' }, [
        React.createElement('h3', { 
            key: 'title',
            style: { marginBottom: '25px', fontSize: '1.4rem', fontWeight: '700' }
        }, 'Workflow Preferences'),

        React.createElement('div', { key: 'morning-group', className: 'form-group' }, [
            React.createElement('label', { key: 'label' }, 'Describe your ideal morning routine:'),
            React.createElement('textarea', {
                key: 'textarea',
                className: `form-input ${form.errors.morning_routine ? 'error' : ''}`,
                value: form.values.morning_routine,
                onChange: (e) => form.setValue('morning_routine', e.target.value),
                onBlur: () => form.setTouched('morning_routine'),
                placeholder: 'e.g., Check emails, review calendar, plan priorities...',
                rows: 3
            }),
            form.errors.morning_routine && React.createElement('span', {
                key: 'error',
                className: 'error-message'
            }, form.errors.morning_routine)
        ]),

        React.createElement('div', { key: 'task-group', className: 'form-group' }, [
            React.createElement('label', { key: 'label' }, 'How do you like to organize tasks?'),
            React.createElement('select', {
                key: 'select',
                className: `form-input ${form.errors.task_organization ? 'error' : ''}`,
                value: form.values.task_organization,
                onChange: (e) => form.setValue('task_organization', e.target.value),
                onBlur: () => form.setTouched('task_organization')
            }, [
                React.createElement('option', { key: 'default', value: '' }, 'Select organization method'),
                React.createElement('option', { key: 'priority', value: 'priority' }, 'By priority (high, medium, low)'),
                React.createElement('option', { key: 'time', value: 'time' }, 'By time blocks'),
                React.createElement('option', { key: 'project', value: 'project' }, 'By project or category'),
                React.createElement('option', { key: 'gtd', value: 'gtd' }, 'Getting Things Done (GTD) method'),
                React.createElement('option', { key: 'kanban', value: 'kanban' }, 'Kanban style (To Do, Doing, Done)')
            ]),
            form.errors.task_organization && React.createElement('span', {
                key: 'error',
                className: 'error-message'
            }, form.errors.task_organization)
        ]),

        React.createElement('div', { key: 'break-group', className: 'form-group' }, [
            React.createElement('label', { key: 'label' }, 'What helps you recharge during breaks?'),
            React.createElement('textarea', {
                key: 'textarea',
                className: 'form-input',
                value: form.values.break_preferences,
                onChange: (e) => form.setValue('break_preferences', e.target.value),
                placeholder: 'e.g., Short walks, meditation, music, quick games...',
                rows: 2
            })
        ])
    ]);
}

// Goals Step
function GoalsStep({ form }) {
    return React.createElement('div', { className: 'wizard-step' }, [
        React.createElement('h3', { 
            key: 'title',
            style: { marginBottom: '25px', fontSize: '1.4rem', fontWeight: '700' }
        }, 'Goals & Objectives'),

        React.createElement('div', { key: 'goals-group', className: 'form-group' }, [
            React.createElement('label', { key: 'label' }, 'What are your primary goals for the next 3-6 months?'),
            React.createElement('textarea', {
                key: 'textarea',
                className: `form-input ${form.errors.primary_goals ? 'error' : ''}`,
                value: form.values.primary_goals,
                onChange: (e) => form.setValue('primary_goals', e.target.value),
                onBlur: () => form.setTouched('primary_goals'),
                placeholder: 'Share your professional and personal goals...',
                rows: 4
            }),
            form.errors.primary_goals && React.createElement('span', {
                key: 'error',
                className: 'error-message'
            }, form.errors.primary_goals)
        ]),

        React.createElement('div', { key: 'metrics-group', className: 'form-group' }, [
            React.createElement('label', { key: 'label' }, 'How do you measure success?'),
            React.createElement('textarea', {
                key: 'textarea',
                className: `form-input ${form.errors.success_metrics ? 'error' : ''}`,
                value: form.values.success_metrics,
                onChange: (e) => form.setValue('success_metrics', e.target.value),
                onBlur: () => form.setTouched('success_metrics'),
                placeholder: 'What metrics, milestones, or outcomes matter most to you?',
                rows: 3
            }),
            form.errors.success_metrics && React.createElement('span', {
                key: 'error',
                className: 'error-message'
            }, form.errors.success_metrics)
        ]),

        React.createElement('div', { key: 'focus-group', className: 'form-group' }, [
            React.createElement('label', { key: 'label' }, 'What areas need the most focus or improvement?'),
            React.createElement('textarea', {
                key: 'textarea',
                className: 'form-input',
                value: form.values.focus_areas,
                onChange: (e) => form.setValue('focus_areas', e.target.value),
                placeholder: 'e.g., Time management, work-life balance, productivity, specific skills...',
                rows: 3
            })
        ])
    ]);
}

// Confirmation Step
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
                    React.createElement('li', { key: 'task' }, `Task organization: ${workflowData.task_organization}`),
                    workflowData.break_preferences && React.createElement('li', { key: 'break' }, `Break preferences: ${workflowData.break_preferences.substring(0, 50)}...`)
                ])
            ]),

            React.createElement('div', { key: 'goals', className: 'summary-section' }, [
                React.createElement('h4', { key: 'title' }, 'Goals & Focus Areas'),
                React.createElement('ul', { key: 'list' }, [
                    React.createElement('li', { key: 'primary' }, `Primary goals: ${goalsData.primary_goals.substring(0, 60)}...`),
                    React.createElement('li', { key: 'metrics' }, `Success metrics: ${goalsData.success_metrics.substring(0, 60)}...`),
                    goalsData.focus_areas && React.createElement('li', { key: 'focus' }, `Focus areas: ${goalsData.focus_areas.substring(0, 60)}...`)
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

// Main Training Wizard Component
function TrainingWizard({ isOpen, onClose }) {
    const [currentStep, setCurrentStep] = React.useState(0);
    const [direction, setDirection] = React.useState('right');
    const [isSubmitting, setIsSubmitting] = React.useState(false);

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
        { title: 'Personal Preferences', component: PersonalStep, form: personalForm },
        { title: 'Workflow Preferences', component: WorkflowStep, form: workflowForm },
        { title: 'Goals & Objectives', component: GoalsStep, form: goalsForm },
        { title: 'Confirmation', component: ConfirmationStep, form: null }
    ];

    const resetForms = () => {
        personalForm.reset();
        workflowForm.reset();
        goalsForm.reset();
        setCurrentStep(0);
        setIsSubmitting(false);
    };

    const handleNext = () => {
        const currentStepData = steps[currentStep];

        if (currentStepData.form && !currentStepData.form.validateAll()) {
            return;
        }

        if (currentStep < steps.length - 1) {
            setDirection('right');
            setCurrentStep(currentStep + 1);
        }
    };

    const handlePrevious = () => {
        if (currentStep > 0) {
            setDirection('left');
            setCurrentStep(currentStep - 1);
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

    const handleClose = () => {
        onClose();
        resetForms();
    };

    if (!isOpen) return null;

    const progressPercent = ((currentStep + 1) / steps.length) * 100;
    const currentStepData = steps[currentStep];

    return React.createElement('div', { className: 'training-wizard-overlay' }, [
        React.createElement('div', { key: 'modal', className: 'training-wizard-modal' }, [
            React.createElement('div', { key: 'header', className: 'training-wizard-header' }, [
                React.createElement('div', { key: 'title-section', className: 'title-section' }, [
                    React.createElement('h2', { key: 'title' }, 'AI Training Session'),
                    React.createElement('p', { key: 'subtitle' }, 'Help ATLAS learn your preferences and working style')
                ]),
                React.createElement('button', {
                    key: 'close',
                    className: 'close-btn',
                    onClick: handleClose
                }, '×')
            ]),

            React.createElement('div', { key: 'progress', className: 'progress-bar' }, [
                React.createElement('div', {
                    key: 'fill',
                    className: 'progress-fill',
                    style: { width: `${progressPercent}%` }
                })
            ]),

            React.createElement('div', { key: 'indicators', className: 'step-indicators' }, 
                steps.map((step, index) => 
                    React.createElement('div', {
                        key: index,
                        className: `step-indicator ${index <= currentStep ? 'active' : ''}`
                    }, index + 1)
                )
            ),

            React.createElement('div', { key: 'content', className: 'training-wizard-content' }, [
                React.createElement('div', {
                    key: 'step',
                    className: `training-step active ${direction === 'left' ? 'direction-left' : ''}`
                }, [
                    currentStep === 3 
                        ? React.createElement(ConfirmationStep, {
                            personalData: personalForm.values,
                            workflowData: workflowForm.values,
                            goalsData: goalsForm.values
                        })
                        : React.createElement(currentStepData.component, { form: currentStepData.form })
                ])
            ]),

            React.createElement('div', { key: 'footer', className: 'training-wizard-footer' }, [
                React.createElement('button', {
                    key: 'previous',
                    className: 'wizard-btn secondary',
                    onClick: handlePrevious,
                    disabled: currentStep === 0
                }, 'Previous'),

                currentStep === steps.length - 1
                    ? React.createElement('button', {
                        key: 'finish',
                        className: 'wizard-btn primary',
                        onClick: handleSubmit,
                        disabled: isSubmitting
                    }, isSubmitting ? 'Saving...' : 'Complete Training')
                    : React.createElement('button', {
                        key: 'next',
                        className: 'wizard-btn primary',
                        onClick: handleNext
                    }, 'Next')
            ])
        ])
    ]);
}

// Export to global scope
window.TrainingWizard = TrainingWizard;
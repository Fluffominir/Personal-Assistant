
const { useState, useEffect, useRef } = React;

function AtlasChatBox() {
    const [messages, setMessages] = useState([
        { role: 'assistant', content: 'Hello! I\'m ATLAS, your personal AI companion. How can I help you today?' }
    ]);
    const [inputValue, setInputValue] = useState('');
    const [isConnected, setIsConnected] = useState(false);
    const [isTyping, setIsTyping] = useState(false);
    const wsRef = useRef(null);
    const textareaRef = useRef(null);
    const messagesEndRef = useRef(null);

    useEffect(() => {
        connectWebSocket();
        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const connectWebSocket = () => {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/atlas`;
        
        wsRef.current = new WebSocket(wsUrl);
        
        wsRef.current.onopen = () => {
            setIsConnected(true);
            console.log('WebSocket connected');
        };
        
        wsRef.current.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'chunk') {
                setMessages(prev => {
                    const newMessages = [...prev];
                    const lastMessage = newMessages[newMessages.length - 1];
                    
                    if (lastMessage && lastMessage.role === 'assistant' && lastMessage.streaming) {
                        lastMessage.content += data.content;
                    } else {
                        newMessages.push({
                            role: 'assistant',
                            content: data.content,
                            streaming: true
                        });
                    }
                    
                    return newMessages;
                });
            } else if (data.type === 'complete') {
                setMessages(prev => {
                    const newMessages = [...prev];
                    const lastMessage = newMessages[newMessages.length - 1];
                    if (lastMessage && lastMessage.streaming) {
                        delete lastMessage.streaming;
                    }
                    return newMessages;
                });
                setIsTyping(false);
            } else if (data.type === 'error') {
                setMessages(prev => [
                    ...prev,
                    { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }
                ]);
                setIsTyping(false);
            }
        };
        
        wsRef.current.onclose = () => {
            setIsConnected(false);
            console.log('WebSocket disconnected');
            // Attempt to reconnect after 3 seconds
            setTimeout(connectWebSocket, 3000);
        };
        
        wsRef.current.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const handleSubmit = () => {
        const message = inputValue.trim();
        if (!message || !isConnected) return;

        // Add user message
        setMessages(prev => [...prev, { role: 'user', content: message }]);
        setInputValue('');
        setIsTyping(true);

        // Send to WebSocket
        wsRef.current.send(JSON.stringify({
            type: 'message',
            content: message
        }));

        // Reset textarea height
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    const handleInputChange = (e) => {
        setInputValue(e.target.value);
        
        // Auto-resize textarea
        const textarea = e.target;
        textarea.style.height = 'auto';
        const newHeight = Math.min(textarea.scrollHeight, window.innerHeight * 0.4);
        textarea.style.height = newHeight + 'px';
    };

    const renderMessage = (message, index) => {
        const isUser = message.role === 'user';
        
        return React.createElement('div', {
            key: index,
            className: `message ${isUser ? 'user' : 'assistant'}`,
            style: {
                display: 'flex',
                justifyContent: isUser ? 'flex-end' : 'flex-start',
                marginBottom: '16px'
            }
        }, React.createElement('div', {
            className: 'message-bubble',
            style: {
                maxWidth: '85%',
                padding: '12px 16px',
                borderRadius: '18px',
                color: 'white',
                fontSize: '0.95rem',
                lineHeight: '1.4',
                backgroundColor: isUser ? 'var(--atlas-accent)' : 'rgba(0, 0, 0, 0.4)',
                borderBottomRightRadius: isUser ? '4px' : '18px',
                borderBottomLeftRadius: isUser ? '18px' : '4px',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word'
            }
        }, message.content));
    };

    return React.createElement('div', {
        style: {
            height: '100%',
            display: 'flex',
            flexDirection: 'column'
        }
    }, [
        // Messages area
        React.createElement('div', {
            key: 'messages',
            style: {
                flex: '1',
                overflowY: 'auto',
                padding: '20px',
                minHeight: '200px',
                maxHeight: '400px'
            }
        }, [
            ...messages.map(renderMessage),
            isTyping && React.createElement('div', {
                key: 'typing',
                style: {
                    display: 'flex',
                    justifyContent: 'flex-start',
                    marginBottom: '16px'
                }
            }, React.createElement('div', {
                style: {
                    backgroundColor: 'rgba(0, 0, 0, 0.4)',
                    borderRadius: '18px',
                    padding: '12px 16px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                }
            }, [
                React.createElement('span', {
                    key: 'dot1',
                    style: {
                        width: '6px',
                        height: '6px',
                        backgroundColor: 'white',
                        borderRadius: '50%',
                        animation: 'typing 1.4s infinite'
                    }
                }),
                React.createElement('span', {
                    key: 'dot2',
                    style: {
                        width: '6px',
                        height: '6px',
                        backgroundColor: 'white',
                        borderRadius: '50%',
                        animation: 'typing 1.4s infinite 0.2s'
                    }
                }),
                React.createElement('span', {
                    key: 'dot3',
                    style: {
                        width: '6px',
                        height: '6px',
                        backgroundColor: 'white',
                        borderRadius: '50%',
                        animation: 'typing 1.4s infinite 0.4s'
                    }
                })
            ])),
            React.createElement('div', {
                key: 'scroll-anchor',
                ref: messagesEndRef
            })
        ]),
        
        // Input area
        React.createElement('div', {
            key: 'input-area',
            style: {
                padding: '20px',
                borderTop: '1px solid rgba(255, 255, 255, 0.1)'
            }
        }, React.createElement('div', {
            style: {
                display: 'flex',
                gap: '12px',
                alignItems: 'flex-end'
            }
        }, [
            React.createElement('textarea', {
                key: 'textarea',
                ref: textareaRef,
                value: inputValue,
                onChange: handleInputChange,
                onKeyPress: handleKeyPress,
                placeholder: 'Ask me anything...',
                disabled: !isConnected,
                style: {
                    flex: '1',
                    background: 'rgba(255, 255, 255, 0.15)',
                    border: '1px solid rgba(255, 255, 255, 0.25)',
                    borderRadius: '20px',
                    padding: '12px 16px',
                    color: 'white',
                    fontSize: '0.95rem',
                    resize: 'none',
                    outline: 'none',
                    fontFamily: 'inherit',
                    minHeight: '44px',
                    maxHeight: '40vh'
                }
            }),
            React.createElement('button', {
                key: 'send-btn',
                onClick: handleSubmit,
                disabled: !inputValue.trim() || !isConnected,
                style: {
                    width: '44px',
                    height: '44px',
                    borderRadius: '22px',
                    border: 'none',
                    background: isConnected ? 'var(--atlas-accent)' : 'rgba(255, 255, 255, 0.3)',
                    color: 'white',
                    cursor: isConnected ? 'pointer' : 'not-allowed',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '1.1rem',
                    transition: 'all 0.3s ease'
                }
            }, '→')
        ]))
    ]);
}

window.AtlasChatBox = AtlasChatBox;

import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import CharacterPanel from './CharacterPanel';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const [gameState, setGameState] = useState('character_creation');
  const [character, setCharacter] = useState(null);
  const [showCharacterPanel, setShowCharacterPanel] = useState(false);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Create a new session when component mounts
  useEffect(() => {
    const createSession = async () => {
      try {
        const response = await fetch('http://localhost:5000/session', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error('Failed to create session');
        }

        const data = await response.json();
        setSessionId(data.session_id);
      } catch (error) {
        console.error('Error creating session:', error);
      }
    };

    createSession();
  }, []);

  // Fetch character data when session ID changes
  useEffect(() => {
    if (sessionId) {
      fetchCharacter();
    }
  }, [sessionId]);

  const fetchCharacter = async () => {
    if (!sessionId) return;

    try {
      const response = await fetch(`http://localhost:5000/character?session_id=${sessionId}`);
      
      if (response.ok) {
        const data = await response.json();
        setCharacter(data);
        // Show character panel if we have character data
        if (data && Object.keys(data).length > 0) {
          setShowCharacterPanel(true);
        }
      }
    } catch (error) {
      console.error('Error fetching character:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    // Add user message to chat
    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Send message to backend
      const response = await fetch('http://localhost:5000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          message: input,
          session_id: sessionId
        }),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();
      
      // Update session data
      if (data.session_id) {
        setSessionId(data.session_id);
      }
      
      if (data.game_state) {
        setGameState(data.game_state);
      }
      
      // Add AI response to chat
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
      
      // Fetch updated character info
      fetchCharacter();
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: "Sorry, there was an error connecting to the game master. Please try again." 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleCharacterPanel = () => {
    setShowCharacterPanel(!showCharacterPanel);
  };

  const updateCharacter = async (updatedCharacter) => {
    try {
      const response = await fetch('http://localhost:5000/character', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          session_id: sessionId,
          character: updatedCharacter 
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to update character');
      }

      setCharacter(updatedCharacter);
    } catch (error) {
      console.error('Error updating character:', error);
    }
  };

  return (
    <div className="app-container">
      <header className="header">
        <h1>D&D Game Master Assistant</h1>
        <div className="game-state">
          <span className="state-indicator">Current Mode: </span>
          <span className={`state-value ${gameState}`}>
            {gameState === 'character_creation' ? 'Character Creation' : 
             gameState === 'combat' ? 'Combat' : 'Adventure'}
          </span>
          <button 
            className="character-toggle-btn"
            onClick={toggleCharacterPanel}
          >
            {showCharacterPanel ? 'Hide Character' : 'Show Character'}
          </button>
        </div>
      </header>
      
      <div className="main-content">
        {showCharacterPanel && (
          <CharacterPanel 
            character={character} 
            updateCharacter={updateCharacter}
            gameState={gameState}
          />
        )}
        
        <div className="chat-container">
          <div className="messages">
            {messages.length === 0 ? (
              <div className="welcome-message">
                <h2>Welcome, adventurer!</h2>
                <p>
                  {gameState === 'character_creation' 
                    ? "I sense great power within you. Might I know the name that carries such potential?" 
                    : "I am your AI Game Master. Describe your character or ask me to start a new adventure."}
                </p>
              </div>
            ) : (
              messages.map((message, index) => (
                <div key={index} className={`message ${message.role}`}>
                  <div className="message-content">
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                    </div>
                </div>
              ))
            )}
            {isLoading && (
              <div className="message assistant loading">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          
          <form className="input-form" onSubmit={handleSubmit}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={gameState === 'character_creation' 
                ? "Enter your character details..." 
                : gameState === 'combat'
                ? "Describe your combat action..."
                : "Enter your action or question..."}
              disabled={isLoading}
            />
            <button type="submit" disabled={isLoading || !input.trim()}>
              {isLoading ? 'Sending...' : 'Send'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default App;
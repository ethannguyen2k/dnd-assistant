import React, { useState, useEffect, useRef } from 'react';
import CharacterPanel from './CharacterPanel';
import WorldInfoPanel from './WorldInfoPanel';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState('');
  const [gameState, setGameState] = useState('character_creation');
  const [character, setCharacter] = useState(null);
  const [worldInfo, setWorldInfo] = useState(null);
  const [showCharacterPanel, setShowCharacterPanel] = useState(false);
  const [showWorldInfoPanel, setShowWorldInfoPanel] = useState(false);
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
      fetchWorldInfo();
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
        if (data && Object.keys(data).length > 0 && data.name) {
          setShowCharacterPanel(true);
        }
      }
    } catch (error) {
      console.error('Error fetching character:', error);
    }
  };

  const fetchWorldInfo = async () => {
    if (!sessionId) return;

    try {
      const response = await fetch(`http://localhost:5000/world?session_id=${sessionId}`);
      
      if (response.ok) {
        const data = await response.json();
        setWorldInfo(data);
        // Show world info panel if we have world data
        if (data && (data.locations?.length > 0 || data.npcs?.length > 0 || data.quests?.length > 0)) {
          setShowWorldInfoPanel(true);
        }
      }
    } catch (error) {
      console.error('Error fetching world info:', error);
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
      
      if (data.character) {
        setCharacter(data.character);
        if (data.character && Object.keys(data.character).length > 0 && data.character.name) {
          setShowCharacterPanel(true);
        }
      }
      
      // Log function calls for debugging
      if (data.function_calls && data.function_calls.length > 0) {
        console.log('Function calls executed:', data.function_calls);
        
        // Refresh world info if needed
        const needsWorldRefresh = data.function_calls.some(call => 
          call.function === 'add_world_location' || 
          call.function === 'add_npc' || 
          call.function === 'update_quest'
        );
        
        if (needsWorldRefresh) {
          fetchWorldInfo();
        }
      }
      
      // Add AI response to chat
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
      
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

  const toggleWorldInfoPanel = () => {
    setShowWorldInfoPanel(!showWorldInfoPanel);
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
        <div className="game-state-controls">
          <div className="game-state">
            <span className="state-indicator">Mode: </span>
            <span className={`state-value ${gameState}`}>
              {gameState === 'character_creation' ? 'Character Creation' : 
               gameState === 'combat' ? 'Combat' : 'Adventure'}
            </span>
          </div>
          <div className="panel-controls">
            <button 
              className={`panel-toggle-btn ${showCharacterPanel ? 'active' : ''}`}
              onClick={toggleCharacterPanel}
            >
              {showCharacterPanel ? 'Hide Character' : 'Show Character'}
            </button>
            <button 
              className={`panel-toggle-btn ${showWorldInfoPanel ? 'active' : ''}`}
              onClick={toggleWorldInfoPanel}
              disabled={!worldInfo || (worldInfo.locations.length === 0 && worldInfo.npcs.length === 0 && worldInfo.quests.length === 0)}
            >
              {showWorldInfoPanel ? 'Hide World Info' : 'Show World Info'}
            </button>
          </div>
        </div>
      </header>
      
      <div className="main-content">
        <div className={`sidebar-container ${showCharacterPanel || showWorldInfoPanel ? 'active' : ''}`}>
          {showCharacterPanel && (
            <CharacterPanel 
              character={character} 
              updateCharacter={updateCharacter}
              gameState={gameState}
            />
          )}
          
          {showWorldInfoPanel && (
            <WorldInfoPanel 
              worldInfo={worldInfo}
            />
          )}
        </div>
        
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
                  <div className="message-content">{message.content}</div>
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
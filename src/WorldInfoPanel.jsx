import React, { useState } from 'react';
import './WorldInfoPanel.css';

const WorldInfoPanel = ({ worldInfo }) => {
  const [activeTab, setActiveTab] = useState('locations');
  
  if (!worldInfo) {
    return (
      <div className="world-info-panel">
        <h2>World Information</h2>
        <div className="world-info-placeholder">
          <p>No world information available yet.</p>
        </div>
      </div>
    );
  }
  
  const { locations = [], npcs = [], quests = [] } = worldInfo;
  
  return (
    <div className="world-info-panel">
      <h2>World Information</h2>
      
      <div className="tabs">
        <button 
          className={`tab-button ${activeTab === 'locations' ? 'active' : ''}`}
          onClick={() => setActiveTab('locations')}
        >
          Locations ({locations.length})
        </button>
        <button 
          className={`tab-button ${activeTab === 'npcs' ? 'active' : ''}`}
          onClick={() => setActiveTab('npcs')}
        >
          NPCs ({npcs.length})
        </button>
        <button 
          className={`tab-button ${activeTab === 'quests' ? 'active' : ''}`}
          onClick={() => setActiveTab('quests')}
        >
          Quests ({quests.length})
        </button>
      </div>
      
      <div className="tab-content">
        {activeTab === 'locations' && (
          <div className="locations-tab">
            {locations.length === 0 ? (
              <p className="empty-state">No locations discovered yet.</p>
            ) : (
              <ul className="location-list">
                {locations.map((location, index) => (
                  <li key={index} className="location-item">
                    <div className="location-header">
                      <h3>{location.name}</h3>
                      <span className="location-type">{location.type}</span>
                    </div>
                    <p className="location-description">{location.description}</p>
                    
                    {location.points_of_interest && location.points_of_interest.length > 0 && (
                      <div className="location-poi">
                        <h4>Points of Interest:</h4>
                        <ul>
                          {location.points_of_interest.map((poi, poiIndex) => (
                            <li key={poiIndex}>{poi}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
        
        {activeTab === 'npcs' && (
          <div className="npcs-tab">
            {npcs.length === 0 ? (
              <p className="empty-state">No NPCs encountered yet.</p>
            ) : (
              <ul className="npc-list">
                {npcs.map((npc, index) => (
                  <li key={index} className="npc-item">
                    <div className="npc-header">
                      <h3>{npc.name}</h3>
                      <span className="npc-role">{npc.role}</span>
                    </div>
                    <p className="npc-description">{npc.description}</p>
                    
                    {npc.location && (
                      <p className="npc-location">
                        <strong>Location:</strong> {npc.location}
                      </p>
                    )}
                    
                    {npc.personality && (
                      <p className="npc-personality">
                        <strong>Personality:</strong> {npc.personality}
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
        
        {activeTab === 'quests' && (
          <div className="quests-tab">
            {quests.length === 0 ? (
              <p className="empty-state">No quests available yet.</p>
            ) : (
              <ul className="quest-list">
                {quests.map((quest, index) => (
                  <li key={index} className={`quest-item status-${quest.status}`}>
                    <div className="quest-header">
                      <h3>{quest.title}</h3>
                      <span className="quest-status">{quest.status.replace('_', ' ')}</span>
                    </div>
                    <p className="quest-description">{quest.description}</p>
                    
                    {quest.giver && (
                      <p className="quest-giver">
                        <strong>Quest Giver:</strong> {quest.giver}
                      </p>
                    )}
                    
                    {quest.location && (
                      <p className="quest-location">
                        <strong>Location:</strong> {quest.location}
                      </p>
                    )}
                    
                    {quest.reward && (
                      <p className="quest-reward">
                        <strong>Reward:</strong> {quest.reward}
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default WorldInfoPanel;
import React, { useState } from 'react';
import './CharacterPanel.css';

const CharacterPanel = ({ character, updateCharacter, gameState }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedCharacter, setEditedCharacter] = useState({ ...character });

  // If character is null or empty, show a placeholder
  if (!character || Object.keys(character).length === 0) {
    return (
      <div className="character-panel">
        <h2>Character Sheet</h2>
        <div className="character-placeholder">
          <p>No character data yet. Complete the character creation process to see your character details here.</p>
        </div>
      </div>
    );
  }

  const handleEdit = () => {
    setIsEditing(true);
    setEditedCharacter({ ...character });
  };

  const handleCancel = () => {
    setIsEditing(false);
  };

  const handleSave = () => {
    updateCharacter(editedCharacter);
    setIsEditing(false);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setEditedCharacter(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleInventoryChange = (index, value) => {
    const newInventory = [...editedCharacter.inventory || []];
    newInventory[index] = value;
    setEditedCharacter(prev => ({
      ...prev,
      inventory: newInventory
    }));
  };

  const addInventoryItem = () => {
    setEditedCharacter(prev => ({
      ...prev,
      inventory: [...(prev.inventory || []), '']
    }));
  };

  const removeInventoryItem = (index) => {
    const newInventory = [...editedCharacter.inventory || []];
    newInventory.splice(index, 1);
    setEditedCharacter(prev => ({
      ...prev,
      inventory: newInventory
    }));
  };

  // Render the view mode (non-editing)
  if (!isEditing) {
    return (
      <div className="character-panel">
        <div className="character-header">
          <h2>Character Sheet</h2>
          {gameState === 'character_creation' && (
            <button className="edit-btn" onClick={handleEdit}>Edit</button>
          )}
        </div>
        
        <div className="character-details">
          <div className="character-section">
            <h3>Basic Info</h3>
            <div className="character-field">
              <label>Name:</label>
              <span>{character.name || 'Unknown'}</span>
            </div>
            <div className="character-field">
              <label>Race:</label>
              <span>{character.race || 'Unknown'}</span>
            </div>
            <div className="character-field">
              <label>Class:</label>
              <span>{character.class || 'Unknown'}</span>
            </div>
            <div className="character-field">
              <label>Background:</label>
              <span>{character.background || 'Unknown'}</span>
            </div>
          </div>
          
          {/* Show other attributes if they exist */}
          {character.strength && (
            <div className="character-section">
              <h3>Attributes</h3>
              <div className="attributes-grid">
                {character.strength && (
                  <div className="attribute">
                    <label>STR</label>
                    <span>{character.strength}</span>
                  </div>
                )}
                {character.dexterity && (
                  <div className="attribute">
                    <label>DEX</label>
                    <span>{character.dexterity}</span>
                  </div>
                )}
                {character.constitution && (
                  <div className="attribute">
                    <label>CON</label>
                    <span>{character.constitution}</span>
                  </div>
                )}
                {character.intelligence && (
                  <div className="attribute">
                    <label>INT</label>
                    <span>{character.intelligence}</span>
                  </div>
                )}
                {character.wisdom && (
                  <div className="attribute">
                    <label>WIS</label>
                    <span>{character.wisdom}</span>
                  </div>
                )}
                {character.charisma && (
                  <div className="attribute">
                    <label>CHA</label>
                    <span>{character.charisma}</span>
                  </div>
                )}
              </div>
            </div>
          )}
          
          {/* Show HP if it exists */}
          {character.hp && (
            <div className="character-section">
              <h3>Health</h3>
              <div className="health-bar">
                <div className="hp-label">HP: {character.currentHp || character.hp}/{character.hp}</div>
                <div className="hp-bar-container">
                  <div 
                    className="hp-bar-fill" 
                    style={{ width: `${((character.currentHp || character.hp) / character.hp) * 100}%` }}
                  ></div>
                </div>
              </div>
            </div>
          )}
          
          {/* Show inventory if it exists */}
          <div className="character-section">
            <h3>Inventory</h3>
            {character.inventory && character.inventory.length > 0 ? (
              <ul className="inventory-list">
                {character.inventory.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            ) : (
              <p>No items in inventory</p>
            )}
          </div>
        </div>
      </div>
    );
  }
  
  // Render the edit mode
  return (
    <div className="character-panel editing">
      <div className="character-header">
        <h2>Edit Character</h2>
        <div className="edit-controls">
          <button className="save-btn" onClick={handleSave}>Save</button>
          <button className="cancel-btn" onClick={handleCancel}>Cancel</button>
        </div>
      </div>
      
      <div className="character-form">
        <div className="character-section">
          <h3>Basic Info</h3>
          <div className="form-group">
            <label>Name:</label>
            <input 
              type="text" 
              name="name" 
              value={editedCharacter.name || ''} 
              onChange={handleChange} 
            />
          </div>
          <div className="form-group">
            <label>Race:</label>
            <input 
              type="text" 
              name="race" 
              value={editedCharacter.race || ''} 
              onChange={handleChange} 
            />
          </div>
          <div className="form-group">
            <label>Class:</label>
            <input 
              type="text" 
              name="class" 
              value={editedCharacter.class || ''} 
              onChange={handleChange} 
            />
          </div>
          <div className="form-group">
            <label>Background:</label>
            <textarea 
              name="background" 
              value={editedCharacter.background || ''} 
              onChange={handleChange} 
            />
          </div>
        </div>
        
        {/* Edit attributes if they exist */}
        {character.strength && (
          <div className="character-section">
            <h3>Attributes</h3>
            <div className="attributes-grid editing">
              <div className="form-group">
                <label>STR:</label>
                <input 
                  type="number" 
                  name="strength" 
                  value={editedCharacter.strength || ''} 
                  onChange={handleChange} 
                />
              </div>
              <div className="form-group">
                <label>DEX:</label>
                <input 
                  type="number" 
                  name="dexterity" 
                  value={editedCharacter.dexterity || ''} 
                  onChange={handleChange} 
                />
              </div>
              <div className="form-group">
                <label>CON:</label>
                <input 
                  type="number" 
                  name="constitution" 
                  value={editedCharacter.constitution || ''} 
                  onChange={handleChange} 
                />
              </div>
              <div className="form-group">
                <label>INT:</label>
                <input 
                  type="number" 
                  name="intelligence" 
                  value={editedCharacter.intelligence || ''} 
                  onChange={handleChange} 
                />
              </div>
              <div className="form-group">
                <label>WIS:</label>
                <input 
                  type="number" 
                  name="wisdom" 
                  value={editedCharacter.wisdom || ''} 
                  onChange={handleChange} 
                />
              </div>
              <div className="form-group">
                <label>CHA:</label>
                <input 
                  type="number" 
                  name="charisma" 
                  value={editedCharacter.charisma || ''} 
                  onChange={handleChange} 
                />
              </div>
            </div>
          </div>
        )}
        
        {/* Edit HP if it exists */}
        {character.hp && (
          <div className="character-section">
            <h3>Health</h3>
            <div className="form-group">
              <label>Max HP:</label>
              <input 
                type="number" 
                name="hp" 
                value={editedCharacter.hp || ''} 
                onChange={handleChange} 
              />
            </div>
            <div className="form-group">
              <label>Current HP:</label>
              <input 
                type="number" 
                name="currentHp" 
                value={editedCharacter.currentHp || editedCharacter.hp || ''} 
                onChange={handleChange} 
              />
            </div>
          </div>
        )}
        
        {/* Edit inventory */}
        <div className="character-section">
          <h3>Inventory</h3>
          {editedCharacter.inventory && editedCharacter.inventory.length > 0 ? (
            <ul className="inventory-edit-list">
              {editedCharacter.inventory.map((item, index) => (
                <li key={index} className="inventory-edit-item">
                  <input
                    type="text"
                    value={item}
                    onChange={(e) => handleInventoryChange(index, e.target.value)}
                  />
                  <button 
                    type="button" 
                    className="remove-item-btn"
                    onClick={() => removeInventoryItem(index)}
                  >
                    ×
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p>No items in inventory</p>
          )}
          <button 
            type="button" 
            className="add-item-btn"
            onClick={addInventoryItem}
          >
            Add Item
          </button>
        </div>
      </div>
    </div>
  );
};

export default CharacterPanel;
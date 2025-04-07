import React from 'react';
import './ModelSelector.css';

const ModelSelector = ({ models, selectedModel, onSelectModel }) => {
  if (!models || Object.keys(models).length === 0) {
    return null;
  }

  return (
    <div className="model-selector">
      <label htmlFor="model-select">AI Model:</label>
      <select 
        id="model-select"
        value={selectedModel}
        onChange={(e) => onSelectModel(e.target.value)}
      >
        {Object.entries(models).map(([id, model]) => (
          <option key={id} value={id}>
            {model.description || id}
          </option>
        ))}
      </select>
    </div>
  );
};

export default ModelSelector;
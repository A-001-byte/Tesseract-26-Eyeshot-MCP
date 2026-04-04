import React from 'react';
import { useAppContext } from '../../context/AppContext.jsx';

const LeftPanel = () => {
  const { entities, selectedEntity, selectEntity } = useAppContext();

  return (
    <div className="left-panel">
      <div className="panel-header">Scene</div>
      <div className="panel-content">
        <ul className="scene-list">
          {entities.map((entity, index) => (
            <li 
              key={entity.id || index} 
              className={`scene-item ${selectedEntity?.id === entity.id ? 'selected' : ''}`}
              onClick={() => selectEntity(entity)}
            >
              <span className="tree-label">{entity.name}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default LeftPanel;

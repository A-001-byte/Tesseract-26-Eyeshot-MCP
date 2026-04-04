import React from 'react';
import { useAppContext } from '../../context/AppContext.jsx';

const Viewport = () => {
  const { entities, selectEntity, selectedEntity } = useAppContext();

  return (
    <div className="viewport">
      <div className="viewport-overlay">3D Viewport</div>
      <div className="viewport-items">
        {entities.map((entity, index) => (
          <div 
            key={entity.id || index} 
            className={`viewport-item ${selectedEntity?.id === entity.id ? 'selected' : ''}`}
            onClick={(e) => {
              e.stopPropagation();
              selectEntity(entity);
            }}
          >
            {entity.name || `Entity ${index + 1}`}
          </div>
        ))}
      </div>
    </div>
  );
};

export default Viewport;

import React from 'react';
import { useAppContext } from '../../context/AppContext.jsx';

const RightPanel = () => {
  const { selectedEntity } = useAppContext();

  return (
    <div className="right-panel">
      <div className="panel-header">Properties</div>
      <div className="panel-content">
        {!selectedEntity ? (
          <div className="no-selection">No selection</div>
        ) : (
          <>
            <div className="property-group">
              <div className="property-group-title">General</div>
              <div className="property-grid">
                <span className="property-label">Name:</span>
                <span className="property-value">{selectedEntity.name}</span>
                <span className="property-label">Type:</span>
                <span className="property-value">{selectedEntity.type}</span>
              </div>
            </div>

            <div className="property-group">
              <div className="property-group-title">Position</div>
              <div className="property-grid">
                <span className="property-label">X:</span>
                <span className="property-value">{selectedEntity.position?.x ?? 0}</span>
                <span className="property-label">Y:</span>
                <span className="property-value">{selectedEntity.position?.y ?? 0}</span>
                <span className="property-label">Z:</span>
                <span className="property-value">{selectedEntity.position?.z ?? 0}</span>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default RightPanel;

import React, { createContext, useState, useContext } from 'react';

const AppContext = createContext();

export const AppProvider = ({ children }) => {
  const [entities, setEntitiesState] = useState([]);
  const [selectedEntity, setSelectedEntity] = useState(null);

  const addEntity = (entity) => {
    setEntitiesState((prev) => [...prev, entity]);
  };

  const setEntities = (list) => {
    setEntitiesState(list);
  };

  const selectEntity = (entity) => {
    setSelectedEntity(entity);
  };

  const value = {
    entities,
    selectedEntity,
    addEntity,
    setEntities,
    selectEntity,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export const useAppContext = () => {
  return useContext(AppContext);
};

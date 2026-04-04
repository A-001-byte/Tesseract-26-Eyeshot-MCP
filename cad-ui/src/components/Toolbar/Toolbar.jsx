import { 
  createHexagon, 
  createCircle, 
  createRectangle, 
  extrude, 
  extrudeAdd, 
  extrudeRemove, 
  exportSTEP,
  getScene
} from '../../api/cadApi.js';
import { useAppContext } from '../../context/AppContext.jsx';

const Toolbar = () => {
  const { addEntity, selectEntity } = useAppContext();

  // Handlers
  const handleHexagon = async () => {
    try {
      const res = await createHexagon();
      console.log("Backend response:", res);
      
      addEntity(res);
      selectEntity(res);
    } catch (err) {
      console.error(err);
    }
  };

  const handleCircle = async () => {
    try {
      const res = await createCircle();
      console.log("Backend response:", res);
      
      addEntity(res);
      selectEntity(res);
    } catch (err) {
      console.error(err);
    }
  };

  const handleRectangle = async () => {
    try {
      const res = await createRectangle();
      console.log("Backend response:", res);
      
      addEntity(res);
      selectEntity(res);
    } catch (err) {
      console.error(err);
    }
  };

  const handleExtrude = async () => {
    try {
      const res = await extrude();
      console.log("Backend response:", res);
      
      addEntity(res);
      selectEntity(res);
    } catch (err) {
      console.error(err);
    }
  };

  const handleExtrudeAdd = async () => {
    try {
      const res = await extrudeAdd();
      console.log("Backend response:", res);
      
      addEntity(res);
      selectEntity(res);
    } catch (err) {
      console.error(err);
    }
  };

  const handleExtrudeRemove = async () => {
    try {
      const res = await extrudeRemove();
      console.log("Backend response:", res);
      
      addEntity(res);
      selectEntity(res);
    } catch (err) {
      console.error(err);
    }
  };

  const handleExport = async () => {
    try {
      const res = await exportSTEP();
      console.log("Backend response:", res);
    } catch (err) {
      console.error(err);
    }
  };

  const handleAction = (actionName) => {
    console.log(`${actionName} clicked`);
  };

  return (
    <div className="toolbar">
      <div className="toolbar-group">
        <button onClick={handleHexagon} className="toolbar-btn">Hexagon</button>
        <button onClick={handleCircle} className="toolbar-btn">Circle</button>
        <button onClick={handleRectangle} className="toolbar-btn">Rectangle</button>
      </div>
      <div className="toolbar-divider"></div>
      
      <div className="toolbar-group">
        <button onClick={handleExtrude} className="toolbar-btn">Extrude</button>
        <button onClick={handleExtrudeAdd} className="toolbar-btn">Add</button>
        <button onClick={handleExtrudeRemove} className="toolbar-btn">Remove</button>
      </div>
      <div className="toolbar-divider"></div>

      <div className="toolbar-group">
        <button onClick={() => handleAction('Move')} className="toolbar-btn">Move</button>
        <button onClick={() => handleAction('Rotate')} className="toolbar-btn">Rotate</button>
      </div>
      <div className="toolbar-divider"></div>

      <div className="toolbar-group">
        <button onClick={handleExport} className="toolbar-btn">STEP</button>
      </div>
    </div>
  );
};

export default Toolbar;

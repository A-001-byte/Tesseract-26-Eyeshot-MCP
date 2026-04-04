import React from 'react';
import Toolbar from '../components/Toolbar/Toolbar.jsx';
import LeftPanel from '../components/LeftPanel/LeftPanel.jsx';
import RightPanel from '../components/RightPanel/RightPanel.jsx';
import AIPanel from '../components/AIPanel/AIPanel.jsx';
import BottomPanel from '../components/BottomPanel/BottomPanel.jsx';
import Viewport from '../components/Viewport/Viewport.jsx';

const MainLayout = () => {
  return (
    <div className="main-container">
      <Toolbar />
      <div className="content">
        <LeftPanel />
        <Viewport />
        <div className="right-sidebar">
          <RightPanel />
          <AIPanel />
        </div>
      </div>
      <BottomPanel />
    </div>
  );
};

export default MainLayout;

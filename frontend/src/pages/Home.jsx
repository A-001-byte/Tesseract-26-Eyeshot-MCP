import React from 'react';
import ChatBox from '../components/ChatBox';
import Viewer from '../components/Viewer';

export default function Home() {
  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw' }}>
      <div style={{ width: '30%', borderRight: '1px solid #ccc' }}>
        <ChatBox />
      </div>
      <div style={{ width: '70%' }}>
        <Viewer />
      </div>
    </div>
  );
}

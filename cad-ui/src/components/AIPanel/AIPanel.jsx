import React, { useState } from 'react';
import { 
  sendMessage, 
  createHexagon, 
  createCircle, 
  createRectangle, 
  extrude, 
  extrudeAdd, 
  extrudeRemove 
} from '../../api/cadApi.js';
import { useAppContext } from '../../context/AppContext.jsx';

const AIPanel = () => {
  const { addEntity, selectEntity } = useAppContext();
  const [messages, setMessages] = useState([
    { role: 'assistant', text: 'Hello! I am your CAD assistant. How can I help you today?' }
  ]);
  const [input, setInput] = useState('');

  const handleSend = async () => {
    if (!input.trim()) return;
    
    const userPrompt = input;
    setInput('');
    
    // Add user message to UI
    setMessages(prev => [...prev, { role: 'user', text: userPrompt }]);
    
    // Call AI API
    const response = await sendMessage(userPrompt);
    
    // Add AI text response to UI
    setMessages(prev => [...prev, { 
      role: response.role || 'assistant', 
      text: response.text || response.message || 'No response from AI'
    }]);

    // Handle CAD Actions
    if (response.action) {
      let actionResult = null;
      
      switch (response.action) {
        case 'createHexagon': actionResult = await createHexagon(); break;
        case 'createCircle': actionResult = await createCircle(); break;
        case 'createRectangle': actionResult = await createRectangle(); break;
        case 'extrude': actionResult = await extrude(); break;
        case 'extrudeAdd': actionResult = await extrudeAdd(); break;
        case 'remove': actionResult = await extrudeRemove(); break;
        default: console.warn('Unknown action:', response.action);
      }

      if (actionResult) {
        addEntity(actionResult);
        selectEntity(actionResult);
      }
    }
  };

  return (
    <div className="ai-panel">
      <div className="panel-header">Assistant</div>
      <div className="ai-chat-area">
        {messages.map((msg, i) => (
          <div key={i} className={`chat-item ${msg.role}`}>
            <div className="chat-text">
              <strong>{msg.role === 'user' ? 'User: ' : 'Assistant: '}</strong>
              {msg.text}
            </div>
          </div>
        ))}
      </div>
      <div className="ai-input-container">
        <input 
          type="text" 
          className="ai-input" 
          placeholder="Ask..." 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
        />
        <button className="ai-send-btn" onClick={handleSend}>Send</button>
      </div>
    </div>
  );
};

export default AIPanel;

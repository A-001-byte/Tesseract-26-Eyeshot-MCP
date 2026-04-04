import React, { useState } from 'react';
import { sendInstruction } from '../services/api';

export default function ChatBox() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  const handleSend = async () => {
    if (!input.trim()) return;
    
    // Optimistic UI update
    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    
    try {
      // Call our MCP Backend
      const response = await sendInstruction(input);
      setMessages(prev => [...prev, { role: 'bot', content: JSON.stringify(response.result, null, 2) }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'bot', content: `Error: ${err.message}` }]);
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '1rem', boxSizing: 'border-box' }}>
      <h2>AI Assistant</h2>
      <div style={{ flex: 1, overflowY: 'auto', marginBottom: '1rem', background: '#f9f9f9', padding: '10px' }}>
        {messages.map((msg, i) => (
          <div key={i} style={{ marginBottom: '10px', textAlign: msg.role === 'user' ? 'right' : 'left' }}>
            <strong>{msg.role}: </strong>
            <pre style={{ display: 'inline-block', margin: 0, textAlign: 'left', whiteSpace: 'pre-wrap' }}>
              {msg.content}
            </pre>
          </div>
        ))}
      </div>
      <div style={{ display: 'flex' }}>
        <input 
          type="text" 
          value={input} 
          onChange={e => setInput(e.target.value)} 
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          style={{ flex: 1, padding: '10px' }}
          placeholder="e.g. Load the sample.step model"
        />
        <button onClick={handleSend} style={{ padding: '10px' }}>Send</button>
      </div>
    </div>
  );
}

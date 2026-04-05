import axios from 'axios';

// Call the Python MCP backend
const API_BASE = 'http://localhost:8000/api/v1/tools';

export const sendInstruction = async (instruction) => {
  try {
    const response = await axios.post(`${API_BASE}/execute`, { instruction });
    return response.data;
  } catch (error) {
    console.error('API Error:', error);
    throw new Error(error.response?.data?.detail || 'Failed to connect to MCP server');
  }
};

export const PORTS = {
    FRONTEND: 3000,
    BACKEND_MCP: 8000,
    LLM_SERVICE: 8001,
    CAD_ENGINE: 5000
};

export const API_BASE_URLS = {
    MCP: `http://localhost:${PORTS.BACKEND_MCP}/api/v1`,
    LLM: `http://localhost:${PORTS.LLM_SERVICE}/api/v1`,
    CAD: `http://localhost:${PORTS.CAD_ENGINE}/api/cad`
};

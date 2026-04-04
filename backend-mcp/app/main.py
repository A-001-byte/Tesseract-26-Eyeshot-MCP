from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.routes import tools
from app.utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(title="AI CAD MCP Server", version="1.0.0")

# Allow requests from our frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the endpoints that serve as our MCP entry points/tools
app.include_router(tools.router, prefix="/api/v1/tools", tags=["MCP Tools"])

@app.get("/")
async def root():
    return {"message": "MCP Server is running. Integrate with CAD Engine and LLM Service."}

if __name__ == "__main__":
    logger.info("Starting up MCP Server on port 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)

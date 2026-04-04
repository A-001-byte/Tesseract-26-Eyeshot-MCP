from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.routes import tools
from app.utils.logger import get_logger
from dotenv import load_dotenv

load_dotenv()

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

# Include endpoints for MCP tools and the chat orchestration flow
app.include_router(tools.router, tags=["MCP"])

@app.get("/")
async def root():
    return {"message": "MCP server running", "chat": "/chat", "tools": "/tools"}


@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    logger.info("Starting up MCP Server on port 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)

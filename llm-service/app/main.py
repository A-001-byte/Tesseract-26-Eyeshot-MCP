from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.services.llm_client import call_llm
from app.services.parser import enforce_json_output
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LLM Parsing Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ParseRequest(BaseModel):
    prompt: str

@app.post("/api/v1/parse")
async def parse_instruction(request: ParseRequest):
    """
    Takes natural language, calls LLM, and enforces JSON schema.
    """
    logger.info(f"Parsing instruction: {request.prompt}")
    try:
        # Call LLM
        raw_llm_response = await call_llm(request.prompt)
        # Enforce JSON
        structured_json = enforce_json_output(raw_llm_response)
        
        return {"status": "success", "structured_command": structured_json}
    except Exception as e:
        logger.error(f"Error parsing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)

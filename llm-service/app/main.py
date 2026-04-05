import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from app.services.llm_client import call_llm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LLM Parsing Service", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ParseRequest(BaseModel):
    prompt: str

class GenerateCommandRequest(BaseModel):
    input: str


# ── Main parse endpoint (used by backend-mcp command router) ──────────────

@app.post("/parse")
async def parse_command(request: Request):
    body = await request.json()
    user_message = body.get("message", "") or body.get("prompt", "") or body.get("input", "")
    if not user_message.strip():
        return JSONResponse(status_code=400, content={"error": "empty prompt"})
    request_id = str(uuid.uuid4())
    logger.info("parse request_id=%s prompt=%s", request_id, user_message[:80])
    result = call_llm(user_message)
    logger.info("parse result request_id=%s command=%s", request_id, result.get("command"))
    return result


@app.post("/api/v1/parse")
async def parse_v1(request: Request):
    body = await request.json()
    user_message = body.get("message", "") or body.get("prompt", "") or body.get("input", "")
    if not user_message.strip():
        return JSONResponse(status_code=400, content={"error": "empty prompt"})
    result = call_llm(user_message)
    return result


@app.post("/generate-command")
async def generate_command(request: Request):
    body = await request.json()
    user_message = body.get("input", "") or body.get("prompt", "") or body.get("message", "")
    if not user_message.strip():
        return JSONResponse(status_code=400, content={"error": "empty input"})
    request_id = str(uuid.uuid4())
    logger.info("generate-command request_id=%s input=%s", request_id, user_message[:80])
    result = call_llm(user_message)
    logger.info("generate-command result request_id=%s name=%s", request_id, result.get("name"))
    return result


# ── Health & Test ─────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/test-llm")
async def test_llm():
    try:
        result = call_llm("make a ball bearing")
        return {"test_input": "make a ball bearing", "llm_output": result}
    except Exception as e:
        import traceback
        return {"test_input": "make a ball bearing", "error": str(e), "trace": traceback.format_exc()}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7000)

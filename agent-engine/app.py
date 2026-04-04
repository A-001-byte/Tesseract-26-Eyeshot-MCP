from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from orchestrator import execute_plan
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="Agent Engine API")

# Enable CORS for the dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from agents.planner import generate_plan
import json

class PromptRequest(BaseModel):
    prompt: str

@app.post("/api/v1/agent/run")
async def run_agent(request: PromptRequest):
    try:
        # 1. Planner Agent
        plan = generate_plan(request.prompt)
        
        # 2. Execution flow (includes Validator & Executor)
        execution = execute_plan(plan, user_prompt=request.prompt)
        
        return {
            "plan": plan,
            "results": execution["results"],
            "review": execution["review"]
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)

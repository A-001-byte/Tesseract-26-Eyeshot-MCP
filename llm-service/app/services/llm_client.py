import os
import httpx
from app.services.prompt_templates import SYSTEM_PROMPT

# Optional depending on whether you use litellm, google-genai, etc.  
# For hackathon, doing a raw simulated call or a basic request is fine if key is missing.

async def call_llm(user_prompt: str) -> str:
    """
    Calls Gemini/GPT. 
    Placeholder logic returns static JSON wrapped in text, representing LLM output.
    """
    # Example for Gemini using HTTP instead of bloated SDK for a clean API
    api_key = os.getenv("LLM_API_KEY", "")
    
    # Fake LLM logic for scaffolding
    print(f"Calling LLM with system prompt and user prompt: {user_prompt}")
    
    if "load" in user_prompt.lower():
        # Simulated raw LLM text that parser will need to extract
        return '```json\n{\n  "action": "load_model",\n  "file_path": "sample.step"\n}\n```'
        
    return '```json\n{\n  "action": "unknown",\n  "error": "Could not map instruction"\n}\n```'

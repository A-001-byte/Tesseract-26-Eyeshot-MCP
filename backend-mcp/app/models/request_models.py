from pydantic import BaseModel

class CommandRequest(BaseModel):
    instruction: str
    # Possible session_id or user contexts
    # session_id: Optional[str] = None

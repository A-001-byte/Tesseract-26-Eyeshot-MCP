from pydantic import BaseModel, Field


class LoadModelRequest(BaseModel):
    filePath: str = Field(..., min_length=1)


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1)

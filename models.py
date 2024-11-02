from pydantic import BaseModel

class GenerateResponse(BaseModel):
    sessionId: str
    response: str
    history: list

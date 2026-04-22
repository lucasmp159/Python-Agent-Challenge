from fastapi import FastAPI
from pydantic import BaseModel
from app.orchestrator import run

app = FastAPI()

class MessageRequest(BaseModel):
    message: str
    session_id: str | None = None

@app.post("/messages")
async def messages(req: MessageRequest):
    if not req.message or not req.message.strip():
        # validação leve no endpoint
        return {"answer": "Não encontrei informação suficiente na base para responder essa pergunta.", "sources": []}
    
    result = await run(req.message, req.session_id)
    return result
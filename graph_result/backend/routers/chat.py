from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Any
from agent.langgraph_agent import invoke_agent

router = APIRouter()

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    response: str
    cypher: Optional[str] = None
    intent: str
    results: Optional[List[dict]] = None
    table: Optional[List[dict]] = None   # Validated flat table rows
    error: Optional[str] = None

@router.post("", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    try:
        result = invoke_agent(req.query)
        return ChatResponse(
            response=result.get("response", "Could not generate a valid response.") or "Could not generate a valid response.",
            cypher=result.get("cypher_query"),
            intent=result.get("intent") or "general",
            results=result.get("results"),
            table=result.get("table"),
            error=result.get("error")
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

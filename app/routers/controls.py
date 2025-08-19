from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from ..auth import get_current_user
from ..models import AgentResponse, ControlSelection
from ..langgraph_agent import iso_agent
from ..database import mongodb

router = APIRouter()

class ChatRequest(BaseModel):
    query: str

@router.post("/chat", response_model=AgentResponse)
async def chat_with_agent(request: ChatRequest, user = Depends(get_current_user)):
    try:
        result = await iso_agent.run(request.query, user["username"])
        
        return AgentResponse(
            response=result["final_response"],
            controls=result.get("generated_controls", []),
            pending_selection=result.get("pending_selection", False),
            session_id=result.get("session_id", "")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/select-controls")
async def select_controls(selection: ControlSelection, user = Depends(get_current_user)):
    try:
        result = await iso_agent.run(
            "", 
            user["username"], 
            selected_controls=selection.selected_control_ids,
            session_id=selection.session_id
        )
        
        return AgentResponse(
            response=result["final_response"],
            pending_selection=False
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user-controls")
async def get_user_controls(user = Depends(get_current_user)):
    try:
        controls = list(mongodb.controls.find({"user_id": user["username"]}))
        for control in controls:
            if "_id" in control:
                control["_id"] = str(control["_id"])
        return {"controls": controls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/controls-by-risk/{risk_id}")
async def get_controls_by_risk(risk_id: str, user = Depends(get_current_user)):
    try:
        controls = mongodb.get_controls_by_risk(risk_id, user["username"])
        return {"controls": controls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
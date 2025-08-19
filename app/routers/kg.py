from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from ..auth import get_current_user
from ..neo4j_db import neo4j_service
from ..database import mongodb

router = APIRouter()

class InitializeUserRequest(BaseModel):
    sync_existing_data: bool = True

@router.post("/initialize-user")
async def initialize_user_in_kg(request: InitializeUserRequest, user = Depends(get_current_user)):
    try:
        user_data = {
            "user_id": user["username"],
            "username": user["username"],
            "organization_name": user.get("organization_name", ""),
            "location": user.get("location", ""),
            "domain": user.get("domain", "")
        }
        
        neo4j_service.create_user_node(user_data)
        
        if request.sync_existing_data:
            risks = mongodb.get_user_risks(user["username"])
            for risk in risks:
                neo4j_service.create_risk_node({
                    "id": str(risk["_id"]),
                    "description": risk["description"],
                    "category": risk["category"],
                    "likelihood": risk["likelihood"],
                    "impact": risk["impact"],
                    "user_id": user["username"]
                })
            
            controls = list(mongodb.controls.find({"user_id": user["username"]}))
            for control in controls:
                neo4j_service.create_control_node({
                    "id": str(control["_id"]),
                    "control_id": control["control_id"],
                    "title": control["title"],
                    "description": control["description"],
                    "domain_category": control["domain_category"],
                    "annex_reference": control["annex_reference"],
                    "user_id": control["user_id"],
                    "risk_id": control["risk_id"]
                })
        
        return {"message": "User initialized in knowledge graph", "synced_data": request.sync_existing_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user-stats")
async def get_user_stats(user = Depends(get_current_user)):
    try:
        stats = neo4j_service.get_user_risk_control_stats(user["username"])
        return {"stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/similar-controls/{domain}/{risk_category}")
async def get_similar_controls_by_domain(domain: str, risk_category: str, user = Depends(get_current_user)):
    try:
        controls = neo4j_service.get_similar_controls_by_domain(domain, risk_category)
        return {"controls": controls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/controls-by-annex/{annex}/{risk_category}")
async def get_controls_by_annex_category(annex: str, risk_category: str, user = Depends(get_current_user)):
    try:
        controls = neo4j_service.get_controls_by_annex_and_category(annex, risk_category)
        return {"controls": controls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/initialize-iso-annexes")
async def initialize_iso_annexes():
    try:
        neo4j_service.initialize_iso_annexes()
        return {"message": "ISO Annexes initialized"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
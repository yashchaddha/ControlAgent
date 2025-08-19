from fastapi import APIRouter, Depends, HTTPException
from ..auth import get_current_user
from ..database import mongodb
from ..rag_service import rag_service
from ..neo4j_db import neo4j_service
from typing import List, Dict

router = APIRouter()

def convert_objectid(obj):
    if isinstance(obj, dict):
        return {key: convert_objectid(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        return convert_objectid(obj.__dict__)
    elif str(type(obj)) == "<class 'bson.objectid.ObjectId'>":
        return str(obj)
    else:
        return obj

def get_user_risks_from_collection(user_id: str) -> List[Dict]:
    risks_docs = list(mongodb.risks.find({"user_id": user_id}))
    all_risks = []
    
    for doc in risks_docs:
        doc = convert_objectid(doc)
        
        if "risks" in doc and isinstance(doc["risks"], list):
            for risk in doc["risks"]:
                risk = convert_objectid(risk)
                risk["user_id"] = doc["user_id"]
                risk["organization_name"] = doc.get("organization_name", "")
                risk["location"] = doc.get("location", "")
                risk["domain"] = doc.get("domain", "")
                
                if "id" not in risk:
                    if "_id" in risk:
                        risk["id"] = str(risk["_id"])
                    else:
                        risk["id"] = str(doc.get("_id", ""))
                
                if "_id" in risk:
                    del risk["_id"]
                
                all_risks.append(risk)
        else:
            if "_id" in doc:
                doc["id"] = str(doc["_id"])
                del doc["_id"]
            all_risks.append(doc)
    
    return all_risks

def get_risks_without_controls(user_id: str) -> List[Dict]:
    all_risks = get_user_risks_from_collection(user_id)
    existing_control_risk_ids = set(str(rid) for rid in mongodb.controls.distinct("risk_id", {"user_id": user_id}))
    
    risks_without_controls = []
    for risk in all_risks:
        risk_id = risk.get("id", "")
        if risk_id not in existing_control_risk_ids:
            risks_without_controls.append(risk)
    
    return risks_without_controls

@router.get("/")
async def get_user_risks(user = Depends(get_current_user)):
    try:
        risks = get_user_risks_from_collection(user["username"])
        return {"risks": risks, "total": len(risks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/without-controls")
async def get_risks_without_controls_endpoint(user = Depends(get_current_user)):
    try:
        risks = get_risks_without_controls(user["username"])
        return {"risks": risks, "total": len(risks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{risk_id}")
async def get_risk_by_id(risk_id: str, user = Depends(get_current_user)):
    try:
        all_risks = get_user_risks_from_collection(user["username"])
        risk = next((r for r in all_risks if r.get("id") == risk_id), None)
        
        if not risk:
            raise HTTPException(status_code=404, detail="Risk not found")
        
        return {"risk": risk}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{risk_id}/embed")
async def create_risk_embedding(risk_id: str, user = Depends(get_current_user)):
    try:
        all_risks = get_user_risks_from_collection(user["username"])
        risk = next((r for r in all_risks if r.get("id") == risk_id), None)
        
        if not risk:
            raise HTTPException(status_code=404, detail="Risk not found")
        
        rag_service.store_risk_embedding(risk)
        neo4j_service.create_risk_node({
            "id": risk_id,
            "description": risk.get("description", ""),
            "category": risk.get("category", ""),
            "likelihood": risk.get("likelihood", ""),
            "impact": risk.get("impact", ""),
            "user_id": user["username"]
        })
        
        return {"message": "Risk embedded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/category/{category}")
async def get_risks_by_category(category: str, user = Depends(get_current_user)):
    try:
        all_risks = get_user_risks_from_collection(user["username"])
        filtered_risks = [r for r in all_risks if r.get("category") == category]
        return {"risks": filtered_risks, "category": category, "total": len(filtered_risks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/")
async def get_risk_documents(user = Depends(get_current_user)):
    try:
        risk_docs = list(mongodb.risks.find({"user_id": user["username"]}))
        
        for doc in risk_docs:
            doc = convert_objectid(doc)
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])
            
            if "risks" in doc and isinstance(doc["risks"], list):
                for risk in doc["risks"]:
                    risk = convert_objectid(risk)
                    if "_id" in risk:
                        risk["_id"] = str(risk["_id"])
        
        return {"documents": risk_docs, "total": len(risk_docs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
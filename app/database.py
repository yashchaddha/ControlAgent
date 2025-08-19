from pymongo import MongoClient
from .config import MONGODB_URI, DATABASE_NAME, COLLECTIONS
from typing import Dict, List, Optional
from bson import ObjectId
import uuid

def convert_objectid(obj):
    if isinstance(obj, dict):
        return {key: convert_objectid(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_objectid(item) for item in obj]
    elif isinstance(obj, ObjectId):
        return str(obj)
    else:
        return obj

class MongoDBService:
    def __init__(self):
        self.client = MongoClient(MONGODB_URI)
        self.db = self.client[DATABASE_NAME]
        self.users = self.db[COLLECTIONS["users"]]
        self.risks = self.db[COLLECTIONS["risks"]]
        self.controls = self.db[COLLECTIONS["controls"]]
        self.sessions = self.db[COLLECTIONS["sessions"]]

    def get_user_context(self, user_id: str) -> Dict:
        return self.users.find_one({"username": user_id})

    def get_user_risks(self, user_id: str, exclude_with_controls: bool = False) -> List[Dict]:
        risk_docs = list(self.risks.find({"user_id": user_id}))
        all_risks = []
        
        for doc in risk_docs:
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
        
        if exclude_with_controls:
            risk_ids_with_controls = set(str(rid) for rid in self.controls.distinct("risk_id", {"user_id": user_id}))
            all_risks = [r for r in all_risks if r.get("id") not in risk_ids_with_controls]
        
        return all_risks

    def get_risk_by_id(self, risk_id: str, user_id: str) -> Optional[Dict]:
        risk_docs = list(self.risks.find({"user_id": user_id}))
        
        for doc in risk_docs:
            doc = convert_objectid(doc)
            
            if "risks" in doc and isinstance(doc["risks"], list):
                for risk in doc["risks"]:
                    risk = convert_objectid(risk)
                    
                    risk_current_id = risk.get("id", str(risk.get("_id", "")))
                    
                    if risk_current_id == risk_id:
                        risk["user_id"] = doc["user_id"]
                        risk["organization_name"] = doc.get("organization_name", "")
                        risk["location"] = doc.get("location", "")
                        risk["domain"] = doc.get("domain", "")
                        
                        if "id" not in risk:
                            risk["id"] = risk_current_id
                        
                        if "_id" in risk:
                            del risk["_id"]
                        
                        return risk
            else:
                if str(doc.get("_id", "")) == risk_id:
                    if "_id" in doc:
                        doc["id"] = str(doc["_id"])
                        del doc["_id"]
                    return doc
        
        return None

    def get_controls_by_risk(self, risk_id: str, user_id: str) -> List[Dict]:
        return list(self.controls.find({"risk_id": risk_id, "user_id": user_id}))

    def get_controls_by_category(self, category: str, user_id: str) -> List[Dict]:
        all_risks = self.get_user_risks(user_id)
        risk_ids = [r.get("id") for r in all_risks if r.get("category") == category]
        return list(self.controls.find({"risk_id": {"$in": risk_ids}, "user_id": user_id}))

    def get_controls_by_annex(self, annex: str, user_id: str) -> List[Dict]:
        return list(self.controls.find({"annex_reference": {"$regex": f"^{annex}"}, "user_id": user_id}))

    def save_controls(self, controls: List[Dict]) -> List[str]:
        control_ids = []
        for control in controls:
            control["_id"] = str(uuid.uuid4())
            control_ids.append(control["_id"])
            self.controls.insert_one(control)
        return control_ids

    def save_session(self, session_data: Dict) -> str:
        session_id = str(uuid.uuid4())
        session_data["_id"] = session_id
        self.sessions.insert_one(session_data)
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        return self.sessions.find_one({"_id": session_id})

    def update_session(self, session_id: str, data: Dict):
        self.sessions.update_one({"_id": session_id}, {"$set": data})

mongodb = MongoDBService()
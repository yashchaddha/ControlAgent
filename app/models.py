from typing import Dict, List, Optional, TypedDict, Literal
from pydantic import BaseModel
from datetime import datetime

class AgentState(TypedDict):
    user_query: str
    user_id: str
    user_context: Dict
    intent: str
    parameters: Dict
    retrieved_context: Dict
    generated_controls: List[Dict]
    selected_controls: List[str]
    conversation_history: List[Dict]
    final_response: str
    pending_selection: bool
    session_id: str

class FinalizedRisk(BaseModel):
    id: Optional[str] = None
    description: str
    category: str
    likelihood: str
    impact: str
    treatment_strategy: str
    asset_value: Optional[str] = None
    department: Optional[str] = None
    risk_owner: Optional[str] = None
    security_impact: Optional[str] = None
    target_date: Optional[str] = None
    risk_progress: Optional[str] = "Identified"
    residual_exposure: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Control(BaseModel):
    id: Optional[str] = None
    control_id: str
    title: str
    description: str
    domain_category: str
    annex_reference: str
    control_statement: str
    implementation_guidance: str
    risk_id: str
    user_id: str
    created_at: Optional[datetime] = None

class ControlSelection(BaseModel):
    session_id: str
    selected_control_ids: List[str]

class FinalizedRisks(BaseModel):
    id: Optional[str] = None
    user_id: str
    organization_name: str
    location: str
    domain: str
    risks: List[FinalizedRisk]
    total_risks: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class AgentResponse(BaseModel):
    response: str
    controls: Optional[List[Control]] = None
    pending_selection: bool = False
    session_id: Optional[str] = None
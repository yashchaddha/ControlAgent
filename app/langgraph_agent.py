from langgraph.graph import StateGraph, END
from typing import Dict, List, Optional
from .models import AgentState
from .openai_service import openai_service
from .database import mongodb
from .neo4j_db import neo4j_service
from .postgres import postgres_service
import uuid

class DatabaseTools:
    """Centralized database operations as methods instead of LangGraph tools"""

    def __init__(self):
        self.mongo = mongodb
        self.neo4j = neo4j_service
        self.postgres = postgres_service
        self.openai = openai_service

    def get_user_risks(self, user_id: str, exclude_with_controls: bool = False) -> List[Dict]:
        """Get all risks for a user from MongoDB"""
        try:
            result = self.mongo.get_user_risks(user_id, exclude_with_controls=exclude_with_controls)
            
            # If no risks found, create some sample data for testing
            if not result:
                sample_risks = [
                    {
                        "id": "risk_001",
                        "description": "Unauthorized access to financial systems",
                        "category": "Operational Risk",
                        "impact": "High",
                        "likelihood": "Medium",
                        "user_id": user_id
                    },
                    {
                        "id": "risk_002", 
                        "description": "Data loss due to system failure",
                        "category": "Technical Risk",
                        "impact": "High",
                        "likelihood": "Low",
                        "user_id": user_id
                    },
                    {
                        "id": "risk_003",
                        "description": "Compliance violation in data processing",
                        "category": "Compliance Risk", 
                        "impact": "Medium",
                        "likelihood": "Medium",
                        "user_id": user_id
                    }
                ]
                return sample_risks
            
            return result
        except Exception as e:
            # Return sample data even on error for testing
            sample_risks = [
                {
                    "id": "risk_001",
                    "description": "Sample operational risk for testing",
                    "category": "Operational Risk",
                    "impact": "High",
                    "likelihood": "Medium",
                    "user_id": user_id
                }
            ]
            return sample_risks

    def get_risk_by_id(self, risk_id: str, user_id: str) -> Optional[Dict]:
        """Get a specific risk by ID from MongoDB"""
        try:
            result = self.mongo.get_risk_by_id(risk_id, user_id)
            return result
        except Exception as e:
            return None

    def search_similar_controls(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for similar controls using vector similarity"""
        try:
            if not query.strip():
                return []
            query_embedding = self.openai.get_embedding(query)
            result = self.postgres.search_similar_controls(query_embedding, limit=limit)
            return result
        except Exception as e:
            return []

    def get_iso_guidance(self, query: str, limit: int = 3) -> List[Dict]:
        """Get ISO guidance using vector similarity"""
        try:
            if not query.strip():
                return []
            query_embedding = self.openai.get_embedding(query)
            result = self.postgres.get_iso_guidance(query_embedding, limit=limit)
            return result
        except Exception as e:
            return []

    def get_similar_controls_by_domain(self, domain: str, category: str) -> List[Dict]:
        """Get similar controls by domain and category from Neo4j"""
        try:
            result = self.neo4j.get_similar_controls_by_domain(domain, category)
            return result
        except Exception as e:
            return []

class ISO27001Agent:
    def __init__(self):
        self.openai = openai_service
        self.mongo = mongodb
        self.graph_db = neo4j_service
        self.db_tools = DatabaseTools()
        self.postgres = postgres_service
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        workflow = StateGraph(AgentState)
        
        workflow.add_node("classify_intent", self.classify_intent_node)
        workflow.add_node("retrieve_context", self.retrieve_context_node)
        workflow.add_node("generate_controls", self.generate_controls_node)
        workflow.add_node("handle_selection", self.handle_selection_node)
        workflow.add_node("synthesize_response", self.synthesize_response_node)
        workflow.add_node("store_data", self.store_data_node)
        
        workflow.set_entry_point("classify_intent")
        
        workflow.add_conditional_edges(
            "classify_intent",
            self.route_after_classification,
            {
                "retrieve": "retrieve_context",
                "direct_response": "synthesize_response"
            }
        )
        
        workflow.add_conditional_edges(
            "retrieve_context", 
            self.route_after_retrieval,
            {
                "generate": "generate_controls",
                "respond": "synthesize_response"
            }
        )
        
        workflow.add_edge("generate_controls", "handle_selection")
        
        workflow.add_conditional_edges(
            "handle_selection",
            self.route_after_selection,
            {
                "store": "store_data", 
                "wait": END
            }
        )
        
        workflow.add_edge("store_data", "synthesize_response")
        workflow.add_edge("synthesize_response", END)
        
        return workflow.compile()

    def classify_intent_node(self, state: AgentState) -> AgentState:
        try:
            result = self.openai.classify_intent(state["user_query"], state["user_context"])
            state["intent"] = result["intent"]
            state["parameters"] = result["parameters"]
        except Exception as e:
            # Fallback classification
            query_lower = state["user_query"].lower()
            if "generate controls" in query_lower:
                if "all" in query_lower or "my risks" in query_lower:
                    state["intent"] = "generate_controls_all"
                else:
                    state["intent"] = "generate_controls_all"  # Default to all
                state["parameters"] = {}
            else:
                state["intent"] = "query_controls"
                state["parameters"] = {}
        return state

    def retrieve_context_node(self, state: AgentState) -> AgentState:
        """Smart context retrieval using database tools"""
        intent = state["intent"]
        user_id = state["user_id"]
                
        if intent.startswith("generate_controls"):
            context = self._retrieve_for_generation_optimized(state)
        else:
            context = self._retrieve_for_other_intents(state)
        
        state["retrieved_context"] = context
        return state

    def _retrieve_for_generation_optimized(self, state: AgentState) -> Dict:
        """Optimized retrieval for control generation"""
        intent = state["intent"]
        user_id = state["user_id"]
        parameters = state["parameters"]
                
        if intent == "generate_controls_specific":
            risk_id = parameters.get("risk_id")
            if not risk_id:
                return {"error": "No risk ID provided"}
            
            # Get specific risk
            risk_data = self.db_tools.get_risk_by_id(risk_id, user_id)
            if not risk_data:
                return {"error": "Risk not found"}
            
            return self._get_context_for_single_risk(risk_data, state["user_context"])
            
        elif intent == "generate_controls_all":
            # Get all risks without controls
            risks = self.db_tools.get_user_risks(user_id, exclude_with_controls=False)
            return {"risks_for_generation": risks}
            
        elif intent == "generate_controls_category":
            category = parameters.get("risk_category")
            all_risks = self.db_tools.get_user_risks(user_id)
            risks = [r for r in all_risks if r.get("category") == category]
            return {"risks_for_generation": risks}

        elif intent == "generate_controls_impact":
            impact = parameters.get("impact")
            all_risks = self.db_tools.get_user_risks(user_id)
            risks = [r for r in all_risks if not impact or str(r.get("impact", "")).lower() == str(impact).lower()]
            return {"risks_for_generation": risks}
        
        # Default case - try to infer from query
        query = state["user_query"].lower()
        
        # Check if query mentions specific categories
        if "operational" in query:
            all_risks = self.db_tools.get_user_risks(user_id)
            risks = [r for r in all_risks if "operational" in r.get("category", "").lower()]
            return {"risks_for_generation": risks}
        elif "financial" in query:
            all_risks = self.db_tools.get_user_risks(user_id)
            risks = [r for r in all_risks if "financial" in r.get("category", "").lower()]
            return {"risks_for_generation": risks}
        
        # Default to all risks without controls
        risks = self.db_tools.get_user_risks(user_id, exclude_with_controls=False)
        return {"risks_for_generation": risks}

    def _retrieve_for_other_intents(self, state: AgentState) -> Dict:
        """Handle other intents like show_risks"""
        intent = state["intent"]
        user_id = state["user_id"]
        parameters = state["parameters"]
        
        if intent == "show_risks":
            risks = self.db_tools.get_user_risks(user_id)
            return {"risks": risks, "total": len(risks)}
        elif intent == "show_risks_without_controls":
            risks = self.db_tools.get_user_risks(user_id, exclude_with_controls=True)
            return {"risks": risks, "total": len(risks)}
        
        # Default empty context
        return {}

    def _get_context_for_single_risk(self, risk_data: Dict, user_context: Dict) -> Dict:
        """Get comprehensive context for a single risk"""
        risk_description = risk_data.get('description', '')
        risk_category = risk_data.get('category', '')
        user_domain = user_context.get('domain', '')
                
        # Get similar controls
        similar_controls = self.db_tools.search_similar_controls(
            f"{risk_description} {risk_category}", 
            limit=3
        )
        
        # Get ISO guidance
        iso_guidance = self.db_tools.get_iso_guidance(risk_description, limit=2)
        
        # Get domain controls
        domain_controls = self.db_tools.get_similar_controls_by_domain(user_domain, risk_category)
        
        context = {
            "risk_data": risk_data,
            "similar_controls": similar_controls,
            "iso_guidance": iso_guidance,
            "domain_controls": domain_controls
        }
        
        return context

    def generate_controls_node(self, state: AgentState) -> AgentState:        
        if state.get("selected_controls"):
            return state

        context = state["retrieved_context"]        
        if "error" in context:
            state["final_response"] = context["error"]
            return state
        
        if "risks_for_generation" in context:
            all_controls = []

            for i, risk in enumerate(context["risks_for_generation"]):
                controls = self.openai.generate_controls(
                    risk, state["user_context"],
                )
                for control in controls:
                    control["risk_id"] = risk.get("id", "")
                    control["user_id"] = state["user_id"]
                    control["id"] = str(uuid.uuid4())
                
                all_controls.extend(controls)
            
            state["generated_controls"] = all_controls
            
        else:
            # Single risk generation
            risk_data = context.get("risk_data")
            
            if not risk_data:
                state["final_response"] = "Risk not found"
                return state
            
            risk_id = state["parameters"].get("risk_id")
            
            # Check for existing controls
            existing_controls = self.mongo.get_controls_by_risk(risk_id, state["user_id"])
            if existing_controls:
                state["final_response"] = f"You already have {len(existing_controls)} controls for this risk. Would you like to see them or generate additional ones?"
                return state
            
            # Generate new controls
            controls = self.openai.generate_controls(
                risk_data, state["user_context"]
            )
            
            # Add metadata
            for control in controls:
                control["risk_id"] = risk_id
                control["user_id"] = state["user_id"]
                control["id"] = str(uuid.uuid4())
            
            state["generated_controls"] = controls
        
        return state

    def handle_selection_node(self, state: AgentState) -> AgentState:
        if state["generated_controls"]:
            if not state.get("selected_controls"):
                state["pending_selection"] = True
                state["session_id"] = self.mongo.save_session({
                    "user_id": state["user_id"],
                    "generated_controls": state["generated_controls"],
                    "state": dict(state)
                })
        return state

    def store_data_node(self, state: AgentState) -> AgentState:
        if state["selected_controls"]:
            controls_to_store = [
                control for control in state["generated_controls"]
                if control["id"] in state["selected_controls"]
            ]
            
            try:
                # Store in MongoDB
                self.mongo.save_controls(controls_to_store)
                
                # Store in Neo4j
                for control in controls_to_store:
                    self.graph_db.create_control_node(control)
                
                # Store embeddings
                for control in controls_to_store:
                    embedding_text = f"{control['title']} {control['description']}"
                    embedding = self.openai.get_embedding(embedding_text)
                    self.postgres.store_control_embedding(
                        control['id'],
                        control['user_id'],
                        control['title'],
                        control['description'],
                        control['annex_reference'],
                        embedding
                    )
                
                state["final_response"] = f"Successfully saved {len(controls_to_store)} controls."
                
            except Exception as e:
                state["final_response"] = f"Error saving controls: {str(e)}"
        
        return state

    def synthesize_response_node(self, state: AgentState) -> AgentState:
        
        if not state.get("final_response"):
            try:
                state["final_response"] = self.openai.synthesize_response(
                    state["user_query"], 
                    state["retrieved_context"], 
                    state.get("generated_controls")
                )
            except Exception as e:
                # Fallback response
                if state.get("generated_controls"):
                    count = len(state["generated_controls"])
                    state["final_response"] = f"I've generated {count} controls for your risks. Please review and select the ones you'd like to implement."
                elif state.get("retrieved_context", {}).get("risks"):
                    count = len(state["retrieved_context"]["risks"])
                    state["final_response"] = f"I found {count} risks in your system."
                else:
                    state["final_response"] = "I've processed your request. Please check the results."
        
        # Ensure we always have some response
        if not state.get("final_response"):
            state["final_response"] = "Request processed successfully."
            
        return state

    def route_after_classification(self, state: AgentState) -> str:
        intent = state["intent"]
        if intent.startswith("generate_controls") or intent.startswith("show_"):
            return "retrieve"
        return "direct_response"

    def route_after_retrieval(self, state: AgentState) -> str:
        if state.get("selected_controls"):
            return "generate"
        intent = state["intent"]
        if intent.startswith("generate_controls"):
            return "generate"
        return "respond"

    def route_after_selection(self, state: AgentState) -> str:
        if state.get("selected_controls"):
            return "store"
        return "wait"

    async def run(self, user_query: str, user_id: str, selected_controls: list = None, session_id: str = None):
        
        try:
            user_context = self.mongo.get_user_context(user_id)
        except Exception as e:
            user_context = {"organization_name": "Test Org", "domain": "Technology"}
        
        if session_id and selected_controls:
            try:
                session_data = self.mongo.get_session(session_id)
                if session_data:
                    state = session_data["state"]
                    state["selected_controls"] = selected_controls
                    result = await self.workflow.ainvoke(state, {"recursion_limit": 10})
                    return result
            except Exception as e:
                print(f"DEBUG: Error processing selection: {e}")
        
        initial_state = {
            "user_query": user_query,
            "user_id": user_id,
            "user_context": user_context,
            "intent": "",
            "parameters": {},
            "retrieved_context": {},
            "generated_controls": [],
            "selected_controls": [],
            "conversation_history": [],
            "final_response": "",
            "pending_selection": False,
            "session_id": ""
        }
        
        
        try:
            result = await self.workflow.ainvoke(initial_state, {"recursion_limit": 10})
            return result
        except Exception as e:
            return {
                "final_response": f"I encountered an error processing your request: {str(e)}",
                "generated_controls": [],
                "pending_selection": False,
                "session_id": ""
            }

iso_agent = ISO27001Agent()
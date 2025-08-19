from langgraph.graph import StateGraph, END
from typing import Dict
from .models import AgentState
from .openai_service import openai_service
from .rag_service import rag_service
from .database import mongodb
from .neo4j_db import neo4j_service
import uuid

class ISO27001Agent:
    def __init__(self):
        self.openai = openai_service
        self.rag = rag_service
        self.mongo = mongodb
        self.graph_db = neo4j_service
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
        result = self.openai.classify_intent(state["user_query"], state["user_context"])
        state["intent"] = result["intent"]
        state["parameters"] = result["parameters"]
        return state

    def retrieve_context_node(self, state: AgentState) -> AgentState:
        intent = state["intent"]
        user_id = state["user_id"]
        
        if intent.startswith("generate_controls"):
            context = self._retrieve_for_generation(state)
        else:
            context = self.rag.retrieve_context_for_query(
                state["user_query"], intent, state["parameters"], user_id
            )
        
        state["retrieved_context"] = context
        return state

    def _retrieve_for_generation(self, state: AgentState) -> Dict:
        intent = state["intent"]
        user_id = state["user_id"]
        parameters = state["parameters"]
        
        if intent == "generate_controls_specific":
            risk_id = parameters.get("risk_id")
            risk_data = self.mongo.get_risk_by_id(risk_id, user_id)
            if not risk_data:
                return {"error": "Risk not found"}
            return self.rag.retrieve_context_for_control_generation(risk_data, state["user_context"])
            
        elif intent == "generate_controls_all":
            risks = self.mongo.get_user_risks(user_id, exclude_with_controls=True)
            return {"risks_for_generation": risks}
            
        elif intent == "generate_controls_category":
            category = parameters.get("risk_category")
            all_risks = self.mongo.get_user_risks(user_id)
            risks = [r for r in all_risks if r.get("category") == category]
            return {"risks_for_generation": risks}
        
        return {}

    def generate_controls_node(self, state: AgentState) -> AgentState:
        context = state["retrieved_context"]
        
        if "error" in context:
            state["final_response"] = context["error"]
            return state
        
        if "risks_for_generation" in context:
            all_controls = []
            for risk in context["risks_for_generation"][:3]:  # Limit for demo
                risk_context = self.rag.retrieve_context_for_control_generation(risk, state["user_context"])
                controls = self.openai.generate_controls(
                    risk, state["user_context"], 
                    risk_context.get("similar_controls", []),
                    risk_context.get("iso_guidance", [])
                )
                for control in controls:
                    control["risk_id"] = risk.get("id", "")
                    control["user_id"] = state["user_id"]
                all_controls.extend(controls)
            state["generated_controls"] = all_controls
        else:
            risk_id = state["parameters"].get("risk_id")
            risk_data = self.mongo.get_risk_by_id(risk_id, state["user_id"])
            
            existing_controls = self.mongo.get_controls_by_risk(risk_id, state["user_id"])
            if existing_controls:
                state["final_response"] = f"You already have {len(existing_controls)} controls for this risk. Would you like to see them or generate additional ones?"
                return state
            
            controls = self.openai.generate_controls(
                risk_data, state["user_context"],
                context.get("similar_controls", []),
                context.get("iso_guidance", [])
            )
            
            for control in controls:
                control["risk_id"] = risk_id
                control["user_id"] = state["user_id"]
                control["id"] = str(uuid.uuid4())
            
            state["generated_controls"] = controls
        
        return state

    def handle_selection_node(self, state: AgentState) -> AgentState:
        if state["generated_controls"]:
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
            
            self.mongo.save_controls(controls_to_store)
            
            for control in controls_to_store:
                self.graph_db.create_control_node(control)
            
            self.rag.store_control_embeddings(controls_to_store)
            
            state["final_response"] = f"Successfully saved {len(controls_to_store)} controls."
        
        return state

    def synthesize_response_node(self, state: AgentState) -> AgentState:
        if not state.get("final_response"):
            state["final_response"] = self.openai.synthesize_response(
                state["user_query"], 
                state["retrieved_context"], 
                state.get("generated_controls")
            )
        return state

    def route_after_classification(self, state: AgentState) -> str:
        intent = state["intent"]
        if intent.startswith("generate_controls"):
            return "retrieve"
        return "retrieve"

    def route_after_retrieval(self, state: AgentState) -> str:
        intent = state["intent"]
        if intent.startswith("generate_controls"):
            return "generate"
        return "respond"

    def route_after_selection(self, state: AgentState) -> str:
        if state.get("selected_controls"):
            return "store"
        return "wait"

    async def run(self, user_query: str, user_id: str, selected_controls: list = None, session_id: str = None):
        user_context = self.mongo.get_user_context(user_id)
        
        if session_id and selected_controls:
            session_data = self.mongo.get_session(session_id)
            if session_data:
                state = session_data["state"]
                state["selected_controls"] = selected_controls
                result = await self.workflow.ainvoke(state, {"recursion_limit": 10})
                return result
        
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
        
        result = await self.workflow.ainvoke(initial_state, {"recursion_limit": 10})
        return result

iso_agent = ISO27001Agent()
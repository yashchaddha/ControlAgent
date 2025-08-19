from typing import Dict, List
from .openai_service import openai_service
from .postgres import postgres_service
from .neo4j_db import neo4j_service
from .database import mongodb

class RAGService:
    def __init__(self):
        self.openai = openai_service
        self.vector_db = postgres_service
        self.graph_db = neo4j_service
        self.mongo_db = mongodb

    def retrieve_context_for_control_generation(self, risk_data: Dict, user_context: Dict) -> Dict:
        risk_description = risk_data.get('description', '')
        risk_category = risk_data.get('category', '')
        user_domain = user_context.get('domain', '')
        
        # Try to get embeddings, but fallback gracefully if DB issues
        try:
            query_embedding = self.openai.get_embedding(risk_description)
            similar_risks = self.vector_db.search_similar_risks(query_embedding, limit=3)
            iso_guidance = self.vector_db.get_iso_guidance(query_embedding, limit=2)
        except Exception as e:
            print(f"Vector search failed, proceeding without: {e}")
            similar_risks = []
            iso_guidance = []
        
        # Try graph operations
        try:
            similar_controls = self.graph_db.get_similar_controls_by_domain(user_domain, risk_category)
        except Exception as e:
            print(f"Graph search failed, proceeding without: {e}")
            similar_controls = []
        
        return {
            "similar_risks": similar_risks,
            "similar_controls": similar_controls,
            "iso_guidance": iso_guidance,
            "risk_patterns": self._get_risk_patterns(risk_category, user_domain)
        }

    def retrieve_context_for_query(self, query: str, intent: str, parameters: Dict, user_id: str) -> Dict:
        query_embedding = self.openai.get_embedding(query)
        
        if intent == "show_finalized_controls":
            return self._get_finalized_controls_context(parameters, user_id)
        elif intent == "show_controls_by_category":
            return self._get_controls_by_category(parameters.get('risk_category'), user_id)
        elif intent == "show_controls_by_annex":
            return self._get_controls_by_annex(parameters.get('annex'), user_id)
        elif intent == "query_controls":
            return self._get_general_query_context(query_embedding, user_id)
        else:
            return {}

    def _get_finalized_controls_context(self, parameters: Dict, user_id: str) -> Dict:
        if parameters.get('risk_id'):
            controls = self.mongo_db.get_controls_by_risk(parameters['risk_id'], user_id)
            risk = self.mongo_db.get_risk_by_id(parameters['risk_id'], user_id)
            return {"controls": controls, "risk": risk}
        else:
            user_stats = self.graph_db.get_user_risk_control_stats(user_id)
            return {"stats": user_stats}

    def _get_controls_by_category(self, category: str, user_id: str) -> Dict:
        controls = self.mongo_db.get_controls_by_category(category, user_id)
        return {"controls": controls, "category": category}

    def _get_controls_by_annex(self, annex: str, user_id: str) -> Dict:
        controls = self.mongo_db.get_controls_by_annex(annex, user_id)
        return {"controls": controls, "annex": annex}

    def _get_general_query_context(self, query_embedding: List[float], user_id: str) -> Dict:
        try:
            similar_controls = self.vector_db.search_similar_controls(query_embedding, limit=5)
            similar_risks = self.vector_db.search_similar_risks(query_embedding, limit=3)
            iso_guidance = self.vector_db.get_iso_guidance(query_embedding, limit=3)
        except Exception as e:
            print(f"Vector search failed in general query: {e}")
            similar_controls = []
            similar_risks = []
            iso_guidance = []
        
        return {
            "similar_controls": similar_controls,
            "similar_risks": similar_risks,
            "iso_guidance": iso_guidance
        }

    def _get_risk_patterns(self, risk_category: str, user_domain: str) -> List[Dict]:
        return self.graph_db.get_controls_by_annex_and_category("A.", risk_category)

    def store_control_embeddings(self, controls: List[Dict]):
        for control in controls:
            embedding_text = f"{control['title']} {control['description']}"
            embedding = self.openai.get_embedding(embedding_text)
            
            self.vector_db.store_control_embedding(
                control['id'],
                control['user_id'],
                control['title'],
                control['description'],
                control['annex_reference'],
                embedding
            )

    def store_risk_embedding(self, risk_data: Dict):
        embedding_text = f"{risk_data.get('description', '')} {risk_data.get('category', '')}"
        embedding = self.openai.get_embedding(embedding_text)
        
        self.vector_db.store_risk_embedding(
            risk_data.get("id", ""),
            risk_data.get("user_id", ""),
            risk_data.get("description", ""),
            risk_data.get("category", ""),
            embedding
        )

rag_service = RAGService()
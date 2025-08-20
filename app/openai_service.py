import openai
from typing import List, Dict
import json
from .config import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

class OpenAIService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=OPENAI_API_KEY)

    def get_embedding(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding

    def classify_intent(self, query: str, user_context: Dict) -> Dict:
        prompt = f"""
        User Query: {query}
        User Context: Organization: {user_context.get('organization_name', '')}, Domain: {user_context.get('domain', '')}
        
        Classify the intent and extract parameters:
        
        Intent Categories:
        - generate_controls_specific: Generate controls for a specific risk
        - generate_controls_all: Generate controls for all risks in register
        - generate_controls_category: Generate controls for specific risk category
        - query_controls: Ask information about controls
        - show_finalized_controls: Show existing finalized controls
        - show_controls_by_category: Show controls by risk category
        - show_controls_by_annex: Show controls by ISO annex
        
        Return JSON with:
        {{
            "intent": "intent_name",
            "parameters": {{
                "risk_id": "if specific risk mentioned",
                "risk_category": "if category mentioned", 
                "annex": "if annex mentioned (A.5, A.6, etc)",
                "query_type": "if asking information"
            }}
        }}
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except:
            return {"intent": "query_controls", "parameters": {}}

    def generate_controls(self, risk_data: Dict, user_context: Dict, 
                         similar_controls: List[Dict], iso_guidance: List[Dict]) -> List[Dict]:
        context_text = f"""
        Risk Details:
        - Description: {risk_data.get('description', '')}
        - Category: {risk_data.get('category', '')}
        - Impact: {risk_data.get('impact', '')}
        - Likelihood: {risk_data.get('likelihood', '')}
        
        Organization Context:
        - Name: {user_context.get('organization_name', '')}
        - Domain: {user_context.get('domain', '')}
        - Location: {user_context.get('location', '')}
        
        Similar Controls Used by Others:
        {json.dumps(similar_controls[:3], indent=2)}
        
        ISO 27001 Guidance:
        {json.dumps(iso_guidance, indent=2)}
        """
        
        prompt = f"""
        Based on the risk and context provided, generate 3-5 relevant ISO 27001:2022 Annex A controls.
        
        {context_text}
        
        For each control, provide:
        1. control_id: Unique ID (format: RISK_CATEGORY-001, e.g., FIN-001)
        2. title: Control title
        3. description: What the control addresses
        4. domain_category: Organizational/People/Physical/Technological Controls
        5. annex_reference: ISO reference (A.5.1, A.8.5, etc.)
        6. control_statement: Actionable statement for implementation
        7. implementation_guidance: How to implement
        
        Return valid JSON array of controls:
        [{{
            "control_id": "...",
            "title": "...",
            "description": "...",
            "domain_category": "...",
            "annex_reference": "...",
            "control_statement": "...",
            "implementation_guidance": "..."
        }}]
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except:
            return []

    def synthesize_response(self, query: str, context: Dict, controls: List[Dict] = None) -> str:
        if controls:
            controls_text = f"Generated {len(controls)} controls for selection."
        else:
            controls_text = json.dumps(context, indent=2)
        
        prompt = f"""
        User Query: {query}
        Context/Results: {controls_text}
        
        Provide a helpful, conversational response to the user's query.
        If controls were generated, mention that they can select from the options.
        Keep response concise and professional.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        return response.choices[0].message.content

openai_service = OpenAIService()
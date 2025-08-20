import openai
from typing import List, Dict
import re
import json
from .config import OPENAI_API_KEY
import os
# Load annex JSON file
ANNEX_JSON_PATH = os.path.join(os.path.dirname(__file__), '..', 'annex.json')
try:
    with open(ANNEX_JSON_PATH, 'r', encoding='utf-8') as f:
        annex_data = json.load(f)
except FileNotFoundError:
    annex_data = {}

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
        # Heuristic-first routing for robustness
        q = (query or "").lower().strip()

        # Listing desires
        wants_listing = (any(word in q for word in ["list", "show", "display", "give me"]) and 
                         ("risk" in q or "risks" in q))
        wants_without_controls = any(phrase in q for phrase in [
            "without controls", "no controls", "missing controls", "without any controls"
        ])

        # Impact detection
        impact_level = None
        if "high" in q and "impact" in q:
            impact_level = "High"
        elif "medium" in q and "impact" in q:
            impact_level = "Medium"
        elif "low" in q and "impact" in q:
            impact_level = "Low"

        if wants_listing:
            if wants_without_controls:
                return {"intent": "show_risks_without_controls", "parameters": {}}
            if impact_level:
                return {"intent": "show_risks_by_impact", "parameters": {"impact": impact_level}}
            return {"intent": "show_risks", "parameters": {}}

        # Generation intents
        mentions_generate_controls = ("generate controls" in q) or ("generate" in q and "controls" in q)
        if mentions_generate_controls:
            # Specific risk id pattern
            m = re.search(r"generate\s+controls\s+for\s+risk\s+([a-z0-9\-]{4,})", q)
            if m:
                return {"intent": "generate_controls_specific", "parameters": {"risk_id": m.group(1)}}
            if impact_level:
                return {"intent": "generate_controls_impact", "parameters": {"impact": impact_level}}
            if any(phrase in q for phrase in ["for all", "for all risks", "for my risks", "for every risk", "for all the risks"]):
                return {"intent": "generate_controls_all", "parameters": {}}
            # If user says just "generate controls" default to all
            return {"intent": "generate_controls_all", "parameters": {}}

        # Fallback to LLM-based classification with expanded intents
        prompt = f"""
You are an intent classifier. Read the user's query and return a strict JSON for one allowed intent.

Allowed intents:
- generate_controls_specific
- generate_controls_all
- generate_controls_category
- generate_controls_impact
- query_controls
- show_finalized_controls
- show_controls_by_category
- show_controls_by_annex
- show_risks
- show_risks_without_controls
- show_risks_by_category
- show_risks_by_impact

Examples:
- "list my risks" -> show_risks
- "show me risks without controls" -> show_risks_without_controls
- "show my risks in Access Control" -> show_risks_by_category with parameters.risk_category="Access Control"
- "list risks with high impact" -> show_risks_by_impact with parameters.impact="High"
- "generate controls" -> generate_controls_all
- "generate controls for risk abc123" -> generate_controls_specific with parameters.risk_id="abc123"
- "generate controls for risks with high impact" -> generate_controls_impact with parameters.impact="High"

Return JSON only:
{{
  "intent": "one_of_the_above",
  "parameters": {{
    "risk_id": "",
    "risk_category": "",
    "annex": "",
    "query_type": ""
  }}
}}

User Query: {query}
Organization: {user_context.get('organization_name', '')}, Domain: {user_context.get('domain', '')}, Location: {user_context.get('location', '')}
""".strip()

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        try:
            return json.loads(response.choices[0].message.content)
        except Exception:
            return {"intent": "query_controls", "parameters": {}}

    def generate_controls(self, risk_data: Dict, user_context: Dict) -> List[Dict]:
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

        ISO 27001:2022 Annex A Guidance:
        {json.dumps(annex_data, indent=2)}
        """
        
        prompt = f"""
        Based on the risk and context provided, generate 3-5 relevant ISO 27001:2022 Annex A controls.
        
        {context_text}
        
        For each control, provide:
        1. control_id: Unique ID (format: RISK_CATEGORY-001, e.g., FIN-001)
        2. title: Control title
        3. description: What the control addresses
        4. domain_category: Organizational/People/Physical/Technological Controls
        5. annex_reference: ISO reference from the given guidance (A.5.1 to A.8.34)
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
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            return []

    def synthesize_response(self, query: str, context: Dict, controls: List[Dict] = None) -> str:   
        if controls:
            controls_text = f"Generated {len(controls)} controls for selection."
        else:
            controls_text = json.dumps(context, default=str, indent=2)
        
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
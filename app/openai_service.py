import openai
from typing import List, Dict
import json
from .config import OPENAI_API_KEY
import logging

logger = logging.getLogger(__name__)

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
        - query_controls: Ask information about controls (general queries like "show me controls related to X", "what controls exist for Y")
        - show_finalized_controls: Show existing finalized controls
        - show_controls_by_category: Show controls by specific risk category (only when user explicitly asks for controls by risk category like "show controls for operational risk")
        - show_controls_by_annex: Show controls by ISO annex
        
        IMPORTANT CLASSIFICATION RULES:
        1. Use query_controls for general information requests about controls (e.g., "show me controls related to supply chain", "what controls exist for information security")
        2. Use show_controls_by_category ONLY when user explicitly asks for controls by risk category (e.g., "show controls for operational risk", "controls by risk category")
        3. "Supply chain" is NOT a risk category - it's a business domain. Use query_controls for supply chain queries.
        4. "Information security" is NOT a risk category - it's a security domain. Use query_controls for information security queries.
        
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
        
        # Format the ISO guidance more clearly
        annex_guidance_text = ""
        if iso_guidance:
            annex_guidance_text = "Available ISO 27001:2022 Annex A Controls:\n"
            for guidance in iso_guidance:
                annex_guidance_text += f"- {guidance.get('reference', 'Unknown')}: {guidance.get('guidance', 'No guidance')}\n"
        else:
            annex_guidance_text = "No specific ISO guidance available. Use standard ISO 27001:2022 Annex A controls."
        
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
        
        {annex_guidance_text}
        """
        
        prompt = f"""
        Based on the risk and context provided, generate 3-5 relevant ISO 27001:2022 Annex A controls.
        
        {context_text}
        
        IMPORTANT: Use the specific annex references provided above (A.5.x, A.6.x, A.7.x, A.8.x) when possible.
        If the risk category matches specific annex controls, prioritize those.
        
        For each control, provide:
        1. control_id: Unique ID (format: RISK_CATEGORY-001, e.g., FIN-001)
        2. title: Control title based on the annex guidance
        3. description: What the control addresses
        4. domain_category: Organizational/People/Physical/Technological Controls (match the annex description)
        5. annex_reference: ISO reference from the provided guidance (A.5.1, A.8.5, etc.)
        6. control_statement: Actionable statement for implementation
        7. implementation_guidance: How to implement based on the annex guidance
        
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

    def generate_contextual_response(self, query: str, context: Dict, user_context: Dict) -> str:
        """Generate enhanced contextual response using retrieved context"""
        try:
            # Enhanced detection for control-related queries
            query_lower = query.lower()
            control_keywords = [
                "control", "controls", "security", "cybersecurity", "cyber security",
                "information security", "infosec", "supply chain", "supply chain risk",
                "data protection", "access control", "authentication", "authorization",
                "encryption", "firewall", "network security", "endpoint security",
                "malware", "vulnerability", "threat", "risk management", "security policy",
                "security awareness", "incident response", "security monitoring",
                "audit", "compliance", "iso 27001", "iso27001", "annex", "annex a",
                "a.5", "a.6", "a.7", "a.8", "business continuity", "disaster recovery"
            ]
            
            # Check if this is a control-related query
            is_control_query = any(keyword in query_lower for keyword in control_keywords)
            
            # Also check if we have controls in the context
            has_controls = bool(context.get("similar_controls") or context.get("existing_controls") or context.get("text_search_controls"))
            
            if is_control_query or has_controls:
                logger.info(f"   🎯 Control query detected, using enhanced control response")
                logger.info(f"      Query keywords: {[k for k in control_keywords if k in query_lower]}")
                logger.info(f"      Has controls in context: {has_controls}")
                return self.generate_general_controls_response(query, context, user_context)
            
            # Prepare context summary for other types of queries
            context_summary = {}
            for key, value in context.items():
                if isinstance(value, list):
                    context_summary[key] = f"Found {len(value)} items"
                elif isinstance(value, dict):
                    context_summary[key] = f"Context object with {len(value)} keys"
                else:
                    context_summary[key] = str(value)
            
            prompt = f"""
            User Query: {query}
            User Context: {user_context}
            Retrieved Context: {context_summary}
            
            Provide a helpful, contextual response based on the retrieved information.
            If controls were generated, explain what was found and next steps.
            If errors occurred, provide a helpful explanation and suggestions.
            Keep the response professional and actionable.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            return response.choices[0].message.content
        except Exception as e:
            # Fallback to simple response
            return f"I found some information related to your query. {str(e)[:100]}"

    def generate_general_controls_response(self, query: str, context: Dict, user_context: Dict) -> str:
        """Generate response for general control queries using ONLY vector search results with high relevance"""
        try:
            similar_controls = context.get("similar_controls", [])
            existing_controls = context.get("existing_controls", [])
            text_search_controls = context.get("text_search_controls", [])
            total_controls_found = context.get("total_controls_found", 0)
            
            # Filter to ONLY show vector search results with relevance score > 0.8
            high_relevance_controls = []
            for control in similar_controls:
                if control.get('source') == 'vector_search':
                    similarity_score = control.get('similarity', 0)
                    if similarity_score > 0.8:
                        high_relevance_controls.append(control)
            
            # If no high-relevance controls found, return appropriate message
            if not high_relevance_controls:
                return "I couldn't find any controls with high relevance (score > 0.8) that match your query. The search found some controls but they didn't meet the relevance threshold."
            
            # Build response with ONLY high-relevance vector search results
            response_parts = []
            
            # Header - remove "Vector Search" terminology
            if "information security" in query.lower() or "security" in query.lower():
                response_parts.append("## Information Security Controls Found")
                response_parts.append("")
                response_parts.append(f"I found {len(high_relevance_controls)} controls related to Information Security with high relevance:")
                response_parts.append("")
            elif "supply chain" in query.lower():
                response_parts.append("## Supply Chain Controls Found")
                response_parts.append("")
                response_parts.append(f"I found {len(high_relevance_controls)} controls related to Supply Chain with high relevance:")
                response_parts.append("")
            else:
                response_parts.append("## Controls Found")
                response_parts.append("")
                response_parts.append(f"I found {len(high_relevance_controls)} controls related to your query with high relevance:")
                response_parts.append("")
            
            # Show ONLY high-relevance vector search controls
            for i, control in enumerate(high_relevance_controls):
                response_parts.append(f"### Control {i+1}: {control.get('title', 'No Title')}")
                response_parts.append(f"**Description**: {control.get('description', 'No description')}")
                
                if control.get('control_statement') and control.get('control_statement') != 'Not specified':
                    response_parts.append(f"**Implementation**: {control.get('control_statement')}")
                
                if control.get('implementation_guidance'):
                    response_parts.append(f"**Guidance**: {control.get('implementation_guidance')}")
                
                # Add similarity score if available
                if control.get('similarity'):
                    response_parts.append(f"**Relevance Score**: {control.get('similarity'):.3f}")
                
                response_parts.append("")
                response_parts.append("")
            
            # Summary - remove "vector search" terminology
            response_parts.append("## Summary")
            response_parts.append("")
            response_parts.append(f"Total high-relevance controls found: {len(high_relevance_controls)}")
            response_parts.append("")
            response_parts.append("These controls were found by searching for controls with similar semantic meaning to your query and meet the high relevance threshold (score > 0.8).")
            
            # Next steps
            response_parts.append("")
            response_parts.append("## Next Steps")
            response_parts.append("")
            if "supply chain" in query.lower():
                response_parts.append("1. Review the high-relevance controls above for supply chain related controls")
                response_parts.append("2. Consider generating additional controls for specific supply chain risks")
                response_parts.append("3. These controls have been pre-filtered for high relevance to your query")
            else:
                response_parts.append("1. Review the high-relevance controls above for relevant controls")
                response_parts.append("2. Consider generating additional controls for specific risks")
                response_parts.append("3. These controls have been pre-filtered for high relevance to your query")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            return f"Error processing search results: {str(e)[:100]}"

    def generate_show_controls_response(self, query: str, context: Dict, user_context: Dict) -> str:
        """Generate response for showing controls queries using LLM for better formatting"""
        try:
            similar_controls = context.get("similar_controls", [])
            annex = context.get("annex", "")
            annex_guidance = context.get("annex_guidance", {})
            
            # Validate that we only have vector search results
            if not similar_controls:
                return "I couldn't find any controls related to your query through vector search. You may want to try searching with different terms or generate new controls for specific risks."
            
            # Ensure we're only working with vector search results
            vector_controls = []
            for control in similar_controls:
                # Only include controls that have similarity scores (vector search results)
                if 'similarity' in control:
                    vector_controls.append(control)
            
            if not vector_controls:
                return "I couldn't find any valid vector search results for your query. The search may need to be refined."
            
            # Prepare the context for LLM - ONLY vector search results
            controls_info = []
            for i, control in enumerate(vector_controls):
                control_info = f"""
Control {i+1}:
- Title: {control.get('title', 'No Title')}
- Description: {control.get('description', 'No description')}
"""
                if control.get('control_statement') and control.get('control_statement') != 'Not specified':
                    control_info += f"- Implementation: {control.get('control_statement')}\n"
                if control.get('implementation_guidance'):
                    control_info += f"- Guidance: {control.get('implementation_guidance')}\n"
                controls_info.append(control_info)
            
            # Create prompt for LLM
            prompt = f"""
You are a professional information security consultant providing a direct response to a user query. 

A user has asked to see controls related to {annex} (ISO 27001:2022 Annex A). I found {len(vector_controls)} controls through vector search.

CRITICAL FORMATTING REQUIREMENTS:
- Write as a direct response
- Do NOT include Control IDs in the response
- Do NOT include relevance scores in the response
- Focus on the title, description, and implementation details only
- Keep the response clean and user-friendly
- Use PROPER SPACING between all sections for readability

FORMATTING STRUCTURE (MUST FOLLOW EXACTLY):
1. Start with main heading: ## Information Security Controls for {annex} (ISO 27001:2022 Annex A)
2. Add introduction paragraph
3. Add TWO blank lines
4. For each control:
   - Control heading (### Control X: Title)
   - Description on next line
   - Add TWO blank lines after each control
5. Add summary paragraph
6. Add TWO blank lines
7. Add Next Steps section
8. Add TWO blank lines
9. Add closing paragraph

Please create a direct response that:

1. Starts immediately with a main heading
2. Lists ONLY the vector search results in a clean, organized manner
3. Uses clear headings and bullet points
4. Is direct
5. Provides helpful next steps
6. Has PROPER SPACING between all sections

IMPORTANT: 
- Do NOT include Control ID fields or relevance scores in your response
- Only show: Title, Description, Implementation (if available), Guidance (if available)
- Use double line breaks between sections for proper spacing
- Ensure each control is clearly separated with adequate spacing
- FOLLOW THE EXACT FORMATTING STRUCTURE ABOVE

Here are the controls found through vector search:

{chr(10).join(controls_info)}

{annex_guidance.get('guidance', '')}

Format this as a clean, professional response with proper spacing between all sections. Each control should be clearly separated, and there should be adequate spacing between the introduction, controls list, and next steps sections.
"""

            # Generate response using LLM
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1  # Very low temperature for consistent formatting
            )
            
            # Post-process the response to remove any remaining email formatting and ensure proper spacing
            response_text = response.choices[0].message.content
            
            # Remove common email formatting patterns
            lines = response_text.split('\n')
            cleaned_lines = []
            skip_until_content = True
            
            for line in lines:
                line_lower = line.lower().strip()
                
                # Skip subject lines and email headers
                if line_lower.startswith('subject:') or line_lower.startswith('subject line:'):
                    continue
                if line_lower.startswith('dear') or line_lower.startswith('hello') or line_lower.startswith('hi'):
                    continue
                if line_lower.startswith('best regards') or line_lower.startswith('sincerely') or line_lower.startswith('yours truly'):
                    continue
                if line_lower.startswith('[') and line_lower.endswith(']'):
                    continue
                
                # Start including content when we hit the first heading
                if line.strip().startswith('##'):
                    skip_until_content = False
                
                if not skip_until_content:
                    cleaned_lines.append(line)
            
            # Ensure proper spacing by adding line breaks where needed
            final_lines = []
            for i, line in enumerate(cleaned_lines):
                final_lines.append(line)
                
                # Add spacing after headings
                if line.strip().startswith('##') or line.strip().startswith('###'):
                    final_lines.append('')
                    final_lines.append('')
                
                # Add spacing after control descriptions
                elif line.strip().startswith('**Description:**') and i < len(cleaned_lines) - 1:
                    # Check if next line is a new control or section
                    next_line = cleaned_lines[i + 1] if i + 1 < len(cleaned_lines) else ''
                    if next_line.strip().startswith('##') or next_line.strip().startswith('###'):
                        final_lines.append('')
                        final_lines.append('')
                    else:
                        final_lines.append('')
                        final_lines.append('')
                
                # Add spacing before Next Steps
                elif line.strip().startswith('# Next Steps') or line.strip().startswith('## Next Steps'):
                    final_lines.append('')
                    final_lines.append('')
            
            return '\n'.join(final_lines)
            
        except Exception as e:
            # Fallback to simple formatted response if LLM fails
            try:
                similar_controls = context.get("similar_controls", [])
                if not similar_controls:
                    return "I couldn't find any controls related to your query."
                
                response_parts = []
                response_parts.append(f"## Controls Related to {annex} (ISO 27001:2022 Annex A)")
                response_parts.append("")
                response_parts.append(f"I found {len(similar_controls)} controls through vector search:")
                response_parts.append("")
                
                for i, control in enumerate(similar_controls):
                    response_parts.append(f"### {i+1}. {control.get('title', 'No Title')}")
                    response_parts.append(f"**Control ID**: {control.get('control_id', 'Unknown')}")
                    response_parts.append(f"**Description**: {control.get('description', 'No description')}")
                    response_parts.append(f"**Relevance Score**: {control.get('similarity', 0):.2f}")
                    
                    if i < len(similar_controls) - 1:
                        response_parts.append("")
                        response_parts.append("---")
                        response_parts.append("")
                
                return "\n".join(response_parts)
                
            except Exception as fallback_error:
                return f"Error generating response: {str(e)[:100]}"

openai_service = OpenAIService()
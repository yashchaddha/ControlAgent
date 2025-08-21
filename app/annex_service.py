import json
import os
from typing import List, Dict
from pathlib import Path

class AnnexService:
    """Service to provide ISO 27001:2022 Annex A guidance from annex2.json"""
    
    def __init__(self):
        self.annex_data = self._load_annex_data()
    
    def _load_annex_data(self) -> List[Dict]:
        """Load annex data from annex2.json file"""
        try:
            # Get the path to annex2.json relative to the project root
            current_dir = Path(__file__).parent
            annex_path = current_dir.parent / "annex2.json"
            
            if not annex_path.exists():
                print(f"⚠️  annex2.json not found at {annex_path}")
                return []
            
            with open(annex_path, 'r') as f:
                data = json.load(f)
                print(f"✅ Loaded {len(data)} annex controls from annex2.json")
                return data
                
        except Exception as e:
            print(f"❌ Failed to load annex2.json: {e}")
            return []
    
    def get_annex_controls(self, risk_category: str = None, limit: int = 10) -> List[Dict]:
        """Get annex controls, optionally filtered by category"""
        if not self.annex_data:
            return []
        
        if not risk_category:
            return self.annex_data[:limit]
        
        # Map risk categories to annex descriptions
        category_mapping = {
            "Operational Risk": ["Organizational Controls"],
            "Technical Risk": ["Technological Controls"],
            "Compliance Risk": ["Organizational Controls", "People Controls"],
            "Financial Risk": ["Organizational Controls"],
            "Strategic Risk": ["Organizational Controls"],
            "Reputational Risk": ["Organizational Controls", "People Controls"],
            "Physical Risk": ["Physical Controls"],
            "Environmental Risk": ["Physical Controls"],
            "Supply Chain Risk": ["Organizational Controls", "Physical Controls"],
            "Cybersecurity Risk": ["Technological Controls", "Organizational Controls"],
            "Data Risk": ["Technological Controls", "Organizational Controls"],
            "Human Resource Risk": ["People Controls"],
            "Natural Disaster Risk": ["Physical Controls", "Organizational Controls"]
        }
        
        # Get relevant categories for the risk
        relevant_categories = category_mapping.get(risk_category, ["Organizational Controls"])
        
        # Filter controls by relevant categories
        relevant_controls = [
            control for control in self.annex_data 
            if control.get("description") in relevant_categories
        ]
        
        return relevant_controls[:limit]
    
    def get_annex_by_reference(self, annex_ref: str) -> Dict:
        """Get specific annex control by reference (e.g., 'A.8.5')"""
        if not self.annex_data:
            return {}
        
        for control in self.annex_data:
            if control.get("reference") == annex_ref:
                return control
        
        return {}
    
    def get_controls_by_domain(self, domain: str) -> List[Dict]:
        """Get controls by domain (Organizational, People, Physical, Technological)"""
        if not self.annex_data:
            return []
        
        domain_controls = [
            control for control in self.annex_data 
            if control.get("description") == f"{domain} Controls"
        ]
        
        return domain_controls
    
    def search_annex_controls(self, query: str, limit: int = 5) -> List[Dict]:
        """Search annex controls by query text"""
        if not self.annex_data:
            return []
        
        query_lower = query.lower()
        matching_controls = []
        
        # Enhanced search with business continuity and disaster recovery keywords
        business_continuity_keywords = [
            "business continuity", "disaster recovery", "continuity", "recovery", 
            "backup", "resilience", "emergency", "incident", "disruption",
            "operational", "organizational", "physical", "environmental"
        ]
        
        # Information Security specific keywords
        information_security_keywords = [
            "information security", "infosec", "security", "cybersecurity", "cyber security",
            "data protection", "data security", "access control", "authentication", "authorization",
            "encryption", "firewall", "network security", "endpoint security", "malware",
            "vulnerability", "threat", "risk management", "security policy", "security awareness",
            "incident response", "security monitoring", "audit", "compliance", "iso 27001",
            "iso27001", "annex a", "annex a.", "a.5", "a.6", "a.7", "a.8"
        ]
        
        # Supply Chain specific keywords
        supply_chain_keywords = [
            "supply chain", "supply chain risk", "supply chain security", "vendor", "vendors",
            "third party", "third-party", "outsourcing", "outsourced", "contractor", "contractors",
            "supplier", "suppliers", "procurement", "logistics", "distribution", "transportation",
            "warehouse", "warehousing", "inventory", "stock", "material", "materials",
            "component", "components", "part", "parts", "raw material", "raw materials",
            "manufacturing", "production", "assembly", "quality control", "quality assurance"
        ]
        
        # Check if query is related to business continuity
        is_business_continuity_query = any(keyword in query_lower for keyword in business_continuity_keywords)
        
        # Check if query is related to information security
        is_information_security_query = any(keyword in query_lower for keyword in information_security_keywords)
        
        # Check if query is related to supply chain
        is_supply_chain_query = any(keyword in query_lower for keyword in supply_chain_keywords)
        
        for control in self.annex_data:
            # Check if query matches reference, description, or guidance
            if (query_lower in control.get("reference", "").lower() or
                query_lower in control.get("description", "").lower() or
                query_lower in control.get("guidance", "").lower()):
                matching_controls.append(control)
            
            # Special handling for business continuity queries
            elif is_business_continuity_query:
                # For business continuity queries, include relevant organizational and physical controls
                if (control.get("description") in ["Organizational Controls", "Physical Controls"] and
                    control.get("reference", "").startswith(("A.5.", "A.7."))):
                    matching_controls.append(control)
            
            # Special handling for information security queries
            elif is_information_security_query:
                # For information security queries, include relevant controls from all domains
                # Prioritize technological and organizational controls
                if (control.get("description") in ["Technological Controls", "Organizational Controls"] and
                    control.get("reference", "").startswith(("A.5.", "A.8."))):
                    matching_controls.append(control)
                # Also include people controls for security awareness and training
                elif (control.get("description") == "People Controls" and
                      control.get("reference", "").startswith("A.6.")):
                    matching_controls.append(control)
            
            # Special handling for supply chain queries
            elif is_supply_chain_query:
                # For supply chain queries, include relevant organizational and physical controls
                # Organizational controls for vendor management, contracts, and policies
                if (control.get("description") == "Organizational Controls" and
                    control.get("reference", "").startswith("A.5.")):
                    matching_controls.append(control)
                # Physical controls for warehouse security, access control, and asset protection
                elif (control.get("description") == "Physical Controls" and
                      control.get("reference", "").startswith("A.7.")):
                    matching_controls.append(control)
                # People controls for training and awareness related to supply chain
                elif (control.get("description") == "People Controls" and
                      control.get("reference", "").startswith("A.6.")):
                    matching_controls.append(control)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_controls = []
        for control in matching_controls:
            control_id = control.get("reference", "")
            if control_id not in seen:
                seen.add(control_id)
                unique_controls.append(control)
        
        return unique_controls[:limit]

# Create global instance
annex_service = AnnexService()

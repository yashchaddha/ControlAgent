from neo4j import GraphDatabase
from .config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
from typing import Dict, List

class Neo4jService:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

    def close(self):
        self.driver.close()

    def create_user_node(self, user_data: Dict):
        with self.driver.session() as session:
            session.run("""
                MERGE (u:User {id: $user_id})
                SET u.username = $username,
                    u.organization_name = $organization_name,
                    u.location = $location,
                    u.domain = $domain
            """, **user_data)

    def create_risk_node(self, risk_data: Dict):
        with self.driver.session() as session:
            session.run("""
                MERGE (r:Risk {id: $id})
                SET r.description = $description,
                    r.category = $category,
                    r.likelihood = $likelihood,
                    r.impact = $impact,
                    r.user_id = $user_id
                WITH r
                MATCH (u:User {id: $user_id})
                MERGE (u)-[:HAS_RISK]->(r)
            """, **risk_data)

    def create_control_node(self, control_data: Dict):
        with self.driver.session() as session:
            session.run("""
                MERGE (c:Control {id: $id})
                SET c.control_id = $control_id,
                    c.title = $title,
                    c.description = $description,
                    c.domain_category = $domain_category,
                    c.annex_reference = $annex_reference,
                    c.user_id = $user_id,
                    c.risk_id = $risk_id
                WITH c
                MATCH (u:User {id: $user_id})
                MATCH (r:Risk {id: $risk_id})
                MERGE (u)-[:SELECTED_CONTROL]->(c)
                MERGE (c)-[:MITIGATES]->(r)
            """, **control_data)

    def get_similar_controls_by_domain(self, domain: str, risk_category: str) -> List[Dict]:
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {domain: $domain})-[:SELECTED_CONTROL]->(c:Control)
                      -[:MITIGATES]->(r:Risk {category: $risk_category})
                RETURN c.control_id, c.title, c.annex_reference, count(*) as usage_count
                ORDER BY usage_count DESC
                LIMIT 10
            """, domain=domain, risk_category=risk_category)
            return [dict(record) for record in result]

    def get_controls_by_annex_and_category(self, annex: str, risk_category: str) -> List[Dict]:
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Control)-[:MITIGATES]->(r:Risk {category: $risk_category})
                WHERE c.annex_reference IS NOT NULL AND c.annex_reference STARTS WITH $annex
                RETURN c.control_id, c.title, c.annex_reference, count(*) as usage_count
                ORDER BY usage_count DESC
            """, annex=annex, risk_category=risk_category)
            return [dict(record) for record in result]

    def get_user_risk_control_stats(self, user_id: str) -> Dict:
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {id: $user_id})-[:HAS_RISK]->(r:Risk)
                OPTIONAL MATCH (u)-[:SELECTED_CONTROL]->(c:Control)-[:MITIGATES]->(r)
                RETURN r.category as risk_category, 
                       count(DISTINCT r) as total_risks,
                       count(DISTINCT c) as total_controls
            """, user_id=user_id)
            return [dict(record) for record in result]

    def initialize_iso_annexes(self):
        annexes = [
            {"reference": "A.5", "description": "Organizational Controls"},
            {"reference": "A.6", "description": "People Controls"},
            {"reference": "A.7", "description": "Physical Controls"},
            {"reference": "A.8", "description": "Technological Controls"}
        ]
        
        with self.driver.session() as session:
            for annex in annexes:
                session.run("""
                    MERGE (a:AnnexCategory {reference: $reference})
                    SET a.description = $description
                """, **annex)

neo4j_service = Neo4jService()
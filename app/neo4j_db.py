from neo4j import GraphDatabase
from .config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
from typing import Dict, List
import logging

# Configure logging
logger = logging.getLogger(__name__)

class Neo4jService:
    def __init__(self):
        try:
            self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
            logger.info("Neo4j service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j service: {e}")
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    def create_user_node(self, user_data: Dict):
        if not self.driver:
            logger.error("Neo4j driver not available")
            return False
            
        try:
            with self.driver.session() as session:
                session.run("""
                    MERGE (u:User {id: $user_id})
                    SET u.username = $username,
                        u.organization_name = $organization_name,
                        u.location = $location,
                        u.domain = $domain
                """, **user_data)
                logger.info(f"User node created/updated: {user_data.get('user_id')}")
                return True
        except Exception as e:
            logger.error(f"Failed to create user node: {e}")
            return False

    def create_risk_node(self, risk_data: Dict):
        if not self.driver:
            logger.error("Neo4j driver not available")
            return False
            
        try:
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
                logger.info(f"Risk node created/updated: {risk_data.get('id')}")
                return True
        except Exception as e:
            logger.error(f"Failed to create risk node: {e}")
            return False

    def create_control_node(self, control_data: Dict):
        if not self.driver:
            logger.error("Neo4j driver not available")
            return False
            
        try:
            with self.driver.session() as session:
                # First, ensure the risk node exists
                session.run("""
                    MERGE (r:Risk {id: $risk_id})
                    SET r.user_id = $user_id
                """, risk_id=control_data.get('risk_id'), user_id=control_data.get('user_id'))
                
                # Create the control node
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
                
                logger.info(f"Control node created/updated: {control_data.get('control_id')}")
                logger.info(f"Risk-control relationship created: {control_data.get('risk_id')} -> {control_data.get('control_id')}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create control node: {e}")
            return False

    def get_similar_controls_by_domain(self, domain: str, risk_category: str) -> List[Dict]:
        if not self.driver:
            logger.error("Neo4j driver not available")
            return []
            
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (u:User {domain: $domain})-[:SELECTED_CONTROL]->(c:Control)
                          -[:MITIGATES]->(r:Risk {category: $risk_category})
                    RETURN c.control_id, c.title, c.annex_reference, count(*) as usage_count
                    ORDER BY usage_count DESC
                    LIMIT 10
                """, domain=domain, risk_category=risk_category)
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Failed to get similar controls: {e}")
            return []

    def get_controls_by_annex_and_category(self, annex: str, risk_category: str) -> List[Dict]:
        if not self.driver:
            logger.error("Neo4j driver not available")
            return []
            
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (c:Control)-[:MITIGATES]->(r:Risk {category: $risk_category})
                    WHERE c.annex_reference IS NOT NULL AND c.annex_reference STARTS WITH $annex
                    RETURN c.control_id, c.title, c.annex_reference, count(*) as usage_count
                    ORDER BY usage_count DESC
                """, annex=annex, risk_category=risk_category)
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Failed to get controls by annex and category: {e}")
            return []

    def get_user_risk_control_stats(self, user_id: str) -> Dict:
        if not self.driver:
            logger.error("Neo4j driver not available")
            return {}
            
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (u:User {id: $user_id})-[:HAS_RISK]->(r:Risk)
                    OPTIONAL MATCH (u)-[:SELECTED_CONTROL]->(c:Control)-[:MITIGATES]->(r)
                    RETURN r.category as risk_category, 
                           count(DISTINCT r) as total_risks,
                           count(DISTINCT c) as total_controls
                """, user_id=user_id)
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Failed to get user risk control stats: {e}")
            return {}

    def initialize_iso_annexes(self):
        if not self.driver:
            logger.error("Neo4j driver not available")
            return False
            
        try:
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
            
            logger.info("ISO annexes initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize ISO annexes: {e}")
            return False

neo4j_service = Neo4jService()
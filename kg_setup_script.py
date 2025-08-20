import asyncio
import argparse
from typing import List, Dict
from pymongo import MongoClient
from neo4j import GraphDatabase
import psycopg2
from psycopg2.extras import RealDictCursor
import openai
from datetime import datetime
import sys
import os
from dotenv import load_dotenv

load_dotenv()

class KnowledgeGraphBuilder:
    def __init__(self):
        self.mongo_client = MongoClient(os.getenv("MONGODB_URI"))
        self.mongo_db = self.mongo_client["isoriskagent"]
        
        self.neo4j_driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(os.getenv("NEO4J_USERNAME", "neo4j"), os.getenv("NEO4J_PASSWORD"))
        )
        
        self.postgres_conn = psycopg2.connect(os.getenv("POSTGRES_URI"))
        
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        self.batch_size = 100

    def close_connections(self):
        self.mongo_client.close()
        self.neo4j_driver.close()
        self.postgres_conn.close()

    def get_embedding(self, text: str) -> List[float]:
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return [0.0] * 1536

    def setup_postgres_tables(self):
        print("Setting up PostgreSQL tables...")
        with self.postgres_conn.cursor() as cur:
            cur.execute("""
                CREATE EXTENSION IF NOT EXISTS vector;
                
                DROP TABLE IF EXISTS risk_embeddings CASCADE;
                DROP TABLE IF EXISTS control_embeddings CASCADE;
                DROP TABLE IF EXISTS iso_guidance_embeddings CASCADE;
                
                CREATE TABLE risk_embeddings (
                    id SERIAL PRIMARY KEY,
                    risk_id VARCHAR(255) UNIQUE,
                    user_id VARCHAR(255),
                    description TEXT,
                    category VARCHAR(255),
                    domain VARCHAR(255),
                    embedding vector(1536),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE control_embeddings (
                    id SERIAL PRIMARY KEY,
                    control_id VARCHAR(255) UNIQUE,
                    user_id VARCHAR(255),
                    title TEXT,
                    description TEXT,
                    annex_reference VARCHAR(10),
                    domain_category VARCHAR(100),
                    embedding vector(1536),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE iso_guidance_embeddings (
                    id SERIAL PRIMARY KEY,
                    annex_reference VARCHAR(10) UNIQUE,
                    guidance_text TEXT,
                    embedding vector(1536),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX risk_embedding_idx ON risk_embeddings 
                USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
                
                CREATE INDEX control_embedding_idx ON control_embeddings 
                USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
                
                CREATE INDEX iso_guidance_embedding_idx ON iso_guidance_embeddings 
                USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
            """)
            self.postgres_conn.commit()
        print("PostgreSQL tables created successfully!")

    def setup_neo4j_schema(self):
        print("Setting up Neo4j schema...")
        with self.neo4j_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            
            session.run("""
                CREATE CONSTRAINT user_id_unique IF NOT EXISTS
                FOR (u:User) REQUIRE u.id IS UNIQUE
            """)
            
            session.run("""
                CREATE CONSTRAINT risk_id_unique IF NOT EXISTS
                FOR (r:Risk) REQUIRE r.id IS UNIQUE
            """)
            
            session.run("""
                CREATE CONSTRAINT control_id_unique IF NOT EXISTS
                FOR (c:Control) REQUIRE c.id IS UNIQUE
            """)
            
            session.run("""
                CREATE CONSTRAINT annex_ref_unique IF NOT EXISTS
                FOR (a:AnnexCategory) REQUIRE a.reference IS UNIQUE
            """)
            
            session.run("""
                CREATE CONSTRAINT risk_cat_unique IF NOT EXISTS
                FOR (rc:RiskCategory) REQUIRE rc.name IS UNIQUE
            """)
            
            session.run("""
                CREATE CONSTRAINT domain_unique IF NOT EXISTS
                FOR (d:Domain) REQUIRE d.name IS UNIQUE
            """)
            
        print("Neo4j schema created successfully!")

    def create_iso_annexes(self):
        print("Creating ISO Annex categories...")
        annexes = [
            {"reference": "A.5", "description": "Organizational Controls", "guidance": "Controls related to organizational policies, procedures, and management systems"},
            {"reference": "A.6", "description": "People Controls", "guidance": "Controls related to human resources security, training, and awareness"},
            {"reference": "A.7", "description": "Physical Controls", "guidance": "Controls related to physical and environmental security"},
            {"reference": "A.8", "description": "Technological Controls", "guidance": "Controls related to access control, cryptography, and system security"}
        ]
        
        with self.neo4j_driver.session() as session:
            for annex in annexes:
                session.run("""
                    MERGE (a:AnnexCategory {reference: $reference})
                    SET a.description = $description,
                        a.guidance = $guidance,
                        a.updated_at = datetime()
                """, **annex)
        
        with self.postgres_conn.cursor() as cur:
            for annex in annexes:
                embedding = self.get_embedding(f"{annex['description']} {annex['guidance']}")
                cur.execute("""
                    INSERT INTO iso_guidance_embeddings (annex_reference, guidance_text, embedding)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (annex_reference) DO UPDATE SET
                        guidance_text = EXCLUDED.guidance_text,
                        embedding = EXCLUDED.embedding
                """, (annex['reference'], annex['guidance'], embedding))
            self.postgres_conn.commit()
        
        print("ISO Annexes created successfully!")

    def process_users(self):
        print("Processing users...")
        users = list(self.mongo_db.users.find({}))
        
        with self.neo4j_driver.session() as session:
            for user in users:
                user_data = {
                    "id": user["username"],
                    "username": user["username"],
                    "organization_name": user.get("organization_name", ""),
                    "location": user.get("location", ""),
                    "domain": user.get("domain", "")
                }
                
                session.run("""
                    MERGE (u:User {id: $id})
                    SET u.username = $username,
                        u.organization_name = $organization_name,
                        u.location = $location,
                        u.domain = $domain,
                        u.updated_at = datetime()
                """, **user_data)
                
                if user_data["domain"]:
                    session.run("""
                        MERGE (d:Domain {name: $domain})
                        WITH d
                        MATCH (u:User {id: $user_id})
                        MERGE (u)-[:OPERATES_IN]->(d)
                    """, domain=user_data["domain"], user_id=user_data["id"])
        
        print(f"Processed {len(users)} users successfully!")

    def process_risks(self):
        print("Processing risks...")
        
        all_risks = []
        # Handle both collection structures
        for collection_name in ["finalized_risks", "risks"]:
            if collection_name in self.mongo_db.list_collection_names():
                risk_docs = list(self.mongo_db[collection_name].find({}))
                for risk_doc in risk_docs:
                    if "risks" in risk_doc and isinstance(risk_doc["risks"], list):
                        # Handle FinalizedRisks structure
                        for idx, risk in enumerate(risk_doc["risks"]):
                            # inherit context from parent document
                            risk["user_id"] = risk_doc.get("user_id", "")
                            risk["organization_name"] = risk_doc.get("organization_name", "")
                            risk["location"] = risk_doc.get("location", "")
                            risk["domain"] = risk_doc.get("domain", "")
                            # Ensure we have a stable, unique id field:
                            # - prefer risk._id if present
                            # - otherwise use parent_doc_id + index to guarantee uniqueness across nested risks
                            if "id" not in risk:
                                if "_id" in risk:
                                    risk["id"] = str(risk["_id"])
                                else:
                                    parent_id = str(risk_doc.get("_id", ""))
                                    risk["id"] = f"{parent_id}_{idx}"
                            # remove nested _id to avoid confusion downstream
                            if "_id" in risk:
                                try:
                                    del risk["_id"]
                                except Exception:
                                    pass
                            all_risks.append(risk)
                    else:
                        # Handle individual risk documents
                        if "_id" in risk_doc:
                            risk_doc["id"] = str(risk_doc["_id"])
                            try:
                                del risk_doc["_id"]
                            except Exception:
                                pass
                        else:
                            risk_doc["id"] = str(risk_doc.get("id", ""))
                        all_risks.append(risk_doc)
        
        print(f"Found {len(all_risks)} risks to process...")
        
        risk_categories = set()
        processed_ids = set()
        skipped = []

        for i, risk in enumerate(all_risks):
            if i % 50 == 0:
                print(f"Processing risk {i+1}/{len(all_risks)}")
            
            risk_id = risk.get("id", "")
            if not risk_id:
                skipped.append((None, "missing_id", risk))
                continue

            if not risk.get("user_id"):
                skipped.append((risk_id, "missing_user_id", risk))
                continue

            if risk_id in processed_ids:
                skipped.append((risk_id, "duplicate_id", risk))
                continue

            # mark as processed to avoid duplicate inserts
            processed_ids.add(risk_id)
            
            user_context = self.mongo_db.users.find_one({"username": risk["user_id"]})
            user_domain = user_context.get("domain", "") if user_context else ""
            
            risk_data = {
                "id": risk_id,
                "description": risk.get("description", ""),
                "category": risk.get("category", ""),
                "likelihood": risk.get("likelihood", ""),
                "impact": risk.get("impact", ""),
                "user_id": risk["user_id"]
            }
            
            if risk_data["category"]:
                risk_categories.add(risk_data["category"])
            
            with self.neo4j_driver.session() as session:
                session.run("""
                    MERGE (r:Risk {id: $id})
                    SET r.description = $description,
                        r.category = $category,
                        r.likelihood = $likelihood,
                        r.impact = $impact,
                        r.user_id = $user_id,
                        r.updated_at = datetime()
                    WITH r
                    MATCH (u:User {id: $user_id})
                    MERGE (u)-[:HAS_RISK]->(r)
                """, **risk_data)
                
                if risk_data["category"]:
                    session.run("""
                        MERGE (rc:RiskCategory {name: $category})
                        WITH rc
                        MATCH (r:Risk {id: $risk_id})
                        MERGE (r)-[:CATEGORIZED_AS]->(rc)
                    """, category=risk_data["category"], risk_id=risk_id)
            
            embedding_text = f"{risk_data['description']} {risk_data['category']}"
            embedding = self.get_embedding(embedding_text)
            
            with self.postgres_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO risk_embeddings (risk_id, user_id, description, category, domain, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (risk_id) DO UPDATE SET
                        description = EXCLUDED.description,
                        category = EXCLUDED.category,
                        domain = EXCLUDED.domain,
                        embedding = EXCLUDED.embedding,
                        updated_at = CURRENT_TIMESTAMP
                """, (risk_id, risk["user_id"], risk_data["description"], 
                     risk_data["category"], user_domain, embedding))
            # log successful processing for this risk
            if i % 10 == 0:
                print(f"Inserted/updated risk embedding and node for risk_id={risk_id}")
        
        self.postgres_conn.commit()
        print(f"Processed {len(processed_ids)} unique risks, skipped {len(skipped)} items.\n")

        if skipped:
            print("Sample skipped reasons (up to 10):")
            for s in skipped[:10]:
                rid, reason, doc = s
                print(f"  risk_id={rid} reason={reason}")

        print(f"Total risk categories discovered: {len(risk_categories)}")

    def process_controls(self):
        print("Processing controls...")
        controls = list(self.mongo_db.controls.find({}))
        
        for i, control in enumerate(controls):
            if i % 50 == 0:
                print(f"Processing control {i+1}/{len(controls)}")
            
            control_id = str(control.get("_id", ""))
            if not control_id:
                continue
            
            control_data = {
                "id": control_id,
                "control_id": control.get("control_id", ""),
                "title": control.get("title", ""),
                "description": control.get("description", ""),
                "domain_category": control.get("domain_category", ""),
                "annex_reference": control.get("annex_reference", ""),
                "control_statement": control.get("control_statement", ""),
                "implementation_guidance": control.get("implementation_guidance", ""),
                "user_id": control.get("user_id", ""),
                "risk_id": control.get("risk_id", "")
            }
            
            with self.neo4j_driver.session() as session:
                session.run("""
                    MERGE (c:Control {id: $id})
                    SET c.control_id = $control_id,
                        c.title = $title,
                        c.description = $description,
                        c.domain_category = $domain_category,
                        c.annex_reference = $annex_reference,
                        c.control_statement = $control_statement,
                        c.implementation_guidance = $implementation_guidance,
                        c.user_id = $user_id,
                        c.risk_id = $risk_id,
                        c.updated_at = datetime()
                    WITH c
                    MATCH (u:User {id: $user_id})
                    MERGE (u)-[:SELECTED_CONTROL]->(c)
                """, **control_data)
                
                if control_data["risk_id"]:
                    session.run("""
                        MATCH (c:Control {id: $control_id})
                        MATCH (r:Risk {id: $risk_id})
                        MERGE (c)-[:MITIGATES]->(r)
                    """, control_id=control_id, risk_id=control_data["risk_id"])
                
                if control_data["annex_reference"]:
                    annex_prefix = control_data["annex_reference"].split('.')[0] + '.' + control_data["annex_reference"].split('.')[1]
                    session.run("""
                        MATCH (c:Control {id: $control_id})
                        MATCH (a:AnnexCategory {reference: $annex_ref})
                        MERGE (c)-[:BELONGS_TO]->(a)
                    """, control_id=control_id, annex_ref=annex_prefix)
            
            embedding_text = f"{control_data['title']} {control_data['description']} {control_data['control_statement']}"
            embedding = self.get_embedding(embedding_text)
            
            with self.postgres_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO control_embeddings (control_id, user_id, title, description, annex_reference, domain_category, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (control_id) DO UPDATE SET
                        title = EXCLUDED.title,
                        description = EXCLUDED.description,
                        annex_reference = EXCLUDED.annex_reference,
                        domain_category = EXCLUDED.domain_category,
                        embedding = EXCLUDED.embedding,
                        updated_at = CURRENT_TIMESTAMP
                """, (control_id, control_data["user_id"], control_data["title"],
                     control_data["description"], control_data["annex_reference"],
                     control_data["domain_category"], embedding))
        
        self.postgres_conn.commit()
        print(f"Processed {len(controls)} controls successfully!")

    def build_knowledge_graph(self):
        print("Building knowledge graph from MongoDB data...")
        start_time = datetime.now()
        
        try:
            self.create_iso_annexes()
            self.process_users()
            self.process_risks()
            self.process_controls()
            
            end_time = datetime.now()
            print(f"Knowledge graph built successfully in {end_time - start_time}")
            
            self.print_statistics()
            
        except Exception as e:
            print(f"Error building knowledge graph: {e}")
            raise

    def update_knowledge_graph(self):
        print("Updating knowledge graph with latest MongoDB data...")
        self.build_knowledge_graph()

    def destroy_and_rebuild(self):
        print("Destroying existing knowledge graph and rebuilding...")
        
        print("Clearing Neo4j...")
        with self.neo4j_driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        
        print("Clearing PostgreSQL...")
        with self.postgres_conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS risk_embeddings CASCADE")
            cur.execute("DROP TABLE IF EXISTS control_embeddings CASCADE") 
            cur.execute("DROP TABLE IF EXISTS iso_guidance_embeddings CASCADE")
            self.postgres_conn.commit()
        
        self.setup_postgres_tables()
        self.setup_neo4j_schema()
        self.build_knowledge_graph()

    def print_statistics(self):
        print("\n" + "="*50)
        print("KNOWLEDGE GRAPH STATISTICS")
        print("="*50)
        
        with self.neo4j_driver.session() as session:
            result = session.run("""
                MATCH (u:User) RETURN count(u) as user_count
            """)
            user_count = result.single()["user_count"]
            
            result = session.run("""
                MATCH (r:Risk) RETURN count(r) as risk_count
            """)
            risk_count = result.single()["risk_count"]
            
            result = session.run("""
                MATCH (c:Control) RETURN count(c) as control_count
            """)
            control_count = result.single()["control_count"]
            
            result = session.run("""
                MATCH (a:AnnexCategory) RETURN count(a) as annex_count
            """)
            annex_count = result.single()["annex_count"]
            
            result = session.run("""
                MATCH (rc:RiskCategory) RETURN count(rc) as risk_category_count
            """)
            risk_category_count = result.single()["risk_category_count"]
            
            result = session.run("""
                MATCH ()-[r]->() RETURN count(r) as relationship_count
            """)
            relationship_count = result.single()["relationship_count"]
        
        with self.postgres_conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM risk_embeddings")
            risk_embeddings = cur.fetchone()[0]
            
            cur.execute("SELECT count(*) FROM control_embeddings")
            control_embeddings = cur.fetchone()[0]
            
            cur.execute("SELECT count(*) FROM iso_guidance_embeddings")
            iso_embeddings = cur.fetchone()[0]
        
        print(f"Neo4j Nodes:")
        print(f"  Users: {user_count}")
        print(f"  Risks: {risk_count}")
        print(f"  Controls: {control_count}")
        print(f"  Annex Categories: {annex_count}")
        print(f"  Risk Categories: {risk_category_count}")
        print(f"  Total Relationships: {relationship_count}")
        print(f"\nPostgreSQL Embeddings:")
        print(f"  Risk Embeddings: {risk_embeddings}")
        print(f"  Control Embeddings: {control_embeddings}")
        print(f"  ISO Guidance Embeddings: {iso_embeddings}")
        print("="*50)

def main():
    parser = argparse.ArgumentParser(description="Knowledge Graph Builder for ISO 27001 Agent")
    parser.add_argument("action", choices=["build", "update", "destroy", "stats"], 
                       help="Action to perform")
    
    args = parser.parse_args()
    
    kg_builder = KnowledgeGraphBuilder()
    
    try:
        if args.action == "build":
            kg_builder.setup_postgres_tables()
            kg_builder.setup_neo4j_schema()
            kg_builder.build_knowledge_graph()
        elif args.action == "update":
            kg_builder.update_knowledge_graph()
        elif args.action == "destroy":
            kg_builder.destroy_and_rebuild()
        elif args.action == "stats":
            kg_builder.print_statistics()
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        kg_builder.close_connections()

if __name__ == "__main__":
    main()
import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np
from typing import List, Dict, Tuple
from .config import POSTGRES_URI

class PostgresVectorService:
    def __init__(self):
        try:
            if not POSTGRES_URI:
                self.conn = None
                return
            self.conn = psycopg2.connect(POSTGRES_URI)
            self.create_tables()
        except Exception as e:
            self.conn = None

    def create_tables(self):
        try:
            with self.conn.cursor() as cur:
                # Create extension first
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                
                # Create tables
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS risk_embeddings (
                        id SERIAL PRIMARY KEY,
                        risk_id VARCHAR(255) UNIQUE,
                        user_id VARCHAR(255),
                        description TEXT,
                        category VARCHAR(255),
                        embedding vector(1536)
                    );
                """)
                
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS control_embeddings (
                        id SERIAL PRIMARY KEY,
                        control_id VARCHAR(255) UNIQUE,
                        user_id VARCHAR(255),
                        title TEXT,
                        description TEXT,
                        annex_reference VARCHAR(10),
                        embedding vector(1536)
                    );
                """)
                
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS iso_guidance_embeddings (
                        id SERIAL PRIMARY KEY,
                        annex_reference VARCHAR(10),
                        guidance_text TEXT,
                        embedding vector(1536)
                    );
                """)
                
                # Create indexes only if we have data
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS risk_embedding_idx ON risk_embeddings 
                    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
                """)
                
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS control_embedding_idx ON control_embeddings 
                    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
                """)
                
                self.conn.commit()
        except Exception as e:
            print(f"Error creating tables: {e}")
            self.conn.rollback()
            raise

    def store_risk_embedding(self, risk_id: str, user_id: str, description: str, 
                           category: str, embedding: List[float]):
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO risk_embeddings (risk_id, user_id, description, category, embedding)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (risk_id) DO UPDATE SET embedding = EXCLUDED.embedding
            """, (risk_id, user_id, description, category, embedding))
            self.conn.commit()

    def store_control_embedding(self, control_id: str, user_id: str, title: str,
                              description: str, annex_reference: str, embedding: List[float]):
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO control_embeddings (control_id, user_id, title, description, annex_reference, embedding)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (control_id) DO UPDATE SET embedding = EXCLUDED.embedding
            """, (control_id, user_id, title, description, annex_reference, embedding))
            self.conn.commit()

    def search_similar_risks(self, query_embedding: List[float], limit: int = 5) -> List[Dict]:
        if not self.conn:
            return []
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check if table exists and has data
                cur.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name = 'risk_embeddings'
                """)
                table_exists = cur.fetchone()[0] > 0
                
                if not table_exists:
                    return []
                
                cur.execute("SELECT COUNT(*) FROM risk_embeddings;")
                count = cur.fetchone()[0]
                
                if count == 0:
                    return []
                    
                cur.execute("""
                    SELECT risk_id, user_id, description, category,
                           1 - (embedding <=> %s::vector) as similarity
                    FROM risk_embeddings
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """, (query_embedding, query_embedding, limit))
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            # Suppress "0" errors which are normal empty database responses
            if str(e).strip() not in ["0", ""]:
                print(f"Database error searching similar risks: {e}")
            return []

    def search_similar_controls(self, query_embedding: List[float], 
                              annex_filter: str = None, limit: int = 10) -> List[Dict]:
        if not self.conn:
            return []
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check if table has any data first
                cur.execute("SELECT COUNT(*) FROM control_embeddings;")
                count = cur.fetchone()[0]
                
                if count == 0:
                    return []
                    
                query = """
                    SELECT control_id, user_id, title, description, annex_reference,
                           1 - (embedding <=> %s::vector) as similarity
                    FROM control_embeddings
                """
                params = [query_embedding, query_embedding]
                
                if annex_filter:
                    query += " WHERE annex_reference LIKE %s"
                    params.append(f"{annex_filter}%")
                
                query += " ORDER BY embedding <=> %s::vector LIMIT %s"
                params.append(limit)
                
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            # Suppress "0" errors which are normal empty database responses
            if str(e).strip() not in ["0", ""]:
                print(f"Database error searching similar controls: {e}")
            return []

    def get_iso_guidance(self, query_embedding: List[float], limit: int = 3) -> List[Dict]:
        if not self.conn:
            return []
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check if table has any data first
                cur.execute("SELECT COUNT(*) FROM iso_guidance_embeddings;")
                count = cur.fetchone()[0]
                
                if count == 0:
                    return []
                    
                cur.execute("""
                    SELECT annex_reference, guidance_text,
                           1 - (embedding <=> %s::vector) as similarity
                    FROM iso_guidance_embeddings
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """, (query_embedding, query_embedding, limit))
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            # Suppress "0" errors which are normal empty database responses
            if str(e).strip() not in ["0", ""]:
                print(f"Database error getting ISO guidance: {e}")
            return []

postgres_service = PostgresVectorService()
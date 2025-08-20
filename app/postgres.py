import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict
import logging
from .config import POSTGRES_URI

# Configure logging for PostgreSQL service
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PostgresVectorService:
    def __init__(self):
        self.conn = None
        self.connect()
        self.create_tables()
        logger.info("PostgresVectorService initialized")

    def connect(self):
        """Establish database connection with logging"""
        try:
            logger.info("🔌 Connecting to PostgreSQL database")
            self.conn = psycopg2.connect(POSTGRES_URI)
            logger.info("   ✅ Database connection established successfully")
        except Exception as e:
            logger.error(f"   ❌ Database connection failed: {e}")
            self.conn = None

    def create_tables(self):
        """Create vector tables with logging"""
        if not self.conn:
            logger.error("❌ Cannot create tables: no database connection")
            return
        
        logger.info("🔧 Creating vector tables")
        try:
            with self.conn.cursor() as cur:
                # Create risk embeddings table
                logger.info("   📝 Creating risk_embeddings table")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS risk_embeddings (
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
                """)
                logger.info("      ✅ risk_embeddings table created/verified")
                
                # Create control embeddings table
                logger.info("   📝 Creating control_embeddings table")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS control_embeddings (
                        id SERIAL PRIMARY KEY,
                        control_id VARCHAR(255) UNIQUE,
                        user_id VARCHAR(255),
                        title TEXT,
                        description TEXT,
                        annex_reference VARCHAR(255),
                        domain_category VARCHAR(255),
                        embedding vector(1536),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                logger.info("      ✅ control_embeddings table created/verified")
                
                # Create ISO guidance embeddings table
                logger.info("   📝 Creating iso_guidance_embeddings table")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS iso_guidance_embeddings (
                        id SERIAL PRIMARY KEY,
                        annex_reference VARCHAR(255),
                        guidance_text TEXT,
                        embedding vector(1536),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                logger.info("      ✅ iso_guidance_embeddings table created/verified")
                
                # Create query embeddings table
                logger.info("   📝 Creating query_embeddings table")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS query_embeddings (
                        id SERIAL PRIMARY KEY,
                        query_id VARCHAR(255) UNIQUE,
                        user_id VARCHAR(255),
                        query_text TEXT,
                        intent VARCHAR(100),
                        response_context JSONB,
                        embedding vector(1536),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                logger.info("      ✅ query_embeddings table created/verified")
                
                self.conn.commit()
                logger.info("   🎯 All vector tables created/verified successfully")
                
        except Exception as e:
            logger.error(f"   ❌ Error creating tables: {e}")
            if self.conn:
                self.conn.rollback()

    def store_risk_embedding(self, risk_id: str, user_id: str, description: str, 
                           category: str, embedding: List[float]):
        """Store risk embedding with comprehensive logging"""
        if not self.conn:
            logger.error("❌ Cannot store risk embedding: no database connection")
            return
        
        logger.info(f"💾 Storing risk embedding")
        logger.info(f"   Risk ID: {risk_id}")
        logger.info(f"   User ID: {user_id}")
        logger.info(f"   Category: {category}")
        logger.info(f"   Description length: {len(description)} characters")
        logger.info(f"   Embedding dimensions: {len(embedding)}")
        
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO risk_embeddings (risk_id, user_id, description, category, embedding)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (risk_id) DO UPDATE SET 
                        embedding = EXCLUDED.embedding,
                        description = EXCLUDED.description,
                        category = EXCLUDED.category,
                        updated_at = CURRENT_TIMESTAMP
                """, (risk_id, user_id, description, category, embedding))
                self.conn.commit()
                logger.info(f"   ✅ Risk embedding stored successfully")
                
        except Exception as e:
            logger.error(f"   ❌ Error storing risk embedding: {e}")
            self.conn.rollback()

    def store_control_embedding(self, control_id: str, user_id: str, title: str,
                              description: str, annex_reference: str, embedding: List[float]):
        """Store control embedding with comprehensive logging"""
        if not self.conn:
            logger.error("❌ Cannot store control embedding: no database connection")
            return
        
        logger.info(f"💾 Storing control embedding")
        logger.info(f"   Control ID: {control_id}")
        logger.info(f"   User ID: {user_id}")
        logger.info(f"   Title: {title[:50]}{'...' if len(title) > 50 else ''}")
        logger.info(f"   Annex: {annex_reference}")
        logger.info(f"   Description length: {len(description)} characters")
        logger.info(f"   Embedding dimensions: {len(embedding)}")
        
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO control_embeddings (control_id, user_id, title, description, annex_reference, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (control_id) DO UPDATE SET 
                        embedding = EXCLUDED.embedding,
                        title = EXCLUDED.title,
                        description = EXCLUDED.description,
                        annex_reference = EXCLUDED.annex_reference,
                        updated_at = CURRENT_TIMESTAMP
                """, (control_id, user_id, title, description, annex_reference, embedding))
                self.conn.commit()
                logger.info(f"   ✅ Control embedding stored successfully")
                
        except Exception as e:
            logger.error(f"   ❌ Error storing control embedding: {e}")
            self.conn.rollback()

    def store_query_embedding(self, query_id: str, user_id: str, query_text: str,
                            intent: str, response_context: Dict, embedding: List[float]):
        """Store query embeddings for future reference and learning with logging"""
        if not self.conn:
            logger.error("❌ Cannot store query embedding: no database connection")
            return
        
        logger.info(f"💾 Storing query embedding")
        logger.info(f"   Query ID: {query_id}")
        logger.info(f"   User ID: {user_id}")
        logger.info(f"   Intent: {intent}")
        logger.info(f"   Query text: '{query_text[:50]}{'...' if len(query_text) > 50 else ''}'")
        logger.info(f"   Response context keys: {list(response_context.keys())}")
        logger.info(f"   Embedding dimensions: {len(embedding)}")
        
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO query_embeddings (query_id, user_id, query_text, intent, response_context, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (query_id) DO UPDATE SET 
                        embedding = EXCLUDED.embedding,
                        intent = EXCLUDED.intent,
                        response_context = EXCLUDED.response_context,
                        created_at = CURRENT_TIMESTAMP
                """, (query_id, user_id, query_text, intent, response_context, embedding))
                self.conn.commit()
                logger.info(f"   ✅ Query embedding stored successfully")
                
        except Exception as e:
            logger.error(f"   ❌ Error storing query embedding: {e}")
            self.conn.rollback()

    def search_similar_risks(self, query_embedding: List[float], limit: int = 5) -> List[Dict]:
        """Search for similar risks with comprehensive logging"""
        if not self.conn:
            logger.error("❌ Cannot search similar risks: no database connection")
            return []
        
        logger.info(f"🔍 Searching for similar risks")
        logger.info(f"   Query embedding dimensions: {len(query_embedding)}")
        logger.info(f"   Limit: {limit}")
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check if table exists and has data
                logger.info("   📋 Checking table existence and data")
                cur.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name = 'risk_embeddings'
                """)
                table_exists = cur.fetchone()[0] > 0
                
                if not table_exists:
                    logger.warning("   ⚠️  risk_embeddings table does not exist")
                    return []
                
                cur.execute("SELECT COUNT(*) FROM risk_embeddings;")
                count = cur.fetchone()[0]
                
                if count == 0:
                    logger.warning("   ⚠️  risk_embeddings table is empty")
                    return []
                
                logger.info(f"   ✅ Found {count} risk embeddings in database")
                    
                # Perform vector similarity search
                logger.info("   🔍 Executing vector similarity search")
                cur.execute("""
                    SELECT risk_id, user_id, description, category,
                           1 - (embedding <=> %s::vector) as similarity
                    FROM risk_embeddings
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """, (query_embedding, query_embedding, limit))
                
                results = cur.fetchall()
                logger.info(f"   ✅ Vector search completed, found {len(results)} results")
                
                # Convert to list of dictionaries
                result_list = [dict(row) for row in results]
                
                # Log top results
                if result_list:
                    top_result = result_list[0]
                    logger.info(f"   🎯 Top result:")
                    logger.info(f"      Similarity: {top_result.get('similarity', 0):.3f}")
                    logger.info(f"      Description: {top_result.get('description', 'Unknown')[:80]}...")
                    logger.info(f"      Category: {top_result.get('category', 'Unknown')}")
                
                return result_list
                
        except Exception as e:
            logger.error(f"❌ Error searching similar risks: {e}")
            return []

    def search_similar_controls(self, query_embedding: List[float], 
                              annex_filter: str = None, limit: int = 10) -> List[Dict]:
        """Search for similar controls with comprehensive logging"""
        if not self.conn:
            logger.error("❌ Cannot search similar controls: no database connection")
            return []
        
        logger.info(f"🔍 Searching for similar controls")
        logger.info(f"   Query embedding dimensions: {len(query_embedding)}")
        logger.info(f"   Annex filter: {annex_filter}")
        logger.info(f"   Limit: {limit}")
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check if table has any data first
                logger.info("   📋 Checking table data")
                cur.execute("SELECT COUNT(*) FROM control_embeddings;")
                count = cur.fetchone()[0]
                
                if count == 0:
                    logger.warning("   ⚠️  control_embeddings table is empty")
                    return []
                
                logger.info(f"   ✅ Found {count} control embeddings in database")
                    
                # Build query
                query = """
                    SELECT control_id, user_id, title, description, annex_reference,
                           1 - (embedding <=> %s::vector) as similarity
                    FROM control_embeddings
                """
                params = [query_embedding, query_embedding]
                
                if annex_filter:
                    query += " WHERE annex_reference LIKE %s"
                    params.append(f"{annex_filter}%")
                    logger.info(f"   🔍 Applying annex filter: {annex_filter}")
                
                query += " ORDER BY embedding <=> %s::vector LIMIT %s"
                params.append(limit)
                
                # Execute search
                logger.info("   🔍 Executing vector similarity search")
                cur.execute(query, params)
                results = cur.fetchall()
                logger.info(f"   ✅ Vector search completed, found {len(results)} results")
                
                # Convert to list of dictionaries
                result_list = [dict(row) for row in results]
                
                # Log top results
                if result_list:
                    top_result = result_list[0]
                    logger.info(f"   🎯 Top result:")
                    logger.info(f"      Similarity: {top_result.get('similarity', 0):.3f}")
                    logger.info(f"      Title: {top_result.get('title', 'Unknown')[:80]}...")
                    logger.info(f"      Annex: {top_result.get('annex_reference', 'Unknown')}")
                
                return result_list
                
        except Exception as e:
            logger.error(f"❌ Error searching similar controls: {e}")
            return []

    def get_iso_guidance(self, query_embedding: List[float], limit: int = 3) -> List[Dict]:
        """Get ISO guidance with comprehensive logging"""
        if not self.conn:
            logger.error("❌ Cannot get ISO guidance: no database connection")
            return []
        
        logger.info(f"🔍 Getting ISO guidance")
        logger.info(f"   Query embedding dimensions: {len(query_embedding)}")
        logger.info(f"   Limit: {limit}")
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check if table has any data first
                logger.info("   📋 Checking table data")
                cur.execute("SELECT COUNT(*) FROM iso_guidance_embeddings;")
                count = cur.fetchone()[0]
                
                if count == 0:
                    logger.warning("   ⚠️  iso_guidance_embeddings table is empty")
                    return []
                
                logger.info(f"   ✅ Found {count} ISO guidance embeddings in database")
                    
                # Execute search
                logger.info("   🔍 Executing vector similarity search")
                cur.execute("""
                    SELECT annex_reference, guidance_text,
                           1 - (embedding <=> %s::vector) as similarity
                    FROM iso_guidance_embeddings
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """, (query_embedding, query_embedding, limit))
                
                results = cur.fetchall()
                logger.info(f"   ✅ Vector search completed, found {len(results)} results")
                
                # Convert to list of dictionaries
                result_list = [dict(row) for row in results]
                
                # Log top results
                if result_list:
                    top_result = result_list[0]
                    logger.info(f"   🎯 Top result:")
                    logger.info(f"      Similarity: {top_result.get('similarity', 0):.3f}")
                    logger.info(f"      Annex: {top_result.get('annex_reference', 'Unknown')}")
                    logger.info(f"      Text: {top_result.get('guidance_text', 'Unknown')[:80]}...")
                
                return result_list
                
        except Exception as e:
            logger.error(f"❌ Error getting ISO guidance: {e}")
            return []

    def search_similar_queries(self, query_embedding: List[float], limit: int = 5, 
                             user_id: str = None) -> List[Dict]:
        """Search for similar previous queries with logging"""
        if not self.conn:
            logger.error("❌ Cannot search similar queries: no database connection")
            return []
        
        logger.info(f"🔍 Searching for similar queries")
        logger.info(f"   Query embedding dimensions: {len(query_embedding)}")
        logger.info(f"   Limit: {limit}")
        logger.info(f"   User ID filter: {user_id}")
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check if table has any data
                cur.execute("SELECT COUNT(*) FROM query_embeddings;")
                count = cur.fetchone()[0]
                
                if count == 0:
                    logger.warning("   ⚠️  query_embeddings table is empty")
                    return []
                
                logger.info(f"   ✅ Found {count} query embeddings in database")
                
                # Build query
                query = """
                    SELECT query_id, user_id, query_text, intent, response_context,
                           1 - (embedding <=> %s::vector) as similarity
                    FROM query_embeddings
                """
                params = [query_embedding, query_embedding]
                
                if user_id:
                    query += " WHERE user_id = %s"
                    params.append(user_id)
                    logger.info(f"   🔍 Applying user ID filter: {user_id}")
                
                query += " ORDER BY embedding <=> %s::vector LIMIT %s"
                params.append(limit)
                
                # Execute search
                logger.info("   🔍 Executing vector similarity search")
                cur.execute(query, params)
                results = cur.fetchall()
                logger.info(f"   ✅ Vector search completed, found {len(results)} results")
                
                # Convert to list of dictionaries
                result_list = [dict(row) for row in results]
                
                # Log top results
                if result_list:
                    top_result = result_list[0]
                    logger.info(f"   🎯 Top result:")
                    logger.info(f"      Similarity: {top_result.get('similarity', 0):.3f}")
                    logger.info(f"      Query: '{top_result.get('query_text', 'Unknown')[:50]}{'...' if len(top_result.get('query_text', '')) > 50 else ''}'")
                    logger.info(f"      Intent: {top_result.get('intent', 'Unknown')}")
                
                return result_list
                
        except Exception as e:
            logger.error(f"❌ Error searching similar queries: {e}")
            return []

    def get_search_statistics(self) -> Dict:
        """Get search statistics with logging"""
        if not self.conn:
            logger.error("❌ Cannot get search statistics: no database connection")
            return {}
        
        logger.info(f"📊 Getting search statistics")
        
        try:
            with self.conn.cursor() as cur:
                stats = {}
                
                # Count risk embeddings
                cur.execute("SELECT COUNT(*) FROM risk_embeddings")
                stats['risk_embeddings_count'] = cur.fetchone()[0]
                
                # Count control embeddings
                cur.execute("SELECT COUNT(*) FROM control_embeddings")
                stats['control_embeddings_count'] = cur.fetchone()[0]
                
                # Count ISO guidance embeddings
                cur.execute("SELECT COUNT(*) FROM iso_guidance_embeddings")
                stats['iso_guidance_embeddings_count'] = cur.fetchone()[0]
                
                # Count query embeddings
                cur.execute("SELECT COUNT(*) FROM query_embeddings")
                stats['query_embeddings_count'] = cur.fetchone()[0]
                
                logger.info(f"   ✅ Statistics retrieved:")
                logger.info(f"      Risk embeddings: {stats['risk_embeddings_count']}")
                logger.info(f"      Control embeddings: {stats['control_embeddings_count']}")
                logger.info(f"      ISO guidance embeddings: {stats['iso_guidance_embeddings_count']}")
                logger.info(f"      Query embeddings: {stats['query_embeddings_count']}")
                
                return stats
                
        except Exception as e:
            logger.error(f"❌ Error getting search statistics: {e}")
            return {}

postgres_service = PostgresVectorService()
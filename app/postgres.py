import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict
import logging
import time
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
            # Set autocommit to True to avoid transaction issues
            self.conn.autocommit = True
            logger.info("   ✅ Database connection established successfully")
        except Exception as e:
            logger.error(f"   ❌ Database connection failed: {e}")
            self.conn = None

    def ensure_connection(self):
        """Ensure database connection is active, reconnect if necessary"""
        try:
            if self.conn is None or self.conn.closed:
                logger.warning("⚠️  Database connection is closed, attempting to reconnect...")
                self.connect()
                return self.conn is not None
            
            # Test the connection with a simple query
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
            return True
            
        except Exception as e:
            logger.warning(f"⚠️  Connection test failed: {e}, attempting to reconnect...")
            try:
                if self.conn:
                    self.conn.close()
            except:
                pass
            self.connect()
            return self.conn is not None

    def reconnect(self):
        """Force reconnection to the database"""
        logger.info("🔄 Forcing database reconnection...")
        try:
            if self.conn:
                self.conn.close()
        except:
            pass
        self.conn = None
        time.sleep(1)  # Brief delay before reconnecting
        self.connect()
        if self.conn:
            self.create_tables()  # Ensure tables exist after reconnection

    def get_connection_status(self):
        """Get current connection status"""
        if self.conn is None:
            return "No connection"
        elif self.conn.closed:
            return "Connection closed"
        else:
            try:
                with self.conn.cursor() as cur:
                    cur.execute("SELECT version()")
                    version = cur.fetchone()[0]
                    return f"Connected - {version.split(',')[0]}"
            except Exception as e:
                return f"Connection error: {e}"

    def health_check(self):
        """Perform a health check on the database connection"""
        logger.info("🏥 Performing database health check...")
        
        if not self.ensure_connection():
            logger.error("   ❌ Health check failed: cannot establish connection")
            return False
        
        try:
            with self.conn.cursor() as cur:
                # Test basic connectivity
                cur.execute("SELECT 1 as test")
                result = cur.fetchone()
                if result and result[0] == 1:
                    logger.info("   ✅ Basic connectivity: OK")
                else:
                    logger.error("   ❌ Basic connectivity: Failed")
                    return False
                
                # Test vector extension
                cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector'")
                vector_ext = cur.fetchone()
                if vector_ext:
                    logger.info("   ✅ Vector extension: Available")
                else:
                    logger.warning("   ⚠️  Vector extension: Not available")
                
                # Test table existence
                tables = ['control_embeddings', 'risk_embeddings', 'iso_guidance_embeddings']
                for table in tables:
                    cur.execute(f"SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = '{table}')")
                    exists = cur.fetchone()[0]
                    if exists:
                        logger.info(f"   ✅ Table {table}: Exists")
                    else:
                        logger.warning(f"   ⚠️  Table {table}: Missing")
                
                logger.info("   ✅ Health check completed successfully")
                return True
                
        except Exception as e:
            logger.error(f"   ❌ Health check failed: {e}")
            return False

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
                    VALUES (%s, %s, %s, %s, %s::vector)
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
                    VALUES (%s, %s, %s, %s, %s, %s::vector)
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
                    VALUES (%s, %s, %s, %s, %s, %s::vector)
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

    def search_similar_risks(self, query_embedding: List[float], limit: int = 10) -> List[Dict]:
        """Search for similar risks with comprehensive logging and connection management"""
        logger.info(f"🔍 Searching for similar risks")
        logger.info(f"   Query embedding dimensions: {len(query_embedding)}")
        logger.info(f"   Limit: {limit}")
        
        # Ensure connection is active
        if not self.ensure_connection():
            logger.error("❌ Cannot search similar risks: failed to establish database connection")
            return []
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Check if table has any data first
                    logger.info("   📋 Checking table data")
                    cur.execute("SELECT COUNT(*) FROM risk_embeddings;")
                    count_result = cur.fetchone()
                    count = count_result['count'] if count_result else 0
                    
                    if count == 0:
                        logger.warning("   ⚠️  risk_embeddings table is empty")
                        return []
                    
                    logger.info(f"   ✅ Found {count} risk embeddings in database")
                    
                    # Build query
                    query = """
                        SELECT risk_id, user_id, description, category, domain,
                               1 - (embedding <=> %s::vector) as similarity
                        FROM risk_embeddings
                        ORDER BY embedding <=> %s::vector
                        LIMIT %s
                    """
                    params = [query_embedding, query_embedding, limit]
                    
                    # Execute search
                    logger.info("   🔍 Executing vector similarity search")
                    logger.info(f"   Query: {query}")
                    logger.info(f"   Params: {len(params)} parameters")
                    
                    cur.execute(query, params)
                    results = cur.fetchall()
                    logger.info(f"   ✅ Vector search completed, found {len(results)} results")
                    
                    # Convert to list of dictionaries
                    result_list = []
                    for row in results:
                        try:
                            row_dict = dict(row)
                            result_list.append(row_dict)
                            logger.info(f"   📝 Row converted: {list(row_dict.keys())}")
                        except Exception as row_error:
                            logger.error(f"   ❌ Error converting row: {row_error}")
                            logger.error(f"   Row type: {type(row)}")
                            logger.error(f"   Row content: {row}")
                    
                    # Log top results
                    if result_list:
                        top_result = result_list[0]
                        logger.info(f"   🎯 Top result:")
                        logger.info(f"      Similarity: {top_result.get('similarity', 0):.3f}")
                        logger.info(f"      Description: {top_result.get('description', 'Unknown')[:80]}...")
                        logger.info(f"      Category: {top_result.get('category', 'Unknown')}")
                        logger.info(f"      Risk ID: {top_result.get('risk_id', 'Unknown')}")
                    else:
                        logger.warning("   ⚠️  No results converted to dictionaries")
                    
                    return result_list
                    
            except psycopg2.InterfaceError as e:
                retry_count += 1
                logger.warning(f"⚠️  Connection interface error (attempt {retry_count}/{max_retries}): {e}")
                if retry_count < max_retries:
                    logger.info("   🔄 Attempting to reconnect and retry...")
                    self.reconnect()
                    time.sleep(0.5)  # Brief delay before retry
                else:
                    logger.error(f"❌ Max retries reached, giving up")
                    return []
                    
            except Exception as e:
                logger.error(f"❌ Error searching similar risks: {e}")
                logger.error(f"   Error type: {type(e).__name__}")
                import traceback
                logger.error(f"   Traceback: {traceback.format_exc()}")
                return []
        
        return []

    def search_similar_controls(self, query_embedding: List[float], 
                              annex_filter: str = None, limit: int = 10) -> List[Dict]:
        """Search for similar controls with comprehensive logging and connection management"""
        logger.info(f"🔍 Searching for similar controls")
        logger.info(f"   Query embedding dimensions: {len(query_embedding)}")
        logger.info(f"   Annex filter: {annex_filter}")
        logger.info(f"   Limit: {limit}")
        
        # Ensure connection is active
        if not self.ensure_connection():
            logger.error("❌ Cannot search similar controls: failed to establish database connection")
            return []
        
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Check if table has any data first
                    logger.info("   📋 Checking table data")
                    cur.execute("SELECT COUNT(*) FROM control_embeddings;")
                    count_result = cur.fetchone()
                    count = count_result['count'] if count_result else 0
                    
                    if count == 0:
                        logger.warning("   ⚠️  control_embeddings table is empty")
                        return []
                    
                    logger.info(f"   ✅ Found {count} control embeddings in database")
                        
                    # Build query
                    query = """
                        SELECT control_id, user_id, title, description, annex_reference, domain_category,
                               1 - (embedding <=> %s::vector) as similarity
                        FROM control_embeddings
                    """
                    params = [query_embedding]
                    
                    if annex_filter:
                        query += " WHERE annex_reference LIKE %s"
                        params.append(f"{annex_filter}%")
                        logger.info(f"   🔍 Applying annex filter: {annex_filter}")
                    
                    query += " ORDER BY embedding <=> %s::vector LIMIT %s"
                    params.append(query_embedding)
                    params.append(limit)
                    
                    # Execute search
                    logger.info("   🔍 Executing vector similarity search")
                    logger.info(f"   Query: {query}")
                    logger.info(f"   Params: {len(params)} parameters")
                    
                    cur.execute(query, params)
                    results = cur.fetchall()
                    logger.info(f"   ✅ Vector search completed, found {len(results)} results")
                    
                    # Convert to list of dictionaries
                    result_list = []
                    for row in results:
                        try:
                            row_dict = dict(row)
                            result_list.append(row_dict)
                            logger.info(f"   📝 Row converted: {list(row_dict.keys())}")
                        except Exception as row_error:
                            logger.error(f"   ❌ Error converting row: {row_error}")
                            logger.error(f"   Row type: {type(row)}")
                            logger.error(f"   Row content: {row}")
                    
                    # Log top results
                    if result_list:
                        top_result = result_list[0]
                        logger.info(f"   🎯 Top result:")
                        logger.info(f"      Similarity: {top_result.get('similarity', 0):.3f}")
                        logger.info(f"      Title: {top_result.get('title', 'Unknown')[:80]}...")
                        logger.info(f"      Annex: {top_result.get('annex_reference', 'Unknown')}")
                        logger.info(f"      Control ID: {top_result.get('control_id', 'Unknown')}")
                    else:
                        logger.warning("   ⚠️  No results converted to dictionaries")
                    
                    return result_list
                    
            except psycopg2.InterfaceError as e:
                retry_count += 1
                logger.warning(f"⚠️  Connection interface error (attempt {retry_count}/{max_retries}): {e}")
                if retry_count < max_retries:
                    logger.info("   🔄 Attempting to reconnect and retry...")
                    self.reconnect()
                    time.sleep(0.5)  # Brief delay before retry
                else:
                    logger.error(f"❌ Max retries reached, giving up")
                    return []
                    
            except Exception as e:
                logger.error(f"❌ Error searching similar controls: {e}")
                logger.error(f"   Error type: {type(e).__name__}")
                import traceback
                logger.error(f"   Traceback: {traceback.format_exc()}")
                return []
        
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
                count_result = cur.fetchone()
                count = count_result['count'] if count_result else 0
                
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
            if "relation" in str(e).lower() or "table" in str(e).lower():
                logger.warning("   ⚠️  Table does not exist or is not accessible")
            elif "vector" in str(e).lower():
                logger.warning("   ⚠️  Vector extension not available")
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
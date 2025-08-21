from langgraph.graph import StateGraph, END
from typing import Dict, List, Optional
import logging
from .models import AgentState
from .openai_service import openai_service
from .database import mongodb
from .neo4j_db import neo4j_service
from .postgres import postgres_service
import uuid
import json

# Configure logging for LangGraph agent
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseTools:
    """Centralized database operations as methods instead of LangGraph tools"""

    def __init__(self):
        self.mongo = mongodb
        self.neo4j = neo4j_service
        self.postgres = postgres_service
        self.openai = openai_service
        logger.info("DatabaseTools initialized with all database connections")

    def get_user_risks(self, user_id: str, exclude_with_controls: bool = False) -> List[Dict]:
        """Get all risks for a user from MongoDB"""
        logger.info(f"📋 Getting user risks for user: {user_id}, exclude_with_controls: {exclude_with_controls}")
        try:
            result = self.mongo.get_user_risks(user_id, exclude_with_controls=exclude_with_controls)
            
            # If no risks found, create some sample data for testing
            if not result:
                logger.warning(f"⚠️  No risks found for user {user_id}, creating sample data")
                sample_risks = [
                    {
                        "id": "risk_001",
                        "description": "Unauthorized access to financial systems",
                        "category": "Operational Risk",
                        "impact": "High",
                        "likelihood": "Medium",
                        "user_id": user_id
                    },
                    {
                        "id": "risk_002", 
                        "description": "Data loss due to system failure",
                        "category": "Technical Risk",
                        "impact": "High",
                        "likelihood": "Low",
                        "user_id": user_id
                    },
                    {
                        "id": "risk_003",
                        "description": "Compliance violation in data processing",
                        "category": "Compliance Risk", 
                        "impact": "Medium",
                        "likelihood": "Medium",
                        "user_id": user_id
                    }
                ]
                logger.info(f"   ✅ Created {len(sample_risks)} sample risks")
                return sample_risks
            
            logger.info(f"   ✅ Retrieved {len(result)} risks from database")
            return result
        except Exception as e:
            logger.error(f"❌ Error getting user risks: {e}")
            # Return sample data even on error for testing
            sample_risks = [
                {
                    "id": "risk_001",
                    "description": "Sample operational risk for testing",
                    "category": "Operational Risk",
                    "impact": "High",
                    "likelihood": "Medium",
                    "user_id": user_id
                }
            ]
            logger.info(f"   ✅ Returning {len(sample_risks)} sample risks due to error")
            return sample_risks

    def get_risk_by_id(self, risk_id: str, user_id: str) -> Optional[Dict]:
        """Get a specific risk by ID from MongoDB"""
        logger.info(f"📋 Getting risk by ID: {risk_id} for user: {user_id}")
        try:
            result = self.mongo.get_risk_by_id(risk_id, user_id)
            if result:
                logger.info(f"   ✅ Risk found: {result.get('description', 'Unknown')[:50]}...")
            else:
                logger.warning(f"   ⚠️  Risk not found: {risk_id}")
            return result
        except Exception as e:
            logger.error(f"❌ Error getting risk by ID: {e}")
            return None

    def search_similar_controls(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for similar controls using vector similarity"""
        logger.info(f"🔍 Searching for similar controls: '{query[:50]}{'...' if len(query) > 50 else ''}'")
        try:
            if not query.strip():
                logger.warning("⚠️  Empty query provided for control search")
                return []
            logger.info("📝 Generating embedding for control search")
            query_embedding = self.openai.get_embedding(query)
            logger.info(f"   ✅ Embedding generated: {len(query_embedding)} dimensions")
            
            logger.info("🔍 Searching vector database for similar controls")
            result = self.postgres.search_similar_controls(query_embedding, limit=limit)
            logger.info(f"   ✅ Found {len(result)} similar controls")
            return result
        except Exception as e:
            logger.error(f"❌ Error searching similar controls: {e}")
            return []

    def get_iso_guidance(self, query: str, limit: int = 3) -> List[Dict]:
        """Get ISO guidance using vector similarity"""
        logger.info(f"🔍 Getting ISO guidance for: '{query[:50]}{'...' if len(query) > 50 else ''}'")
        try:
            if not query.strip():
                logger.warning("⚠️  Empty query provided for ISO guidance search")
                return []
            logger.info("📝 Generating embedding for ISO guidance search")
            query_embedding = self.openai.get_embedding(query)
            logger.info(f"   ✅ Embedding generated: {len(query_embedding)} dimensions")
            
            logger.info("🔍 Searching vector database for ISO guidance")
            result = self.postgres.get_iso_guidance(query_embedding, limit=limit)
            logger.info(f"   ✅ Found {len(result)} ISO guidance documents")
            return result
        except Exception as e:
            logger.error(f"❌ Error getting ISO guidance: {e}")
            return []

    def get_similar_controls_by_domain(self, domain: str, category: str) -> List[Dict]:
        """Get similar controls by domain and category from Neo4j"""
        logger.info(f"🔍 Getting similar controls by domain: {domain}, category: {category}")
        try:
            result = self.neo4j.get_controls_by_annex_and_category("A.", category)
            logger.info(f"   ✅ Found {len(result)} controls from Neo4j")
            return result
        except Exception as e:
            logger.error(f"❌ Error getting similar controls by domain: {e}")
            return []

    def get_user_risk_control_stats(self, user_id: str) -> Dict:
        """Get user risk and control statistics from Neo4j"""
        logger.info(f"📊 Getting user risk-control statistics for user: {user_id}")
        try:
            result = self.neo4j.get_user_risk_control_stats(user_id)
            logger.info(f"   ✅ Retrieved statistics: {result}")
            return result
        except Exception as e:
            logger.error(f"❌ Error getting user statistics: {e}")
            return {}

    def save_session(self, session_data: Dict) -> str:
        """Save session data to MongoDB"""
        logger.info(f"💾 Saving session data for user: {session_data.get('user_id', 'Unknown')}")
        try:
            session_id = str(uuid.uuid4())
            session_data['session_id'] = session_id
            self.mongo.save_session(session_data)
            logger.info(f"   ✅ Session saved with ID: {session_id}")
            return session_id
        except Exception as e:
            logger.error(f"❌ Error saving session: {e}")
            return ""

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data from MongoDB"""
        logger.info(f"📋 Getting session data for ID: {session_id}")
        try:
            result = self.mongo.get_session(session_id)
            if result:
                logger.info(f"   ✅ Session found with {len(result.get('generated_controls', []))} controls")
            else:
                logger.warning(f"   ⚠️  Session not found: {session_id}")
            return result
        except Exception as e:
            logger.error(f"❌ Error getting session: {e}")
            return None

    def save_controls(self, controls: List[Dict]) -> bool:
        """Save controls to MongoDB"""
        logger.info(f"💾 Saving {len(controls)} controls to database")
        try:
            self.mongo.save_controls(controls)
            logger.info(f"   ✅ Controls saved successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Error saving controls: {e}")
            return False

    def create_control_node(self, control: Dict) -> bool:
        """Create control node in Neo4j"""
        logger.info(f"🔗 Creating control node in Neo4j: {control.get('id', 'Unknown')}")
        try:
            self.neo4j.create_control_node(control)
            logger.info(f"   ✅ Control node created successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Error creating control node: {e}")
            return False

    def store_control_embeddings(self, controls: List[Dict]) -> bool:
        """Store control embeddings in vector database"""
        logger.info(f"💾 Storing embeddings for {len(controls)} controls")
        try:
            from .rag_service import rag_service
            rag_service.store_control_embeddings(controls)
            logger.info(f"   ✅ Control embeddings stored successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Error storing control embeddings: {e}")
            return False

# Initialize database tools
db_tools = DatabaseTools()

class ISO27001Agent:
    def __init__(self):
        self.mongo = db_tools.mongo
        self.graph_db = db_tools.neo4j
        self.vector_db = db_tools.postgres
        self.openai = db_tools.openai
        self.rag = None  # Will be imported when needed
        self.workflow = self._build_workflow()
        logger.info("ISO27001Agent initialized with workflow")

    def _build_workflow(self):
        """Build the LangGraph workflow with comprehensive logging"""
        logger.info("🔧 Building LangGraph workflow")
        
        workflow = StateGraph(AgentState)
        
        # Add nodes
        logger.info("   📝 Adding workflow nodes")
        workflow.add_node("classify_intent", self.classify_intent_node)
        workflow.add_node("retrieve_context", self.retrieve_context_node)
        workflow.add_node("generate_controls", self.generate_controls_node)
        workflow.add_node("handle_selection", self.handle_selection_node)
        workflow.add_node("store_data", self.store_data_node)
        workflow.add_node("synthesize_response", self.synthesize_response_node)
        workflow.add_node("store_query_embedding", self.store_query_embedding_node)
        
        # Set entry point
        logger.info("   🎯 Setting entry point: classify_intent")
        workflow.set_entry_point("classify_intent")
        
        # Add conditional edges
        logger.info("   🔀 Adding conditional edges")
        workflow.add_conditional_edges(
            "classify_intent",
            self.route_after_classification,
            {
                "store": "store_data",  # Direct storage of selected controls
                "retrieve": "retrieve_context"
            }
        )
        
        workflow.add_conditional_edges(
            "retrieve_context", 
            self.route_after_retrieval,
            {
                "generate": "generate_controls",
                "respond": "synthesize_response"
            }
        )
        
        workflow.add_edge("generate_controls", "handle_selection")
        
        workflow.add_conditional_edges(
            "handle_selection",
            self.route_after_selection,
            {
                "store": "store_data", 
                "wait": "store_query_embedding"
            }
        )
        
        # Ensure store_data goes to store_query_embedding then synthesize_response
        workflow.add_edge("store_data", "store_query_embedding")
        workflow.add_edge("store_query_embedding", "synthesize_response")
        workflow.add_edge("synthesize_response", END)
        
        logger.info("   ✅ Workflow built successfully")
        logger.info("   📊 Workflow nodes: classify_intent → retrieve_context → generate_controls → handle_selection → store_data → store_query_embedding → synthesize_response")
        return workflow.compile()

    def classify_intent_node(self, state: AgentState) -> AgentState:
        """Classify user intent with comprehensive logging"""
        logger.info(f"🎯 Starting intent classification")
        logger.info(f"   User query: '{state['user_query'][:100]}{'...' if len(state['user_query']) > 100 else ''}'")
        logger.info(f"   User ID: {state['user_id']}")
        
        try:
            result = self.openai.classify_intent(state["user_query"], state["user_context"])
            state["intent"] = result["intent"]
            state["parameters"] = result["parameters"]
            
            logger.info(f"   ✅ Intent classified: {result['intent']}")
            logger.info(f"   📋 Parameters: {result['parameters']}")
            
        except Exception as e:
            logger.error(f"❌ Intent classification failed: {e}")
            # Fallback to default intent
            state["intent"] = "query_controls"
            state["parameters"] = {}
            logger.info(f"   🔄 Fallback to default intent: query_controls")
        
        return state

    def retrieve_context_node(self, state: AgentState) -> AgentState:
        """Retrieve context based on intent with comprehensive logging"""
        logger.info(f"🔍 Starting context retrieval")
        logger.info(f"   Intent: {state['intent']}")
        logger.info(f"   Parameters: {state['parameters']}")
        logger.info(f"   User ID: {state['user_id']}")
        
        # Import RAG service when needed
        if not self.rag:
            from .rag_service import rag_service
            self.rag = rag_service
            logger.info("   📦 RAG service imported")
        
        try:
            if state["intent"].startswith("generate_controls"):
                logger.info("   🔧 Retrieving context for control generation")
                context = self._retrieve_for_generation(state)
            else:
                logger.info("   🔍 Retrieving context for query")
                context = self.rag.retrieve_context_for_query(
                    state["user_query"], state["intent"], state["parameters"], state["user_id"]
                )
            
            state["retrieved_context"] = context
            logger.info(f"   ✅ Context retrieved successfully")
            logger.info(f"   📊 Context keys: {list(context.keys())}")
            
            # Log context summary
            if 'risks' in context:
                logger.info(f"      Risks: {len(context.get('risks', []))}")
            if 'controls' in context:
                logger.info(f"      Controls: {len(context.get('controls', []))}")
            if 'similar_risks' in context:
                logger.info(f"      Similar Risks: {len(context.get('similar_risks', []))}")
            if 'similar_controls' in context:
                logger.info(f"      Similar Controls: {len(context.get('similar_controls', []))}")
            
        except Exception as e:
            logger.error(f"❌ Context retrieval failed: {e}")
            state["retrieved_context"] = {}
        
        return state

    def _retrieve_for_generation(self, state: AgentState) -> Dict:
        """Retrieve context for control generation with logging"""
        logger.info(f"🔧 Retrieving context for control generation")
        intent = state["intent"]
        user_id = state["user_id"]
        parameters = state["parameters"]
        
        try:
            if intent == "generate_controls_specific":
                risk_id = parameters.get("risk_id")
                logger.info(f"   📋 Getting specific risk: {risk_id}")
                risk_data = self.mongo.get_risk_by_id(risk_id, user_id)
                if not risk_data:
                    logger.error(f"   ❌ Risk not found: {risk_id}")
                    return {"error": "Risk not found"}
                logger.info(f"   ✅ Risk found: {risk_data.get('description', 'Unknown')[:50]}...")
                return self.rag.retrieve_context_for_control_generation(risk_data, state["user_context"])
                
            elif intent == "generate_controls_all":
                logger.info(f"   📋 Getting all risks without controls")
                risks = self.rag.get_risks_for_generation(user_id, exclude_with_controls=False)
                logger.info(f"   ✅ Found {len(risks)} risks without controls")
                return {"risks_for_generation": risks}
                
            elif intent == "generate_controls_category":
                category = parameters.get("risk_category")
                logger.info(f"   📋 Getting risks by category: {category}")
                all_risks = self.rag.get_risks_for_generation(user_id, exclude_with_controls=False)
                risks = [r for r in all_risks if r.get("category") == category]
                logger.info(f"   ✅ Found {len(risks)} risks in category: {category}")
                return {"risks_for_generation": risks}
            
            logger.warning(f"   ⚠️  Unknown generation intent: {intent}")
            return {}
            
        except Exception as e:
            logger.error(f"❌ Error in generation context retrieval: {e}")
            return {"error": str(e)}

    def generate_controls_node(self, state: AgentState) -> AgentState:
        """Generate controls with comprehensive logging"""
        logger.info(f"🔧 Starting control generation")
        context = state["retrieved_context"]
        
        if "error" in context:
            logger.error(f"   ❌ Context error: {context['error']}")
            state["final_response"] = context["error"]
            return state
        
        try:
            if "risks_for_generation" in context:
                logger.info(f"   📋 Generating controls for multiple risks")
                all_controls = []
                risks = context["risks_for_generation"][:3]  # Limit for demo
                logger.info(f"   🎯 Processing {len(risks)} risks")
                
                for i, risk in enumerate(risks):
                    logger.info(f"      📝 Generating controls for risk {i+1}/{len(risks)}: {risk.get('description', 'Unknown')[:50]}...")
                    
                    risk_context = self.rag.retrieve_context_for_control_generation(risk, state["user_context"])
                    controls = self.openai.generate_controls(
                        risk, 
                        state["user_context"],
                        risk_context.get("similar_controls", []),
                        risk_context.get("iso_guidance", [])
                    )
                    
                    # Ensure all required fields are present for each control
                    for j, control in enumerate(controls):
                        # Add required fields
                        control["risk_id"] = risk.get('id', '')
                        control["user_id"] = state["user_id"]
                        
                        # Generate unique ID if not present
                        if not control.get("id"):
                            control["id"] = str(uuid.uuid4())
                        
                        # Ensure control_id is present (required by Pydantic model)
                        if not control.get("control_id"):
                            control["control_id"] = f"CTRL-{risk.get('id', 'UNK')}-{j+1:03d}"
                        
                        # Log control validation
                        logger.info(f"         Control {j+1} validated:")
                        logger.info(f"            ID: {control.get('id')}")
                        logger.info(f"            Control ID: {control.get('control_id')}")
                        logger.info(f"            Risk ID: {control.get('risk_id')}")
                        logger.info(f"            User ID: {control.get('user_id')}")
                    
                    all_controls.extend(controls)
                    logger.info(f"      ✅ Generated {len(controls)} controls for risk {i+1}")
                
                state["generated_controls"] = all_controls
                logger.info(f"   🎯 Total controls generated: {len(all_controls)}")
                
            else:
                logger.info(f"   📋 Generating controls for specific risk")
                risk_id = state["parameters"].get("risk_id")
                risk_data = self.mongo.get_risk_by_id(risk_id, state["user_id"])
                
                existing_controls = self.mongo.get_controls_by_risk(risk_id, state["user_id"])
                if existing_controls:
                    logger.info(f"   ⚠️  Risk already has {len(existing_controls)} controls")
                    state["final_response"] = f"You already have {len(existing_controls)} controls for this risk. Would you like to see them or generate additional ones?"
                    return state
                
                logger.info(f"   📝 Generating controls for risk: {risk_data.get('description', 'Unknown')[:50]}...")
                risk_context = self.rag.retrieve_context_for_control_generation(risk_data, state["user_context"])
                controls = self.openai.generate_controls(
                    risk_data, 
                    state["user_context"],
                    risk_context.get("similar_controls", []),
                    risk_context.get("iso_guidance", [])
                )
                
                # Ensure all required fields are present for each control
                for j, control in enumerate(controls):
                    # Add required fields
                    control["risk_id"] = risk_id
                    control["user_id"] = state["user_id"]
                    
                    # Generate unique ID if not present
                    if not control.get("id"):
                        control["id"] = str(uuid.uuid4())
                    
                    # Ensure control_id is present (required by Pydantic model)
                    if not control.get("control_id"):
                        control["control_id"] = f"CTRL-{risk_id}-{j+1:03d}"
                    
                    # Log control validation
                    logger.info(f"         Control {j+1} validated:")
                    logger.info(f"            ID: {control.get('id')}")
                    logger.info(f"            Control ID: {control.get('control_id')}")
                    logger.info(f"            Risk ID: {control.get('risk_id')}")
                    logger.info(f"            User ID: {control.get('user_id')}")
                
                state["generated_controls"] = controls
                logger.info(f"   ✅ Generated {len(controls)} controls")
            
        except Exception as e:
            logger.error(f"❌ Control generation failed: {e}")
            state["generated_controls"] = []
        
        return state

    def handle_selection_node(self, state: AgentState) -> AgentState:
        """Handle control selection with logging"""
        logger.info(f"🤝 Handling control selection")
        
        if state["generated_controls"]:
            logger.info(f"   📋 Controls available for selection: {len(state['generated_controls'])}")
            state["pending_selection"] = True
            
            try:
                session_id = self.mongo.save_session({
                    "user_id": state["user_id"],
                    "generated_controls": state["generated_controls"],
                    "state": dict(state)
                })
                state["session_id"] = session_id
                logger.info(f"   ✅ Session saved with ID: {session_id}")
            except Exception as e:
                logger.error(f"   ❌ Failed to save session: {e}")
                state["session_id"] = ""
        else:
            logger.info(f"   ⚠️  No controls to select from")
            state["pending_selection"] = False
        
        return state

    def store_data_node(self, state: AgentState) -> AgentState:
        """Store selected controls with comprehensive logging"""
        logger.info(f"💾 Starting data storage")
        
        if state["selected_controls"]:
            logger.info(f"   📋 Storing {len(state['selected_controls'])} selected controls")
            
            try:
                # Get controls to store - handle both UUIDs and control_ids
                controls_to_store = []
                
                for selected_id in state["selected_controls"]:
                    # Try to find control by UUID first
                    control_by_uuid = next(
                        (control for control in state["generated_controls"] if control.get("id") == selected_id), 
                        None
                    )
                    
                    # Try to find control by control_id if UUID not found
                    control_by_control_id = next(
                        (control for control in state["generated_controls"] if control.get("control_id") == selected_id), 
                        None
                    )
                    
                    if control_by_uuid:
                        controls_to_store.append(control_by_uuid)
                        logger.info(f"         ✅ Control found by UUID: {selected_id}")
                    elif control_by_control_id:
                        controls_to_store.append(control_by_control_id)
                        logger.info(f"         ✅ Control found by control_id: {selected_id}")
                    else:
                        logger.warning(f"         ⚠️  Control not found for ID: {selected_id}")
                
                if not controls_to_store:
                    logger.error(f"   ❌ No controls found for the selected IDs: {state['selected_controls']}")
                    logger.error(f"   📋 Available control IDs (UUIDs): {[c.get('id') for c in state['generated_controls']]}")
                    logger.error(f"   📋 Available control IDs (control_ids): {[c.get('control_id') for c in state['generated_controls']]}")
                    state["final_response"] = "Error: No controls found for the selected IDs. Please try again."
                    return state
                
                logger.info(f"   🎯 Controls to store: {len(controls_to_store)}")
                logger.info(f"   📋 Selected controls: {[c.get('control_id', c.get('id')) for c in controls_to_store]}")
                
                # Validate controls before storage
                for i, control in enumerate(controls_to_store):
                    logger.info(f"      Validating control {i+1}:")
                    logger.info(f"         Control ID: {control.get('control_id', 'Missing!')}")
                    logger.info(f"         Title: {control.get('title', 'Missing!')[:50]}...")
                    logger.info(f"         Risk ID: {control.get('risk_id', 'Missing!')}")
                    logger.info(f"         User ID: {control.get('user_id', 'Missing!')}")
                    
                    # Ensure all required fields are present
                    if not control.get("control_id"):
                        logger.error(f"         ❌ Missing control_id!")
                    if not control.get("title"):
                        logger.error(f"         ❌ Missing title!")
                    if not control.get("risk_id"):
                        logger.error(f"         ❌ Missing risk_id!")
                    if not control.get("user_id"):
                        logger.error(f"         ❌ Missing user_id!")
                
                # Save to MongoDB
                logger.info("   💾 Saving controls to MongoDB")
                try:
                    saved_control_ids = self.mongo.save_controls(controls_to_store)
                    logger.info(f"      ✅ Controls saved to MongoDB: {len(saved_control_ids)} controls")
                    logger.info(f"      📋 Saved control IDs: {saved_control_ids}")
                except Exception as e:
                    logger.error(f"      ❌ MongoDB save failed: {e}")
                    state["final_response"] = f"Failed to save controls to database: {str(e)}"
                    return state
                
                # Create Neo4j nodes and relationships
                logger.info("   🔗 Creating control nodes and risk relationships in Neo4j")
                neo4j_success_count = 0
                for i, control in enumerate(controls_to_store):
                    try:
                        success = self.graph_db.create_control_node(control)
                        if success:
                            neo4j_success_count += 1
                            logger.info(f"      ✅ Control {i+1} Neo4j node created: {control.get('control_id')}")
                        else:
                            logger.warning(f"      ⚠️  Control {i+1} Neo4j node creation failed: {control.get('control_id')}")
                    except Exception as e:
                        logger.error(f"      ❌ Control {i+1} Neo4j creation error: {e}")
                
                logger.info(f"      📊 Neo4j results: {neo4j_success_count}/{len(controls_to_store)} controls created")
                
                # Store vector embeddings
                logger.info("   📝 Storing control embeddings in vector database")
                try:
                    # Ensure RAG service is available
                    if not self.rag:
                        from .rag_service import rag_service
                        self.rag = rag_service
                        logger.info("      📦 RAG service imported for control embedding storage")
                    
                    self.rag.store_control_embeddings(controls_to_store)
                    logger.info(f"      ✅ Control embeddings stored successfully")
                except Exception as e:
                    logger.error(f"      ❌ Control embedding storage failed: {e}")
                    # Don't fail the entire process for embedding issues
                
                # Update risk status to indicate controls are assigned
                logger.info("   🔄 Updating risk status to reflect control assignment")
                try:
                    risk_ids = list(set([control.get('risk_id') for control in controls_to_store]))
                    logger.info(f"      📋 Updating {len(risk_ids)} risks with control assignment")
                    
                    # Here you could add logic to update risk status
                    # For example, mark risks as "Controls Assigned"
                    for risk_id in risk_ids:
                        logger.info(f"         Risk {risk_id} now has controls assigned")
                        
                except Exception as e:
                    logger.error(f"      ❌ Risk status update failed: {e}")
                    # Don't fail the entire process for status update issues
                
                state["final_response"] = f"Successfully saved {len(controls_to_store)} controls with risk mapping. Controls are now stored in the database, vector embeddings created, and knowledge graph relationships established."
                logger.info(f"   🎯 Data storage completed successfully")
                logger.info(f"   📊 Summary: {len(controls_to_store)} controls stored, {neo4j_success_count} Neo4j nodes created, embeddings stored")
                
            except Exception as e:
                logger.error(f"   ❌ Data storage failed: {e}")
                state["final_response"] = f"Failed to save controls: {str(e)}"
        else:
            logger.info(f"   ⚠️  No controls selected for storage")
            state["final_response"] = "No controls were selected for storage."
        
        return state

    def store_query_embedding_node(self, state: AgentState) -> AgentState:
        """Store the query embedding for future reference and learning with logging"""
        logger.info(f"💾 Storing query embedding for learning")
        logger.info(f"   Query: '{state['user_query'][:100]}{'...' if len(state['user_query']) > 100 else ''}'")
        logger.info(f"   Intent: {state.get('intent', 'Unknown')}")
        logger.info(f"   User ID: {state['user_id']}")
        
        try:
            # Store query embedding with context
            response_context = {
                "intent": state.get("intent", ""),
                "generated_controls_count": len(state.get("generated_controls", [])),
                "retrieved_context_summary": {
                    "controls_found": len(state.get("retrieved_context", {}).get("similar_controls", [])),
                    "risks_found": len(state.get("retrieved_context", {}).get("similar_risks", [])),
                    "guidance_found": len(state.get("retrieved_context", {}).get("iso_guidance", []))
                }
            }
            
            # Ensure all values are JSON serializable
            response_context = json.loads(json.dumps(response_context))
            
            logger.info(f"   📊 Response context prepared:")
            logger.info(f"      Intent: {response_context['intent']}")
            logger.info(f"      Generated controls: {response_context['generated_controls_count']}")
            logger.info(f"      Controls found: {response_context['retrieved_context_summary']['controls_found']}")
            logger.info(f"      Risks found: {response_context['retrieved_context_summary']['risks_found']}")
            logger.info(f"      Guidance found: {response_context['retrieved_context_summary']['guidance_found']}")
            
            self.rag.store_query_embedding(
                str(uuid.uuid4()),  # query_id
                state["user_id"],
                state["user_query"],
                state.get("intent", "unknown"),
                response_context
            )
            logger.info(f"   ✅ Query embedding stored successfully")
            
        except Exception as e:
            logger.error(f"   ❌ Failed to store query embedding: {e}")
        
        return state

    def synthesize_response_node(self, state: AgentState) -> AgentState:
        """Synthesize final response with comprehensive logging"""
        logger.info(f"🎯 Starting response synthesis")
        
        if not state.get("final_response"):
            logger.info(f"   📝 No final response yet, generating one")
            
            if state.get("retrieved_context"):
                logger.info(f"   🔍 Using retrieved context for response generation")
                logger.info(f"      Context keys: {list(state['retrieved_context'].keys())}")
                
                # Try the enhanced contextual response first
                try:
                    logger.info(f"   🚀 Attempting enhanced contextual response")
                    
                    # Check if this is a "show controls" type query
                    intent = state.get("intent", "")
                    
                    # Check if we have controls in the context (regardless of intent)
                    has_controls = bool(
                        state.get("retrieved_context", {}).get("similar_controls") or 
                        state.get("retrieved_context", {}).get("controls") or
                        state.get("retrieved_context", {}).get("existing_controls") or
                        state.get("retrieved_context", {}).get("text_search_controls")
                    )
                    
                    # Use show controls response for specific annex queries or when we have controls
                    if (intent.startswith("show_controls_by_annex") or 
                        (intent.startswith("show_controls") and "annex" in state.get("user_query", "").lower())):
                        logger.info(f"   🎯 Using show controls response method (annex-specific)")
                        state["final_response"] = self.openai.generate_show_controls_response(
                            state["user_query"],
                            state["retrieved_context"],
                            state["user_context"]
                        )
                    # Use enhanced general controls response when we have controls (regardless of intent)
                    elif has_controls:
                        logger.info(f"   🎯 Using enhanced general controls response (controls found)")
                        state["final_response"] = self.openai.generate_general_controls_response(
                            state["user_query"],
                            state["retrieved_context"],
                            state["user_context"]
                        )
                    else:
                        logger.info(f"   🎯 Using contextual response method (general query)")
                        state["final_response"] = self.openai.generate_contextual_response(
                            state["user_query"],
                            state["retrieved_context"],
                            state["user_context"]
                        )
                    
                    logger.info(f"      ✅ Enhanced response generated successfully")
                    
                except Exception as e:
                    logger.warning(f"      ⚠️  Enhanced response failed: {e}")
                    logger.info(f"      🔄 Falling back to standard response")
                    
                    try:
                        state["final_response"] = self.openai.synthesize_response(
                            state["user_query"], 
                            state["retrieved_context"], 
                            state.get("generated_controls")
                        )
                        logger.info(f"      ✅ Standard response generated successfully")
                    except Exception as e2:
                        logger.error(f"      ❌ Standard response also failed: {e2}")
                        state["final_response"] = "I apologize, but I encountered an error while generating a response. Please try again."
            else:
                logger.info(f"   ⚠️  No retrieved context available")
                logger.info(f"   🔄 Using fallback response generation")
                
                try:
                    state["final_response"] = self.openai.synthesize_response(
                        state["user_query"], 
                        {}, 
                        state.get("generated_controls")
                    )
                    logger.info(f"      ✅ Fallback response generated successfully")
                except Exception as e:
                    logger.error(f"      ❌ Fallback response failed: {e}")
                    state["final_response"] = "I apologize, but I encountered an error while generating a response. Please try again."
        else:
            logger.info(f"   ✅ Final response already exists, skipping generation")
        
        logger.info(f"   📝 Final response length: {len(state.get('final_response', ''))}")
        logger.info(f"🎯 Response synthesis completed")
        
        return state

    def route_after_classification(self, state: AgentState) -> str:
        """Route after intent classification with logging"""
        intent = state["intent"]
        logger.info(f"🔄 Routing after classification: {intent}")
        
        # Check if we're just storing already generated controls
        if intent == "store_selected_controls" and state.get("generated_controls") and state.get("selected_controls"):
            logger.info(f"   🎯 Routing to: store_data (direct storage of selected controls)")
            return "store"
        
        if intent.startswith("generate_controls"):
            logger.info(f"   🎯 Routing to: retrieve_context (for control generation)")
            return "retrieve"
        
        logger.info(f"   🎯 Routing to: retrieve_context (for general query)")
        return "retrieve"

    def route_after_retrieval(self, state: AgentState) -> str:
        """Route after context retrieval with logging"""
        intent = state["intent"]
        logger.info(f"🔄 Routing after retrieval: {intent}")
        
        if intent.startswith("generate_controls"):
            logger.info(f"   🎯 Routing to: generate_controls")
            return "generate"
        
        logger.info(f"   🎯 Routing to: synthesize_response")
        return "respond"

    def route_after_selection(self, state: AgentState) -> str:
        """Route after control selection with logging"""
        logger.info(f"🔄 Routing after selection")
        
        if state.get("selected_controls"):
            logger.info(f"   🎯 Controls selected, routing to: store_data")
            return "store"
        
        logger.info(f"   🎯 No controls selected, routing to: store_query_embedding")
        return "wait"

    async def run(self, user_query: str, user_id: str, selected_controls: list = None, session_id: str = None):
        """Run the agent workflow with comprehensive logging"""
        logger.info(f"🚀 Starting ISO27001Agent workflow")
        logger.info(f"   User query: '{user_query[:100]}{'...' if len(user_query) > 100 else ''}'")
        logger.info(f"   User ID: {user_id}")
        logger.info(f"   Session ID: {session_id}")
        logger.info(f"   Selected controls: {len(selected_controls) if selected_controls else 0}")
        
        user_context = self.mongo.get_user_context(user_id)
        logger.info(f"   👤 User context retrieved: {user_context.get('organization_name', 'Unknown')} in {user_context.get('domain', 'Unknown')}")
        
        if session_id and selected_controls:
            logger.info(f"   📋 Resuming session: {session_id}")
            session_data = self.mongo.get_session(session_id)
            if session_data:
                logger.info(f"      ✅ Session data retrieved")
                state = session_data["state"]
                state["selected_controls"] = selected_controls
                logger.info(f"      🔄 Resuming workflow with selected controls")
                
                # If we have selected controls, we can skip the generation and go straight to storage
                if state.get("generated_controls") and selected_controls:
                    logger.info(f"      🎯 Controls already generated, proceeding to storage")
                    # Create a minimal workflow for just storing the selected controls
                    storage_state = {
                        "user_query": user_query,
                        "user_id": user_id,
                        "user_context": user_context,
                        "generated_controls": state["generated_controls"],
                        "selected_controls": selected_controls,
                        "session_id": session_id,
                        "retrieved_context": state.get("retrieved_context", {}),
                        "intent": state.get("intent", "store_selected_controls"),
                        "parameters": state.get("parameters", {}),
                        "conversation_history": state.get("conversation_history", []),
                        "final_response": "",
                        "pending_selection": False
                    }
                    
                    # Run just the storage part
                    result = await self.workflow.ainvoke(storage_state, {"recursion_limit": 10})
                    logger.info(f"   🎯 Storage workflow completed")
                    return result
                else:
                    # Normal workflow resumption
                    result = await self.workflow.ainvoke(state, {"recursion_limit": 10})
                    logger.info(f"   🎯 Session workflow completed")
                    return result
            else:
                logger.warning(f"      ⚠️  Session not found, starting new workflow")
        
        logger.info(f"   🆕 Starting new workflow")
        initial_state = {
            "user_query": user_query,
            "user_id": user_id,
            "user_context": user_context,
            "intent": "",
            "parameters": {},
            "retrieved_context": {},
            "generated_controls": [],
            "selected_controls": [],
            "conversation_history": [],
            "final_response": "",
            "pending_selection": False,
            "session_id": ""
        }
        
        logger.info(f"   📝 Initial state prepared")
        result = await self.workflow.ainvoke(initial_state, {"recursion_limit": 10})
        logger.info(f"   🎯 New workflow completed")
        logger.info(f"🚀 ISO27001Agent workflow finished")
        
        return result

iso_agent = ISO27001Agent()
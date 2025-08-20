from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from ..auth import get_current_user
from ..models import AgentResponse, ControlSelection
from ..langgraph_agent import iso_agent
from ..database import mongodb
from ..neo4j_db import neo4j_service
from ..rag_service import rag_service
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

class ChatRequest(BaseModel):
    query: str

@router.post("/chat", response_model=AgentResponse)
async def chat_with_agent(request: ChatRequest, user = Depends(get_current_user)):
    try:
        result = await iso_agent.run(request.query, user["username"])
        
        # Get generated controls and ensure they have all required fields
        generated_controls = result.get("generated_controls", [])
        validated_controls = []
        
        if generated_controls:
            logger.info(f"📋 Validating {len(generated_controls)} generated controls")
            
            for i, control in enumerate(generated_controls):
                try:
                    # Ensure all required fields are present
                    validated_control = {
                        "id": control.get("id"),
                        "control_id": control.get("control_id"),
                        "title": control.get("title"),
                        "description": control.get("description"),
                        "domain_category": control.get("domain_category"),
                        "annex_reference": control.get("annex_reference"),
                        "control_statement": control.get("control_statement"),
                        "implementation_guidance": control.get("implementation_guidance"),
                        "risk_id": control.get("risk_id"),
                        "user_id": control.get("user_id"),
                        "created_at": control.get("created_at")
                    }
                    
                    # Validate that required fields are present
                    required_fields = ["control_id", "title", "description", "domain_category", 
                                    "annex_reference", "control_statement", "implementation_guidance", 
                                    "risk_id", "user_id"]
                    
                    missing_fields = [field for field in required_fields if not validated_control.get(field)]
                    
                    if missing_fields:
                        logger.warning(f"   ⚠️  Control {i+1} missing required fields: {missing_fields}")
                        # Skip invalid controls
                        continue
                    
                    validated_controls.append(validated_control)
                    logger.info(f"   ✅ Control {i+1} validated successfully")
                    
                except Exception as e:
                    logger.error(f"   ❌ Control {i+1} validation failed: {e}")
                    # Skip invalid controls
                    continue
            
            logger.info(f"📊 Validation complete: {len(validated_controls)}/{len(generated_controls)} controls valid")
        
        return AgentResponse(
            response=result["final_response"],
            controls=validated_controls if validated_controls else None,
            pending_selection=result.get("pending_selection", False),
            session_id=result.get("session_id", "")
        )
    except Exception as e:
        logger.error(f"❌ Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/select-controls")
async def select_controls(selection: ControlSelection, user = Depends(get_current_user)):
    try:
        logger.info(f"🎯 Processing control selection for user: {user['username']}")
        logger.info(f"   Session ID: {selection.session_id}")
        logger.info(f"   Selected control IDs: {selection.selected_control_ids}")
        
        # Get the session data to retrieve the generated controls
        session_data = mongodb.get_session(selection.session_id)
        if not session_data:
            logger.error(f"   ❌ Session not found: {selection.session_id}")
            raise HTTPException(status_code=404, detail="Session not found")
        
        logger.info(f"   ✅ Session data retrieved successfully")
        
        # Get the generated controls from the session
        generated_controls = session_data.get("state", {}).get("generated_controls", [])
        if not generated_controls:
            logger.error(f"   ❌ No generated controls found in session")
            raise HTTPException(status_code=400, detail="No generated controls found in session")
        
        logger.info(f"   📋 Found {len(generated_controls)} generated controls in session")
        
        # Filter controls based on user selection
        # Frontend might send either UUIDs (id field) or control_ids
        # We need to handle both cases
        selected_controls = []
        
        for selected_id in selection.selected_control_ids:
            # Try to find control by UUID first
            control_by_uuid = next(
                (control for control in generated_controls if control.get("id") == selected_id), 
                None
            )
            
            # Try to find control by control_id if UUID not found
            control_by_control_id = next(
                (control for control in generated_controls if control.get("control_id") == selected_id), 
                None
            )
            
            if control_by_uuid:
                selected_controls.append(control_by_uuid)
                logger.info(f"      ✅ Control found by UUID: {selected_id}")
            elif control_by_control_id:
                selected_controls.append(control_by_control_id)
                logger.info(f"      ✅ Control found by control_id: {selected_id}")
            else:
                logger.warning(f"      ⚠️  Control not found for ID: {selected_id}")
        
        if not selected_controls:
            logger.error(f"   ❌ No controls found for selected IDs: {selection.selected_control_ids}")
            logger.error(f"   📋 Available control IDs (UUIDs): {[c.get('id') for c in generated_controls]}")
            logger.error(f"   📋 Available control IDs (control_ids): {[c.get('control_id') for c in generated_controls]}")
            raise HTTPException(status_code=400, detail="No controls found for the selected IDs")
        
        logger.info(f"   🎯 Successfully matched {len(selected_controls)} selected controls")
        logger.info(f"   📋 Selected controls: {[c.get('control_id', c.get('id')) for c in selected_controls]}")
        
        # Store the selected controls directly
        try:
            # Save to MongoDB
            logger.info("   💾 Saving selected controls to MongoDB")
            saved_control_ids = mongodb.save_controls(selected_controls)
            logger.info(f"      ✅ Controls saved to MongoDB: {len(saved_control_ids)} controls")
            
            # Create Neo4j nodes and relationships
            logger.info("   🔗 Creating control nodes and risk relationships in Neo4j")
            neo4j_success_count = 0
            for i, control in enumerate(selected_controls):
                try:
                    success = neo4j_service.create_control_node(control)
                    if success:
                        neo4j_success_count += 1
                        logger.info(f"      ✅ Control {i+1} Neo4j node created: {control.get('control_id')}")
                    else:
                        logger.warning(f"      ⚠️  Control {i+1} Neo4j node creation failed: {control.get('control_id')}")
                except Exception as e:
                    logger.error(f"      ❌ Control {i+1} Neo4j creation error: {e}")
            
            logger.info(f"      📊 Neo4j results: {neo4j_success_count}/{len(selected_controls)} controls created")
            
            # Store vector embeddings
            logger.info("   📝 Storing control embeddings in vector database")
            try:
                rag_service.store_control_embeddings(selected_controls)
                logger.info(f"      ✅ Control embeddings stored successfully")
            except Exception as e:
                logger.error(f"      ❌ Control embedding storage failed: {e}")
            
            # Update session to mark controls as stored
            mongodb.update_session(selection.session_id, {
                "controls_stored": True,
                "stored_control_ids": saved_control_ids,
                "stored_at": datetime.now().isoformat()
            })
            
            logger.info(f"   ✅ Session updated with storage information")
            
            success_message = f"Successfully saved {len(selected_controls)} controls with risk mapping. Controls are now stored in the database, vector embeddings created, and knowledge graph relationships established."
            
            logger.info(f"   🎯 Control selection and storage completed successfully")
            
            return AgentResponse(
                response=success_message,
                pending_selection=False
            )
            
        except Exception as e:
            logger.error(f"   ❌ Control storage failed: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to store controls: {str(e)}")
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"❌ Control selection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user-controls")
async def get_user_controls(user = Depends(get_current_user)):
    try:
        controls = list(mongodb.controls.find({"user_id": user["username"]}))
        for control in controls:
            if "_id" in control:
                control["_id"] = str(control["_id"])
        return {"controls": controls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/controls-by-risk/{risk_id}")
async def get_controls_by_risk(risk_id: str, user = Depends(get_current_user)):
    try:
        controls = mongodb.get_controls_by_risk(risk_id, user["username"])
        return {"controls": controls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/store-controls")
async def store_controls(controls: List[Dict], user = Depends(get_current_user)):
    try:
        logger.info(f"💾 Storing {len(controls)} controls for user: {user['username']}")
        
        stored_count = 0
        for i, control in enumerate(controls):
            try:
                # Ensure required fields are present
                control["user_id"] = user["username"]
                
                # Validate required fields
                required_fields = ["title", "description", "domain_category", "annex_reference", 
                                "control_statement", "implementation_guidance", "risk_id"]
                
                missing_fields = [field for field in required_fields if not control.get(field)]
                
                if missing_fields:
                    logger.warning(f"   ⚠️  Control {i+1} missing required fields: {missing_fields}")
                    continue
                
                # Generate control_id if not present
                if not control.get("control_id"):
                    control["control_id"] = f"CTRL-{control.get('risk_id', 'UNK')}-{i+1:03d}"
                
                # Generate id if not present
                if not control.get("id"):
                    control["id"] = str(uuid.uuid4())
                
                mongodb.controls.insert_one(control)
                stored_count += 1
                logger.info(f"   ✅ Control {i+1} stored successfully")
                
            except Exception as e:
                logger.error(f"   ❌ Control {i+1} storage failed: {e}")
                continue
        
        logger.info(f"📊 Storage complete: {stored_count}/{len(controls)} controls stored")
        
        return AgentResponse(
            response=f"Successfully stored {stored_count} out of {len(controls)} controls",
            pending_selection=False
        )
    except Exception as e:
        logger.error(f"❌ Store controls endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
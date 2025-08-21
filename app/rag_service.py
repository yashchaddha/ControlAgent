from typing import Dict, List
from .openai_service import openai_service
from .postgres import postgres_service
from .neo4j_db import neo4j_service
from .database import mongodb
from .annex_service import annex_service

class RAGService:
    def __init__(self):
        self.openai = openai_service
        self.vector_db = postgres_service
        self.graph_db = neo4j_service
        self.mongo_db = mongodb
        self.annex = annex_service

    def retrieve_context_for_control_generation(self, risk_data: Dict, user_context: Dict) -> Dict:
        risk_description = risk_data.get('description', '')
        risk_category = risk_data.get('category', '')
        user_domain = user_context.get('domain', '')
        
        # Try to get embeddings, but fallback gracefully if DB issues
        try:
            query_embedding = self.openai.get_embedding(risk_description)
            similar_risks = self.vector_db.search_similar_risks(query_embedding, limit=3)
        except Exception as e:
            print(f"Vector search failed, proceeding without: {e}")
            similar_risks = []
        
        # Get ISO guidance from annex service instead of vector database
        iso_guidance = self.annex.get_annex_controls(risk_category, limit=5)
        print(f"📋 Retrieved {len(iso_guidance)} annex controls for category: {risk_category}")
        
        # Try graph operations
        try:
            similar_controls = self.graph_db.get_similar_controls_by_domain(user_domain, risk_category)
        except Exception as e:
            print(f"Graph search failed, proceeding without: {e}")
            similar_controls = []
        
        # Log what we found
        print(f"Context retrieval results:")
        print(f"  - Similar risks: {len(similar_risks)}")
        print(f"  - Similar controls: {len(similar_controls)}")
        print(f"  - ISO guidance: {len(iso_guidance)}")
        
        return {
            "similar_risks": similar_risks,
            "similar_controls": similar_controls,
            "iso_guidance": iso_guidance,
            "risk_patterns": self._get_risk_patterns(risk_category, user_domain)
        }

    def get_risks_for_generation(self, user_id: str, exclude_with_controls: bool = True) -> List[Dict]:
        """Get risks for control generation from MongoDB"""
        try:
            if exclude_with_controls:
                return self.mongo_db.get_user_risks(user_id, exclude_with_controls=True)
            else:
                return self.mongo_db.get_user_risks(user_id, exclude_with_controls=False)
        except Exception as e:
            print(f"Failed to get risks for generation: {e}")
            return []

    def retrieve_context_for_query(self, query: str, intent: str, parameters: Dict, user_id: str, vector_only: bool = True) -> Dict:
        query_embedding = self.openai.get_embedding(query)
        
        if intent == "show_finalized_controls":
            return self._get_finalized_controls_context(parameters, user_id)
        elif intent == "show_controls_by_category":
            return self._get_controls_by_category(parameters.get('risk_category'), user_id)
        elif intent == "show_controls_by_annex":
            return self._get_controls_by_annex(parameters.get('annex'), user_id)
        elif intent == "query_controls":
            return self._get_general_query_context(query_embedding, user_id, query, vector_only)
        else:
            return {}

    def _get_finalized_controls_context(self, parameters: Dict, user_id: str) -> Dict:
        if parameters.get('risk_id'):
            controls = self.mongo_db.get_controls_by_risk(parameters['risk_id'], user_id)
            risk = self.mongo_db.get_risk_by_id(parameters['risk_id'], user_id)
            return {"controls": controls, "risk": risk}
        else:
            user_stats = self.graph_db.get_user_risk_control_stats(user_id)
            return {"stats": user_stats}

    def _get_controls_by_category(self, category: str, user_id: str) -> Dict:
        """Get controls by category with comprehensive search including vector search"""
        print(f"🔍 Searching for controls by category: {category}")
        
        # 1. Get controls from MongoDB by risk category
        mongo_controls = self.mongo_db.get_controls_by_category(category, user_id)
        print(f"   📋 MongoDB controls found: {len(mongo_controls)}")
        
        # 2. Also search for controls by text using the category as a search term
        text_search_controls = []
        try:
            text_search_controls = self._search_existing_controls_by_text(user_id, category, limit=10)
            print(f"   🔤 Text search controls found: {len(text_search_controls)}")
        except Exception as e:
            print(f"   ❌ Text search failed: {e}")
        
        # 3. Search vector database for similar controls using the category as a query
        vector_controls = []
        try:
            # Generate embedding for the category to search vector database
            category_embedding = self.openai.get_embedding(category)
            vector_controls = self.vector_db.search_similar_controls(category_embedding, limit=10)
            print(f"   🧮 Vector search controls found: {len(vector_controls)}")
        except Exception as e:
            print(f"   ❌ Vector search failed: {e}")
        
        # 4. Get ISO guidance from annex service for this category
        iso_guidance = self.annex.get_annex_controls(category, limit=5)
        print(f"   📋 ISO guidance controls found: {len(iso_guidance)}")
        
        # 5. Combine all results - prioritize existing controls, then text search, then vector search, then ISO guidance
        all_controls = []
        
        # Add MongoDB controls first (these are user's actual controls)
        for control in mongo_controls:
            control['source'] = 'existing_user_controls'
            all_controls.append(control)
        
        # Add text search controls (avoid duplicates)
        existing_ids = {c.get('control_id', '') for c in all_controls}
        for control in text_search_controls:
            if control.get('control_id') not in existing_ids:
                control['source'] = 'text_search'
                all_controls.append(control)
        
        # Add vector search controls (avoid duplicates)
        existing_ids = {c.get('control_id', '') for c in all_controls}
        for control in vector_controls:
            if control.get('control_id') not in existing_ids:
                control['source'] = 'vector_search'
                all_controls.append(control)
        
        # Add ISO guidance controls (avoid duplicates)
        existing_references = {c.get('reference', '') for c in all_controls}
        for control in iso_guidance:
            if control.get('reference') not in existing_references:
                control['source'] = 'iso_guidance'
                all_controls.append(control)
        
        print(f"   ✅ Total combined controls: {len(all_controls)}")
        
        return {
            "controls": all_controls,
            "similar_controls": all_controls,  # Use all controls for response generation
            "category": category,
            "existing_controls": mongo_controls,
            "text_search_controls": text_search_controls,
            "vector_controls": vector_controls,
            "iso_guidance": iso_guidance,
            "total_controls_found": len(all_controls)
        }

    def _get_controls_by_annex(self, annex: str, user_id: str) -> Dict:
        """Get controls by annex reference with comprehensive search"""
        print(f"🔍 Searching for controls by annex: {annex}")
        
        # 1. Get controls from MongoDB by annex reference
        mongo_controls = self.mongo_db.get_controls_by_annex(annex, user_id)
        print(f"   📋 MongoDB controls found: {len(mongo_controls)}")
        
        # 2. Search vector database for controls with this annex reference
        try:
            # Create a dummy embedding for annex search (we'll filter by annex reference)
            dummy_embedding = [0.1] * 1536
            vector_controls = self.vector_db.search_similar_controls(dummy_embedding, annex_filter=annex, limit=10)
            print(f"   🔍 Vector search controls found: {len(vector_controls)}")
        except Exception as e:
            print(f"   ❌ Vector search failed: {e}")
            vector_controls = []
        
        # 3. Get annex guidance for this specific annex reference
        annex_guidance = self.annex.get_annex_by_reference(annex)
        print(f"   📋 Annex guidance found: {annex_guidance.get('reference', 'None')}")
        
        # 4. Get all controls from annex service for this annex family (e.g., A.5.x for A.5.3)
        annex_family = annex.split('.')[0] + '.' + annex.split('.')[1] if '.' in annex else annex
        annex_family_controls = self.annex.get_controls_by_domain("Organizational Controls")  # Default to organizational for A.5.x
        if annex_family == "A.5":
            annex_family_controls = self.annex.get_controls_by_domain("Organizational Controls")
        elif annex_family == "A.6":
            annex_family_controls = self.annex.get_controls_by_domain("People Controls")
        elif annex_family == "A.7":
            annex_family_controls = self.annex.get_controls_by_domain("Physical Controls")
        elif annex_family == "A.8":
            annex_family_controls = self.annex.get_controls_by_domain("Technological Controls")
        
        print(f"   📋 Annex family controls found: {len(annex_family_controls)}")
        
        # 5. Combine and deduplicate results
        all_controls = []
        
        # Add MongoDB controls
        for control in mongo_controls:
            control['source'] = 'mongodb'
            all_controls.append(control)
        
        # Add vector search controls (avoid duplicates)
        existing_ids = {c.get('control_id', '') for c in all_controls}
        for control in vector_controls:
            if control.get('control_id') not in existing_ids:
                control['source'] = 'vector_search'
                all_controls.append(control)
        
        # Add annex guidance
        if annex_guidance:
            annex_guidance['source'] = 'annex_guidance'
            all_controls.append(annex_guidance)
        
        # Add annex family controls
        for control in annex_family_controls:
            if control.get('reference') not in {c.get('reference', '') for c in all_controls}:
                control['source'] = 'annex_family'
                all_controls.append(control)
        
        print(f"   ✅ Total combined controls: {len(all_controls)}")
        
        return {
            "controls": all_controls,
            "similar_controls": vector_controls,  # Add this field for response generation
            "annex": annex,
            "annex_guidance": annex_guidance,
            "annex_family_controls": annex_family_controls,
            "sources": {
                "mongodb": len(mongo_controls),
                "vector_search": len(vector_controls),
                "annex_guidance": 1 if annex_guidance else 0,
                "annex_family": len(annex_family_controls)
            }
        }

    def _get_general_query_context(self, query_embedding: List[float], user_id: str, query_text: str = "", vector_only: bool = True) -> Dict:
        try:
            # 1. Vector search for similar controls - increase limit to get more results for filtering
            similar_controls = self.vector_db.search_similar_controls(query_embedding, limit=15)  # Increased from 5 to 15
            similar_risks = self.vector_db.search_similar_risks(query_embedding, limit=3)
            
            # 2. IMPORTANT: Also search existing controls in MongoDB for the user
            existing_controls = self._search_existing_controls_by_query(user_id, query_embedding)
            
            # 3. NEW: Text-based search for better Information Security control discovery
            text_search_controls = []
            if query_text:
                text_search_controls = self._search_existing_controls_by_text(user_id, query_text, limit=5)
            
            # 4. Get general ISO guidance from annex service
            iso_guidance = self.annex.get_annex_controls(limit=5)
            
            # 5. Also search annex controls by text query for better relevance
            if query_text:
                text_based_annex_controls = self.annex.search_annex_controls(query_text, limit=5)
                # Combine and prioritize results
                combined_iso_guidance = text_based_annex_controls if text_based_annex_controls else iso_guidance
            else:
                combined_iso_guidance = iso_guidance
            
            # 6. Combine all results - prioritize existing controls, then text search, then vector search, then ISO guidance
            all_controls = []
            
            # Add existing controls first (these are user's actual controls)
            for control in existing_controls:
                control['source'] = 'existing_user_controls'
                all_controls.append(control)
            
            # Add text search controls (avoid duplicates)
            existing_ids = {c.get('control_id', '') for c in all_controls}
            for control in text_search_controls:
                if control.get('control_id') not in existing_ids:
                    control['source'] = 'text_search'
                    all_controls.append(control)
            
            # Add vector search controls (avoid duplicates)
            existing_ids = {c.get('control_id', '') for c in all_controls}
            for control in similar_controls:
                if control.get('control_id') not in existing_ids:
                    control['source'] = 'vector_search'
                    all_controls.append(control)
            
            # Add ISO guidance controls (avoid duplicates)
            existing_references = {c.get('reference', '') for c in all_controls}
            for control in combined_iso_guidance:
                if control.get('reference') not in existing_references:
                    control['source'] = 'iso_guidance'
                    all_controls.append(control)
            
            # 7. Count high-relevance vector controls for logging
            high_relevance_count = 0
            for control in similar_controls:
                if control.get('source') == 'vector_search' and control.get('similarity', 0) > 0.8:
                    high_relevance_count += 1
            
            print(f"🔍 General query context results:")
            print(f"   - Existing user controls: {len(existing_controls)}")
            print(f"   - Text search controls: {len(text_search_controls)}")
            print(f"   - Vector search controls: {len(similar_controls)}")
            print(f"   - High-relevance vector controls (>0.8): {high_relevance_count}")
            print(f"   - ISO guidance controls: {len(combined_iso_guidance)}")
            print(f"   - Total combined controls: {len(all_controls)}")
            
            # If vector_only is True, return only vector search results in similar_controls
            if vector_only:
                return {
                    "similar_controls": all_controls,  # Return ALL controls for reference
                    "similar_risks": similar_risks,
                    "iso_guidance": combined_iso_guidance,
                    "existing_controls": existing_controls,
                    "text_search_controls": text_search_controls,
                    "total_controls_found": len(all_controls),
                    "vector_only_mode": True,  # Flag to indicate vector-only display
                    "vector_search_count": len(similar_controls),  # Count of actual vector search results
                    "high_relevance_count": high_relevance_count  # Count of high-relevance controls
                }
            else:
                return {
                    "similar_controls": all_controls,  # Return ALL controls found
                    "similar_risks": similar_risks,
                    "iso_guidance": combined_iso_guidance,
                    "existing_controls": existing_controls,
                    "text_search_controls": text_search_controls,
                    "total_controls_found": len(all_controls),
                    "vector_only_mode": False,
                    "high_relevance_count": high_relevance_count
                }
            
        except Exception as e:
            print(f"Vector search failed in general query: {e}")
            # Fallback to just searching existing controls
            try:
                existing_controls = self._search_existing_controls_by_query(user_id, query_embedding)
                text_search_controls = []
                if query_text:
                    text_search_controls = self._search_existing_controls_by_text(user_id, query_text, limit=5)
                
                all_controls = existing_controls + text_search_controls
                
                return {
                    "similar_controls": all_controls,
                    "similar_risks": [],
                    "iso_guidance": [],
                    "existing_controls": existing_controls,
                    "text_search_controls": text_search_controls,
                    "total_controls_found": len(all_controls),
                    "vector_only_mode": vector_only,
                    "high_relevance_count": 0
                }
            except Exception as fallback_error:
                print(f"Fallback search also failed: {fallback_error}")
                return {
                    "similar_controls": [],
                    "similar_risks": [],
                    "iso_guidance": [],
                    "existing_controls": [],
                    "text_search_controls": [],
                    "total_controls_found": 0,
                    "vector_only_mode": vector_only,
                    "high_relevance_count": 0
                }
    
    def _search_existing_controls_by_query(self, user_id: str, query_embedding: List[float]) -> List[Dict]:
        """Search through existing stored controls for the user based on query similarity"""
        try:
            # Get all user controls
            all_controls = list(self.mongo_db.controls.find({"user_id": user_id}))
            
            if not all_controls:
                print(f"   📋 No existing controls found for user: {user_id}")
                return []
            
            print(f"   📋 Found {len(all_controls)} existing controls for user: {user_id}")
            
            # For each control, create a searchable text and check similarity
            control_scores = []
            for control in all_controls:
                # Create searchable text from control fields
                searchable_text = f"{control.get('title', '')} {control.get('description', '')} {control.get('control_statement', '')} {control.get('implementation_guidance', '')}"
                
                if searchable_text.strip():
                    # Generate embedding for the control text
                    control_embedding = self.openai.get_embedding(searchable_text)
                    
                    # Calculate cosine similarity (simple dot product for now)
                    similarity = self._calculate_similarity(query_embedding, control_embedding)
                    
                    control_scores.append({
                        "control": control,
                        "similarity": similarity,
                        "searchable_text": searchable_text
                    })
            
            # Sort by similarity and return top results
            control_scores.sort(key=lambda x: x["similarity"], reverse=True)
            
            # Return top 5 most similar controls
            top_controls = []
            for item in control_scores[:5]:
                control = item["control"]
                # Ensure we have all required fields
                enriched_control = {
                    "id": str(control.get("_id", "")),
                    "control_id": control.get("control_id", ""),
                    "title": control.get("title", ""),
                    "description": control.get("description", ""),
                    "domain_category": control.get("domain_category", ""),
                    "annex_reference": control.get("annex_reference", ""),
                    "control_statement": control.get("control_statement", ""),
                    "implementation_guidance": control.get("implementation_guidance", ""),
                    "risk_id": control.get("risk_id", ""),
                    "user_id": control.get("user_id", ""),
                    "similarity": item["similarity"]
                }
                top_controls.append(enriched_control)
            
            print(f"   ✅ Found {len(top_controls)} relevant existing controls")
            return top_controls
            
        except Exception as e:
            print(f"   ❌ Error searching existing controls: {e}")
            return []

    def _search_existing_controls_by_text(self, user_id: str, query_text: str, limit: int = 10) -> List[Dict]:
        """Search existing controls by text query for better Information Security control discovery"""
        try:
            print(f"   🔍 Searching existing controls by text: '{query_text[:50]}{'...' if len(query_text) > 50 else ''}'")
            
            # Use the new MongoDB text search method
            text_results = self.mongo_db.search_controls_by_text(query_text, user_id, limit)
            print(f"   📋 Text search found {len(text_results)} controls")
            
            # Convert to the expected format
            formatted_controls = []
            for control in text_results:
                formatted_control = {
                    "id": control.get("id", ""),
                    "control_id": control.get("control_id", ""),
                    "title": control.get("title", ""),
                    "description": control.get("description", ""),
                    "domain_category": control.get("domain_category", ""),
                    "annex_reference": control.get("annex_reference", ""),
                    "control_statement": control.get("control_statement", ""),
                    "implementation_guidance": control.get("implementation_guidance", ""),
                    "risk_id": control.get("risk_id", ""),
                    "user_id": control.get("user_id", ""),
                    "similarity": 0.8,  # High similarity for text matches
                    "source": "text_search"
                }
                formatted_controls.append(formatted_control)
            
            print(f"   ✅ Text search completed, found {len(formatted_controls)} controls")
            return formatted_controls
            
        except Exception as e:
            print(f"   ❌ Error in text search: {e}")
            return []
    
    def _calculate_similarity(self, query_embedding: List[float], control_embedding: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            if len(query_embedding) != len(control_embedding):
                return 0.0
            
            # Calculate dot product
            dot_product = sum(a * b for a, b in zip(query_embedding, control_embedding))
            
            # Calculate magnitudes
            query_magnitude = sum(a * a for a in query_embedding) ** 0.5
            control_magnitude = sum(b * b for b in control_embedding) ** 0.5
            
            # Avoid division by zero
            if query_magnitude == 0 or control_magnitude == 0:
                return 0.0
            
            # Calculate cosine similarity
            similarity = dot_product / (query_magnitude * control_magnitude)
            
            return max(0.0, min(1.0, similarity))  # Clamp between 0 and 1
            
        except Exception as e:
            print(f"   ❌ Error calculating similarity: {e}")
            return 0.0

    def _get_risk_patterns(self, risk_category: str, user_domain: str) -> List[Dict]:
        return self.graph_db.get_controls_by_annex_and_category("A.", risk_category)

    def store_control_embeddings(self, controls: List[Dict]):
        for control in controls:
            embedding_text = f"{control['title']} {control['description']}"
            embedding = self.openai.get_embedding(embedding_text)
            
            self.vector_db.store_control_embedding(
                control['id'],
                control['user_id'],
                control['title'],
                control['description'],
                control['annex_reference'],
                embedding
            )

    def store_risk_embedding(self, risk_data: Dict):
        embedding_text = f"{risk_data.get('description', '')} {risk_data.get('category', '')}"
        embedding = self.openai.get_embedding(embedding_text)
        
        self.vector_db.store_risk_embedding(
            risk_data.get("id", ""),
            risk_data.get("user_id", ""),
            risk_data.get("description", ""),
            risk_data.get("category", ""),
            embedding
        )

    def store_query_embedding(self, query_id: str, user_id: str, query_text: str, intent: str, response_context: Dict):
        """Store query embedding for learning and analytics"""
        try:
            # Generate embedding for the query
            query_embedding = self.openai.get_embedding(query_text)
            
            # Store in vector database
            self.vector_db.store_query_embedding(
                query_id, 
                user_id, 
                query_text, 
                intent, 
                response_context, 
                query_embedding
            )
            
            return True
        except Exception as e:
            print(f"Failed to store query embedding: {e}")
            return False

rag_service = RAGService()
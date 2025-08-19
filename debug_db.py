#!/usr/bin/env python3
"""
Debug script to test database connection issues
"""
import sys
import os
sys.path.append('app')

try:
    from app.postgres import postgres_service
    from app.config import POSTGRES_URI
    print(f"POSTGRES_URI: {POSTGRES_URI}")
    print(f"Connection status: {postgres_service.conn is not None}")
    
    if postgres_service.conn:
        print("Testing vector search...")
        result = postgres_service.search_similar_controls([0.1] * 1536, limit=1)
        print(f"Search result: {result}")
    else:
        print("No database connection available")
        
except Exception as e:
    print(f"Error during debug: {e}")
    print(f"Error type: {type(e)}")
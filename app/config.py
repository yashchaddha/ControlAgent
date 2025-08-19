import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
POSTGRES_URI = os.getenv("POSTGRES_URI")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")

DATABASE_NAME = "isoriskagent"
COLLECTIONS = {
    "users": "users",
    "risks": "finalized_risks", 
    "controls": "controls",
    "sessions": "agent_sessions"
}
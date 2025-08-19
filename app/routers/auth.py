from fastapi import APIRouter, HTTPException, Depends, Form
from fastapi.security import OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import jwt
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Union
from ..config import SECRET_KEY
from ..database import mongodb
from ..neo4j_db import neo4j_service
from ..auth import get_current_user

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserCreate(BaseModel):
    username: str
    password: str
    organization_name: str
    location: str
    domain: str
    risks_applicable: list = []

class Token(BaseModel):
    access_token: str
    token_type: str

def get_password_hash(password):
    return password

def verify_password(plain_password, hashed_password):
    return plain_password == hashed_password

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=60))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

@router.post("/signup", response_model=Token)
def signup(user: UserCreate):
    if mongodb.users.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_password = get_password_hash(user.password)
    user_data = {
        "username": user.username,
        "hashed_password": hashed_password,
        "organization_name": user.organization_name,
        "location": user.location,
        "domain": user.domain,
        "risks_applicable": user.risks_applicable,
        "created_at": datetime.utcnow()
    }
    
    mongodb.users.insert_one(user_data)
    
    try:
        neo4j_service.create_user_node({
            "user_id": user.username,
            "username": user.username,
            "organization_name": user.organization_name,
            "location": user.location,
            "domain": user.domain
        })
    except Exception as e:
        print(f"Warning: Failed to create user in Neo4j: {e}")
    
    access_token = create_access_token({"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = mongodb.users.find_one({"username": form_data.username})

    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token = create_access_token({"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login-json", response_model=Token)
def login_json(login_req: LoginRequest):
    user = mongodb.users.find_one({"username": login_req.username})

    if not user or not verify_password(login_req.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token = create_access_token({"sub": login_req.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me")
def get_current_user_info(current_user = Depends(get_current_user)):
    user_info = {
        "username": current_user["username"],
        "organization_name": current_user.get("organization_name", ""),
        "location": current_user.get("location", ""),
        "domain": current_user.get("domain", ""),
        "created_at": current_user.get("created_at", "")
    }
    return user_info
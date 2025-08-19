from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, controls, risks, search, kg

app = FastAPI(title="ISO 27001 Control Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(controls.router, prefix="/controls", tags=["controls"])
app.include_router(risks.router, prefix="/risks", tags=["risks"])
app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(kg.router, prefix="/kg", tags=["knowledge-graph"])

@app.get("/")
async def root():
    return {"message": "ISO 27001 Control Generation Agent"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
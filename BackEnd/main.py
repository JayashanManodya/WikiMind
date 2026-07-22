import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Ensure project root is in sys.path so running from inside BackEnd/ or root works seamlessly
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from BackEnd.schemas import RootResponse, HealthResponse
from BackEnd.routers.upload import router as upload_router

# Load environment variables
load_dotenv()

app = FastAPI(
    title=os.getenv("APP_NAME", "WikiMind"),
    description="AI-powered Knowledge Management & Wikipedia-style QA Platform API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(upload_router)

@app.get(
    "/",
    response_model=RootResponse,
    summary="API Root",
    description="Returns system status, application name, environment, and welcome message."
)
def read_root():
    return RootResponse(
        status="online",
        app=os.getenv("APP_NAME", "WikiMind"),
        environment=os.getenv("APP_ENV", "development"),
        message="Welcome to WikiMind Knowledge Management System API"
    )

@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="System health inspection and path accessibility check."
)
def health_check():
    storage_dir = os.getenv("STORAGE_DIR", "./storage")
    wiki_dir = os.getenv("WIKI_DIR", "./wiki")
    llm_provider = os.getenv("LLM_PROVIDER", "openai")
    
    storage_accessible = os.path.exists(storage_dir) or os.access(".", os.W_OK)

    return HealthResponse(
        status="healthy",
        storage_dir=storage_dir,
        wiki_dir=wiki_dir,
        llm_provider=llm_provider,
        storage_accessible=storage_accessible
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("BackEnd.main:app", host=host, port=port, reload=True)

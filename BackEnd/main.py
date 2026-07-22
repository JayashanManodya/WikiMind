import os
from fastapi import FastAPI
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

app = FastAPI(
    title=os.getenv("APP_NAME", "WikiMind"),
    description="AI-powered Knowledge Management & Wikipedia-style QA Platform API",
    version="0.1.0"
)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "app": os.getenv("APP_NAME", "WikiMind"),
        "environment": os.getenv("APP_ENV", "development"),
        "message": "Welcome to WikiMind Knowledge Management System API"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "storage_dir": os.getenv("STORAGE_DIR", "./storage"),
        "wiki_dir": os.getenv("WIKI_DIR", "./wiki"),
        "llm_provider": os.getenv("LLM_PROVIDER", "openai")
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("main:app", host=host, port=port, reload=True)

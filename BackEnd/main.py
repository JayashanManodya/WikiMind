import uvicorn

if __name__ == "__main__":
    print("Starting WikiLLM API Server...")
    print("Interactive API Documentation: http://127.0.0.1:8000/docs")
    print("Alternative ReDoc Documentation: http://127.0.0.1:8000/redoc")
    uvicorn.run("app.api:app", host="127.0.0.1", port=8000, reload=True)
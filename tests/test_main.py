import os
import pytest
from fastapi.testclient import TestClient
from BackEnd.main import app

client = TestClient(app)

def test_read_root():
    """Test root endpoint '/' returns online status and app metadata"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["app"] == os.getenv("APP_NAME", "WikiMind")
    assert "message" in data
    assert "environment" in data

def test_health_check():
    """Test '/health' endpoint returns healthy status and configured storage paths"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "storage_dir" in data
    assert "wiki_dir" in data
    assert "llm_provider" in data
    assert data["storage_accessible"] is True

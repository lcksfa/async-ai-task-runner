#!/usr/bin/env python3
"""
Simple test to verify basic imports work
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_imports():
    """Test that basic app imports work"""
    try:
        from app.models import Task
        from app.schemas import TaskCreate, TaskStatus
        from app.main import app
        print("✅ All basic imports successful!")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_health_endpoint():
    """Test that we can create a simple test client"""
    try:
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✅ Health check endpoint test passed!")
        return True
    except Exception as e:
        print(f"❌ Health check test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Running Simple Tests")
    print("=" * 50)

    success = True

    if not test_basic_imports():
        success = False

    if not test_health_endpoint():
        success = False

    print("=" * 50)
    if success:
        print("🎉 All simple tests passed!")
        sys.exit(0)
    else:
        print("💥 Some simple tests failed!")
        sys.exit(1)
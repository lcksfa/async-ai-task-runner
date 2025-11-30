#!/usr/bin/env python3
"""
测试简化的应用启动
"""
import sys
import os

# Add project to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

async def test_app_imports():
    """测试应用导入"""
    print("🔍 Testing app imports...")

    try:
        from app.main import app
        from app.core.config_simple import settings
        print("✅ App imports successful!")
        print(f"✅ App title: {app.title}")
        return True
    except Exception as e:
        print(f"❌ App import failed: {e}")
        return False

async def test_health_endpoint():
    """测试健康检查端点"""
    print("🔍 Testing health endpoint...")

    try:
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        print("✅ Health check passed!")
        print(f"✅ Status: {data['status']}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

async def main():
    """运行所有测试"""
    print("🧪 Simple App Tests")
    print("=" * 50)

    tests = [
        ("App Imports", test_app_imports),
        ("Health Endpoint", test_health_endpoint),
    ]

    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            result = await test_func()
            if result:
                print(f"✅ {test_name} passed!")
            else:
                print(f"❌ {test_name} failed!")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")

    print("\n" + "=" * 50)
    print("📈 APP TEST SUMMARY")
    print("=" * 50)

    passed = sum(1 for _, result in tests if result)
    total = len(tests)

    if passed == total:
        print("🎉 All app tests passed!")
        return 0
    else:
        print(f"💥 {total - passed} tests failed!")
        return 1

if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
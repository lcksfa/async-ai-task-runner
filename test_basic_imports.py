#!/usr/bin/env python3
"""
基本导入测试
"""
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_direct_imports():
    """直接测试所有模块的导入"""
    print("🔍 Testing direct imports...")

    try:
        # Test config_fixed.py directly
        import app.core.config_fixed as config_module
        print("✅ config_fixed.py imported successfully")

        # Create settings instance
        settings = config_module.Settings()
        print(f"✅ Settings created: {settings.app_name}")
        return True
    except Exception as e:
        print(f"❌ Direct import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_absolute_imports():
    """使用绝对导入"""
    print("🔍 Testing absolute imports...")

    try:
        # Test main.py
        from app.main import app
        print("✅ app.main imported successfully")

        # Test API router
        from app.api.v1.api import api_router
        print("✅ API router imported successfully")

        return True
    except Exception as e:
        print(f"❌ Absolute import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Basic Import Tests")
    print("=" * 50)

    # Test step by step
    if test_direct_imports():
        print("✅ Direct imports work!")

        if test_absolute_imports():
            print("✅ All imports successful!")
            sys.exit(0)
        else:
            print("❌ Absolute imports failed!")
            sys.exit(1)
    else:
        print("❌ Direct imports failed!")
        sys.exit(1)
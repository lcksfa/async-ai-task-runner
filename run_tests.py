#!/usr/bin/env python3
"""
🧪 Async AI Task Runner - Test Runner Script

Convenient test runner with common development scenarios and reporting.
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description=""):
    """Run command and handle output."""
    print(f"🚀 {description}")
    print(f"💻 Command: {cmd}")
    print("-" * 60)

    result = subprocess.run(cmd, shell=True, capture_output=False, text=True)

    if result.returncode == 0:
        print(f"✅ {description} - PASSED")
    else:
        print(f"❌ {description} - FAILED (exit code: {result.returncode})")

    print("-" * 60)
    return result.returncode == 0

def main():
    parser = argparse.ArgumentParser(description="Async AI Task Runner Test Runner")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--external", action="store_true", help="Run tests requiring external services")
    parser.add_argument("--slow", action="store_true", help="Run slow tests")
    parser.add_argument("--cov", action="store_true", help="Generate coverage report")
    parser.add_argument("--fast", action="store_true", help="Run fast tests only (exclude slow and external)")
    parser.add_argument("--ci", action="store_true", help="CI mode - comprehensive testing with coverage")
    parser.add_argument("--watch", action="store_true", help="Watch mode (requires pytest-watch)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--file", help="Run specific test file")
    parser.add_argument("--function", help="Run specific test function")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Change to project root
    project_root = Path(__file__).parent
    os.chdir(project_root)

    # Base pytest command - use uv if available, fallback to python
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
        pytest_cmd = "uv run pytest tests/"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest_cmd = "python -m pytest tests/"

    # Add verbosity
    if args.verbose:
        pytest_cmd += " -v"
    else:
        pytest_cmd += " -q"

    # Add coverage
    if args.cov or args.ci:
        pytest_cmd += " --cov=app --cov-report=html --cov-report=term-missing"

    # Add debug logging
    if args.debug or args.ci:
        pytest_cmd += " --log-cli-level=DEBUG"

    # Build marker selection
    markers = []

    if args.unit:
        markers.append("unit")
    elif args.integration:
        markers.append("integration")
    elif args.performance:
        markers.append("performance")
    elif args.external:
        markers.append("external")
    elif args.fast:
        pytest_cmd += " -m 'not slow and not external'"
    elif args.slow:
        markers.append("slow")

    # Apply markers
    if markers:
        marker_expr = " or ".join(markers)
        pytest_cmd += f' -m "{marker_expr}"'

    # Specific file
    if args.file:
        pytest_cmd = f"python -m pytest {args.file}"
        if args.verbose:
            pytest_cmd += " -v"

    # Specific function
    if args.function:
        if args.file:
            pytest_cmd += f"::{args.function}"
        else:
            pytest_cmd += f" -k {args.function}"

    # CI mode
    if args.ci:
        # Comprehensive testing
        print("🤖 CI Mode - Running comprehensive test suite...")

        tests_success = True

        # 1. Run unit tests
        if not run_command(
            "uv run pytest tests/ -m unit --cov=app --cov-report=xml",
            "Running Unit Tests"
        ):
            tests_success = False

        # 2. Run integration tests
        if not run_command(
            "uv run pytest tests/ -m integration --cov=app --cov-append --cov-report=xml",
            "Running Integration Tests"
        ):
            tests_success = False

        # 3. Run async tests
        if not run_command(
            "uv run pytest tests/test_async_features.py -m 'not slow' --cov=app --cov-append --cov-report=xml",
            "Running Async Features Tests"
        ):
            tests_success = False

        # 4. Run MCP tests
        if not run_command(
            "uv run pytest tests/test_mcp_server.py --cov=app --cov-append --cov-report=xml",
            "Running MCP Server Tests"
        ):
            tests_success = False

        if tests_success:
            print("🎉 All CI tests passed!")
            sys.exit(0)
        else:
            print("💥 Some CI tests failed!")
            sys.exit(1)

    # Watch mode
    elif args.watch:
        try:
            import pytest_watch
        except ImportError:
            print("❌ pytest-watch not installed. Install with: pip install pytest-watch")
            sys.exit(1)

        watch_cmd = pytest_cmd.replace("python -m pytest", "ptw")
        run_command(watch_cmd, "Running tests in watch mode")

    # Regular test run
    else:
        # Add first failure stop for CI
        if args.ci:
            pytest_cmd += " -x"

        success = run_command(pytest_cmd, "Running Test Suite")

        if not success:
            sys.exit(1)

        # Show coverage if generated
        if args.cov and os.path.exists("htmlcov/index.html"):
            print("\n📊 Coverage report generated: htmlcov/index.html")
            print("💡 Open with: open htmlcov/index.html")

def show_test_menu():
    """Show interactive test menu."""
    print("🧪 Async AI Task Runner - Test Menu")
    print("=" * 50)
    print("1. 🏃 Quick Test (fast tests only)")
    print("2. 🧪 All Tests (comprehensive)")
    print("3. 🧪 Unit Tests only")
    print("4. 🔗 Integration Tests only")
    print("5. 🚀 Async Features Tests")
    print("6. 🤖 AI Service Tests")
    print("7. 🌐 MCP Server Tests")
    print("8. 📊 Tests with Coverage")
    print("9. 🐛 Debug Mode (verbose logging)")
    print("10. 👀 Watch Mode")
    print("11. 🤖 CI Mode (comprehensive + coverage)")
    print("0. Exit")
    print("=" * 50)

    while True:
        try:
            choice = input("Select option (0-11): ").strip()

            if choice == "0":
                break
            elif choice == "1":
                os.system("uv run pytest tests/ -m 'not slow'")
            elif choice == "2":
                os.system("uv run pytest tests/ --cov=app --cov-report=term")
            elif choice == "3":
                os.system("uv run pytest tests/ -m unit --cov=app --cov-report=term")
            elif choice == "4":
                os.system("uv run pytest tests/ -m integration --cov=app --cov-report=term")
            elif choice == "5":
                os.system("uv run pytest tests/test_async_features.py --cov=app --cov-report=term")
            elif choice == "6":
                os.system("uv run pytest tests/test_ai_service.py --cov=app --cov-report=term")
            elif choice == "7":
                os.system("uv run pytest tests/test_mcp_server.py --cov=app --cov-report=term")
            elif choice == "8":
                os.system("uv run pytest tests/ --cov=app --cov-report=html --cov-report=term")
            elif choice == "9":
                os.system("uv run pytest tests/ --log-cli-level=DEBUG")
            elif choice == "10":
                try:
                    import pytest_watch
                    os.system("uv run ptw tests/")
                except ImportError:
                    print("❌ pytest-watch not installed. Install with: uv add --dev pytest-watch")
            elif choice == "11":
                os.system("uv run pytest tests/ --cov=app --cov-report=html --cov-report=term")
            else:
                print("❌ Invalid option. Please select 0-11.")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        show_test_menu()
    else:
        main()
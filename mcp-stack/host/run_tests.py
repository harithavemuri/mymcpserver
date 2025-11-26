"""Run tests for the MCP host."""
import asyncio
import sys
import importlib
import inspect
from typing import Any, Callable, Dict, List, Type, TypeVar
from unittest.mock import AsyncMock, patch, MagicMock

# Add the src directory to the Python path
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Import test modules
try:
    from tests.test_mcp_client_models import *
    from tests.test_api_models import *
except ImportError as e:
    print(f"Error importing test modules: {e}")
    sys.exit(1)

# Type variable for test functions
T = TypeVar('T')

def find_test_functions(module_name: str) -> List[Callable]:
    """Find all test functions in a module."""
    module = sys.modules[module_name]
    return [
        func for name, func in inspect.getmembers(module, inspect.isfunction)
        if name.startswith('test_') and asyncio.iscoroutinefunction(func)
    ]

async def run_tests():
    """Run all tests and report results."""
    test_modules = [
        'tests.test_mcp_client_models',
        'tests.test_api_models'
    ]

    total_tests = 0
    passed_tests = 0
    failed_tests = 0

    for module_name in test_modules:
        print(f"\nRunning tests in {module_name}...")
        print("=" * 80)

        test_functions = find_test_functions(module_name)

        for test_func in test_functions:
            test_name = f"{module_name}.{test_func.__name__}"
            print(f"Running {test_name}...", end=" ")
            total_tests += 1

            try:
                await test_func()
                print("✓ PASSED")
                passed_tests += 1
            except Exception as e:
                print(f"✗ FAILED: {str(e)}")
                failed_tests += 1
                import traceback
                traceback.print_exc()

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success rate: {passed_tests / total_tests * 100:.1f}%" if total_tests > 0 else "No tests run")
    print("=" * 80)

    return 0 if failed_tests == 0 else 1

if __name__ == "__main__":
    # Run the tests
    exit_code = asyncio.run(run_tests())
    sys.exit(exit_code)

import pytest
import sys

if __name__ == "__main__":
    # Run the specific test with verbose output
    sys.exit(pytest.main(["tests/test_api.py::test_search_customers", "-v", "-s"]))

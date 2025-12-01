import pytest
import sys

if __name__ == "__main__":
    # Run pytest and exit with its return code
    sys.exit(pytest.main(["tests/test_erie_generation.py", "-vv"]))

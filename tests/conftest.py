import sys
import os

# Add the project root (clarvyn/) to sys.path so `from core.config import ...` works
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

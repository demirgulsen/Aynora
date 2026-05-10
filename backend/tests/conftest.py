import sys
import os

# Add backend/ root to Python path so 'services', 'config' etc. are importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
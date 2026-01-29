"""
Pytest configuration and fixtures for backend tests.
"""
import os
import sys

# Add src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

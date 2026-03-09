"""
Pytest configuration and shared fixtures.
"""

import os

# Set up test environment variables BEFORE any imports
os.environ["OPENAI_API_KEY"] = "test-openai-key"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-jwt-tokens"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["FILE_STORAGE_ROOT"] = "/tmp/test_storage"

import pytest
from unittest.mock import Mock, patch
from hypothesis import settings, Verbosity

# Configure Hypothesis profiles for faster test execution
settings.register_profile("fast", max_examples=20, verbosity=Verbosity.normal)
settings.register_profile("ci", max_examples=50, verbosity=Verbosity.normal)
settings.register_profile("thorough", max_examples=200, verbosity=Verbosity.verbose)

# Load the profile from environment or default to "fast"
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "fast"))

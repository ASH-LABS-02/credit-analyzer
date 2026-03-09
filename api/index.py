"""
Vercel Serverless Function Entry Point
This file routes all API requests to the FastAPI application
"""
import sys
import os

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.main import app

# Vercel handler
handler = app

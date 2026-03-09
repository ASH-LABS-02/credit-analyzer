"""
Vercel Serverless Function Entry Point
This file routes all API requests to the FastAPI application
"""
import sys
import os

# Add backend directory to Python path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

from app.main import app
from mangum import Mangum

# Vercel handler using Mangum adapter
handler = Mangum(app, lifespan="off")

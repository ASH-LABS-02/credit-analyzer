"""
Vercel serverless function entry point for FastAPI
"""
from app.main import app

# Vercel expects a variable named 'app' or 'handler'
handler = app

"""
API Module - FastAPI application and routes

Includes:
- Main FastAPI application setup
- Request/response models
- WebSocket handling
- API route definitions
- CORS and middleware configuration
"""

try:
    from .main import app
    from .models import *
except ImportError as e:
    import warnings
    warnings.warn(f"Could not import API modules: {e}", ImportWarning)

__all__ = [
    "app",
]

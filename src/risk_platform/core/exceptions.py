"""Base exception hierarchy shared across layers.

Framework-specific error handlers (FastAPI exception handlers) translate
these into HTTP responses without domain/application code knowing about HTTP.
"""

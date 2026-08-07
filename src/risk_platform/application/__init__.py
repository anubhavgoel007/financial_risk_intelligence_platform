"""Application layer (Use Cases).

Orchestrates domain objects to fulfil specific application actions.
Depends only on the domain layer and its own abstract ports; knows nothing
about FastAPI, SQLAlchemy, or XGBoost directly.
"""

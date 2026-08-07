"""Infrastructure layer (Frameworks & Drivers).

Concrete implementations of the ports declared in domain/application:
SQLAlchemy repositories, XGBoost model adapters, Gemini API client, caching.
This is the only layer allowed to depend on third-party frameworks.
"""

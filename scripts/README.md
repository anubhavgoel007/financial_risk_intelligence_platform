Standalone operational scripts (not part of the application package):
- seed_db.py        - populate the database with reference/sample data
- train_model.py     - CLI entry point to run an XGBoost training pipeline
- run_migrations.py  - convenience wrapper around Alembic

These call into application use cases; they contain no business logic themselves.

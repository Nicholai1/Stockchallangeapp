This folder contains Alembic migration environment files.

Usage:

1. Install alembic in your environment:
   pip install alembic

2. Generate an autogenerate migration:
   alembic revision --autogenerate -m "create tables"

3. Apply migrations:
   alembic upgrade head

Notes:
- The default sqlalchemy.url is set to `sqlite:///./portfolio.db` in `alembic.ini`.
- The env.py will prefer `app.database.SQLALCHEMY_DATABASE_URL` if available.

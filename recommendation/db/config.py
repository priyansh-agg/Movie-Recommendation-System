"""
Database configuration — reads connection URLs from environment.
"""

import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/movie_recommender",
)

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

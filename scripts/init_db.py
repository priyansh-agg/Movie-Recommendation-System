"""
Database initialisation script.

Creates all tables defined in the ORM models.
Run once after setting up the PostgreSQL database.

Usage::

    python scripts/init_db.py
"""

import sys
from pathlib import Path

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv
load_dotenv()

from recommendation.db.config import DATABASE_URL
from recommendation.db.session import engine
from recommendation.db.models import Base


def main():
    print(f"Database: {DATABASE_URL[:50]}...")
    print("Creating tables...")

    Base.metadata.create_all(bind=engine)

    print("Tables created:")
    for table_name in Base.metadata.tables:
        print(f"  - {table_name}")

    print("\nDone!")


if __name__ == "__main__":
    main()

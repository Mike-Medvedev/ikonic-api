"""Pre start script for creating SQL tables and seeding data."""

from core.db import init_db

if __name__ == "__main__":
    init_db()

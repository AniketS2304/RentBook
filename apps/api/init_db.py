import os
import sys

# Ensure app is importable
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import app.models  # noqa: F401
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine

def init_db():
    print(f"Initializing database at: {settings.DATABASE_URL}")
    Base.metadata.create_all(bind=engine)
    print("Tables created:")
    for table_name in Base.metadata.tables.keys():
        print(f" - {table_name}")
    print("Database initialization complete.")

if __name__ == "__main__":
    init_db()

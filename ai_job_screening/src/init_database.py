from database.database import Base, engine, SQLALCHEMY_DATABASE_URL
from database.models import JobDescription, Candidate, CandidateMatch
import os

def init_database():
    # Remove existing database if it exists
    db_path = SQLALCHEMY_DATABASE_URL.replace('sqlite:///', '')
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database at {db_path}")

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_database()

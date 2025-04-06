from .database import Base, engine
from .models import JobDescription, Candidate, CandidateMatch

def init_database():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_database()

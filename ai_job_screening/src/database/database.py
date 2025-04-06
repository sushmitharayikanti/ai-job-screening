from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from pathlib import Path

# Create database directory if it doesn't exist
db_dir = Path(__file__).parent.parent / "data"
db_dir.mkdir(exist_ok=True)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_dir}/job_screening.db"
print(f"Database path: {db_dir}/job_screening.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

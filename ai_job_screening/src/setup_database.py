from pathlib import Path
import sqlite3

# Create data directory
data_dir = Path(__file__).parent / "data"
data_dir.mkdir(exist_ok=True)

# Database path
db_path = data_dir / "job_screening.db"

# Create tables
def create_tables():
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create job_descriptions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS job_descriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title VARCHAR(255) NOT NULL,
        company VARCHAR(255) NOT NULL,
        description TEXT NOT NULL,
        required_skills TEXT NOT NULL,
        required_experience INTEGER,
        required_qualifications TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Create candidates table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL UNIQUE,
        resume_text TEXT NOT NULL,
        skills TEXT,
        experience_years INTEGER,
        qualifications TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Create candidate_matches table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidate_matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        candidate_id INTEGER NOT NULL,
        match_score FLOAT NOT NULL,
        shortlisted BOOLEAN DEFAULT FALSE,
        interview_scheduled BOOLEAN DEFAULT FALSE,
        interview_datetime TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (job_id) REFERENCES job_descriptions(id),
        FOREIGN KEY (candidate_id) REFERENCES candidates(id)
    )
    """)

    conn.commit()
    conn.close()
    print(f"Database created at: {db_path}")
    print("All tables created successfully!")

if __name__ == "__main__":
    if db_path.exists():
        db_path.unlink()
        print(f"Removed existing database at: {db_path}")
    create_tables()

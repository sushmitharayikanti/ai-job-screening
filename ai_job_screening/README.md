# AI Job Screening System

An intelligent system that automates the job screening process using AI and Data Intelligence.

## Features

- Job Description Summarizer: Extracts key information from job descriptions
- CV Parser: Analyzes candidate CVs and extracts relevant information
- Matching Engine: Scores candidates based on job requirements
- Interview Scheduler: Automates interview scheduling for shortlisted candidates
- SQLite Database: Stores all relevant data and matching history

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
python src/database/init_db.py
```

4. Start the application:
```bash
python src/main.py
```

## Project Structure

- `src/`: Main source code
  - `agents/`: AI agents for different tasks
  - `database/`: Database models and operations
  - `api/`: FastAPI endpoints
  - `utils/`: Helper functions and utilities
- `tests/`: Unit and integration tests
- `data/`: Sample data and model files
- `templates/`: Email templates

## API Documentation

Access the API documentation at `http://localhost:8000/docs` when running the application.

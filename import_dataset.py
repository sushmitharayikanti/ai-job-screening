"""
Import script for hackathon dataset into AI Job Screening System.
This script imports job descriptions from a CSV file and resumes from a folder of PDFs.
"""

import os
import csv
import pandas as pd
from pathlib import Path
import shutil
import logging
import sys
from sqlalchemy.orm import Session
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project directory to the path to allow imports from the project
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import project modules
from ai_job_screening.src.database.database import get_db, engine
from ai_job_screening.src.database.models import JobDescription, Candidate, Base
from ai_job_screening.src.agents.cv_parser import CVParser

def ensure_uploads_dir():
    """Ensure the uploads directory exists."""
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)
    return uploads_dir

def import_job_descriptions(csv_path, db):
    """
    Import job descriptions from a CSV file.
    Expected columns: Job Title, Job Description
    """
    logger.info(f"Importing job descriptions from {csv_path}")
    try:
        # Read CSV file with different encodings to handle special characters
        encodings_to_try = ['utf-8', 'latin1', 'cp1252', 'ISO-8859-1']
        
        df = None
        for encoding in encodings_to_try:
            try:
                logger.info(f"Trying to read CSV with {encoding} encoding")
                df = pd.read_csv(csv_path, encoding=encoding)
                logger.info(f"Successfully read CSV with {encoding} encoding")
                break
            except UnicodeDecodeError:
                logger.warning(f"Failed to decode with {encoding}, trying next encoding")
        
        if df is None:
            logger.error("Failed to read CSV with any encoding")
            return False
        
        # Check if required columns exist (adjusted for your actual dataset)
        if 'Job Title' not in df.columns or 'Job Description' not in df.columns:
            logger.error(f"CSV must contain columns: 'Job Title', 'Job Description'")
            return False
        
        # Process each job description
        for _, row in df.iterrows():
            title = row['Job Title']
            description = row['Job Description']
            company = "Hackathon Company"  # Default company name
            
            # Skip if title or description is empty
            if pd.isna(title) or pd.isna(description) or not str(title).strip() or not str(description).strip():
                continue
                
            logger.info(f"Processing job: {title}")
            
            # Parse skills from description
            skills_text = str(description).lower()
            skills = []
            common_skills = ["python", "javascript", "java", "c++", "sql", "aws", "docker", 
                            "kubernetes", "react", "angular", "vue", "node.js", "tensorflow", 
                            "pytorch", "machine learning", "deep learning", "nlp", "ai", 
                            "data science", "cloud", "git", "agile", "devops"]
            
            for skill in common_skills:
                if skill in skills_text:
                    skills.append(skill)
            
            # Extract experience requirement
            import re
            experience_pattern = r'(\d+)\+?\s*(?:years?|yrs?)'
            experience_match = re.search(experience_pattern, skills_text)
            required_experience = int(experience_match.group(1)) if experience_match else 0
            
            # Extract qualifications
            qualifications = []
            qual_keywords = ["bachelor", "master", "phd", "degree", "certification"]
            for line in skills_text.split('\n'):
                if any(keyword in line for keyword in qual_keywords):
                    qualifications.append(line.strip())
            
            # Check if job with this title already exists
            existing_job = db.query(JobDescription).filter(
                JobDescription.title == title
            ).first()
            
            if existing_job:
                logger.info(f"Job {title} already exists, skipping.")
                continue
            
            # Create new job description
            job = JobDescription(
                title=title,
                company=company,
                description=description,
                required_skills=json.dumps(skills),
                required_experience=required_experience,
                required_qualifications=json.dumps(qualifications)
            )
            
            db.add(job)
            logger.info(f"Added job: {title}")
        
        # Commit all changes
        db.commit()
        logger.info("Successfully imported job descriptions")
        return True
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error importing job descriptions: {str(e)}")
        return False

def import_resumes(resumes_dir, db):
    """
    Import resumes from a directory of PDF files.
    """
    logger.info(f"Importing resumes from {resumes_dir}")
    uploads_dir = ensure_uploads_dir()
    cv_parser = CVParser()
    
    try:
        # Get all PDF files in the directory
        pdf_files = list(Path(resumes_dir).glob("*.pdf"))
        if not pdf_files:
            logger.warning(f"No PDF files found in {resumes_dir}")
            return False
        
        logger.info(f"Found {len(pdf_files)} PDF files")
        
        # Process each resume
        for pdf_path in pdf_files:
            try:
                # Copy file to uploads directory
                dest_path = uploads_dir / pdf_path.name
                shutil.copy2(pdf_path, dest_path)
                
                logger.info(f"Processing resume: {pdf_path.name}")
                
                # Generate candidate name and email from filename
                filename_stem = pdf_path.stem  # e.g., "C1061"
                
                # Parse resume
                try:
                    resume_data = cv_parser.parse(str(dest_path))
                    name = resume_data.get('name', f"Candidate_{filename_stem}")
                    email = resume_data.get('email', f"{filename_stem.lower()}@example.com")
                    resume_text = resume_data.get('raw_text', '')
                    skills = resume_data.get('skills', [])
                    experience_years = resume_data.get('experience_years', 0)
                    qualifications = resume_data.get('qualifications', [])
                except Exception as parse_error:
                    logger.warning(f"Error parsing resume, using default values: {str(parse_error)}")
                    name = f"Candidate_{filename_stem}"
                    email = f"{filename_stem.lower()}@example.com"
                    resume_text = ""
                    skills = []
                    experience_years = 0
                    qualifications = []
                
                # Check if candidate already exists
                existing_candidate = db.query(Candidate).filter(Candidate.email == email).first()
                if existing_candidate:
                    logger.info(f"Candidate with email {email} already exists, skipping.")
                    continue
                
                # Create candidate record - removed resume_path field since it doesn't exist in the model
                candidate = Candidate(
                    name=name,
                    email=email,
                    resume_text=resume_text,
                    skills=json.dumps(skills),
                    experience_years=experience_years,
                    qualifications=json.dumps(qualifications)
                )
                
                db.add(candidate)
                logger.info(f"Added candidate: {name} ({email})")
                
            except Exception as e:
                logger.error(f"Error processing resume {pdf_path}: {str(e)}")
        
        # Commit all changes
        db.commit()
        logger.info("Successfully imported resumes")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error importing resumes: {str(e)}")
        return False

def main():
    """Main function to import dataset."""
    # Define paths to your dataset - Updated to actual location
    dataset_dir = Path("ai_job_screening/dataset")
    job_csv_path = dataset_dir / "job_description.csv"
    resumes_dir = dataset_dir / "resumes"
    
    if not job_csv_path.exists():
        logger.error(f"Job description CSV file not found: {job_csv_path}")
        return
    
    if not resumes_dir.exists() or not resumes_dir.is_dir():
        logger.error(f"Resumes directory not found: {resumes_dir}")
        return
    
    # Get database session
    db = next(get_db())
    
    try:
        # Import job descriptions
        job_import_success = import_job_descriptions(job_csv_path, db)
        
        # Import resumes
        resume_import_success = import_resumes(resumes_dir, db)
        
        if job_import_success:
            logger.info("Job descriptions imported successfully")
        else:
            logger.warning("There were issues importing job descriptions")
            
        if resume_import_success:
            logger.info("Resumes imported successfully")
        else:
            logger.warning("There were issues importing resumes")
            
    except Exception as e:
        logger.error(f"Error during import: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    main()

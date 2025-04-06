from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
import uvicorn
from pathlib import Path
import json
from datetime import datetime
import shutil
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from database.database import get_db
from database.models import JobDescription, Candidate, CandidateMatch
from agents.jd_summarizer import JobDescriptionSummarizer
from agents.cv_parser import CVParser
from agents.matching_engine import MatchingEngine
from agents.ai_matcher import AIMatchingEngine
from agents.interview_scheduler import InterviewScheduler

# Set up base directory
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
UPLOADS_DIR = BASE_DIR / "data" / "uploads"

# Create necessary directories
STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="AI Job Screening System")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Set up templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Initialize agents
jd_summarizer = JobDescriptionSummarizer()
cv_parser = CVParser()
matching_engine = MatchingEngine()
ai_matcher = AIMatchingEngine(model_name="llama2")
interview_scheduler = InterviewScheduler()

# Create necessary directories
os.makedirs('uploads', exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def root():
    try:
        template_path = TEMPLATES_DIR / "index.html"
        if not template_path.exists():
            raise HTTPException(status_code=404, detail="Template not found")
        with open(template_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        logger.error(f"Error serving template: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving template: {str(e)}")

@app.post("/job-descriptions/")
async def create_job_description(
    title: str = Form(...),
    company: str = Form(...),
    description: str = Form(...),
    db: Session = Depends(get_db)
) -> dict:
    logger.info(f"Received job description - Title: {title}, Company: {company}")
    logger.info(f"Description: {description}")
    # Extract and summarize job description
    try:
        # Parse skills from description
        skills_text = description.lower()
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
        experience_match = re.search(experience_pattern, description.lower())
        required_experience = int(experience_match.group(1)) if experience_match else 0
        
        # Extract qualifications
        qualifications = []
        qual_keywords = ["bachelor", "master", "phd", "degree", "certification"]
        for line in description.lower().split('\n'):
            if any(keyword in line for keyword in qual_keywords):
                qualifications.append(line.strip())
        
        # Create job description in database
        job = JobDescription(
            title=title,
            company=company,
            description=description,
            required_skills=json.dumps(skills),
            required_experience=required_experience,
            required_qualifications=json.dumps(qualifications)
        )
        
        db.add(job)
        db.commit()
        db.refresh(job)
        
        return {"message": "Job description created successfully", "job_id": job.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/candidates/")
async def upload_candidate(
    name: str = Form(...),
    email: str = Form(...),
    resume: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    logger = logging.getLogger(__name__)
    file_path = None
    try:
        # Log received data
        logger.info(f"Received candidate upload request - Name: {name}, Email: {email}, File: {resume.filename}")
        
        # Validate file extension
        if not resume.filename.lower().endswith(('.pdf', '.docx', '.txt')):
            raise HTTPException(
                status_code=400,
                detail="Invalid file format. Please upload a PDF, DOCX, or TXT file."
            )
        
        # Save resume file
        file_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{resume.filename}"
        file_path = UPLOADS_DIR / file_name
        
        content = await resume.read()
        if not content:
            return JSONResponse(status_code=400, content={"detail": "Empty file uploaded"})
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Parse CV
        try:
            logger.info("Parsing resume...")
            cv_data = cv_parser.parse(str(file_path))
            logger.info("Resume parsed successfully")
        except ValueError as e:
            logger.error(f"ValueError while parsing resume: {str(e)}")
            if file_path and file_path.exists():
                file_path.unlink()
            return JSONResponse(status_code=400, content={"detail": str(e)})
        except Exception as e:
            logger.error(f"Error while parsing resume: {str(e)}")
            if file_path and file_path.exists():
                file_path.unlink()
            return JSONResponse(status_code=400, content={"detail": f"Error parsing resume: {str(e)}"})
        
        # Check if candidate with email already exists
        try:
            existing_candidate = db.query(Candidate).filter(Candidate.email == email).first()
            if existing_candidate:
                logger.warning(f"Candidate with email {email} already exists")
                if file_path and file_path.exists():
                    file_path.unlink()
                return JSONResponse(
                    status_code=400,
                    content={
                        "detail": f"A candidate with email {email} already exists. Please use a different email address."
                    }
                )
            
            # Create new candidate
            logger.info("Creating candidate in database...")
            candidate = Candidate(
                name=name,
                email=email,
                resume_text=cv_data.get("raw_text", ""),
                skills=json.dumps(cv_data.get("skills", [])),
                experience_years=cv_data.get("experience", {}).get("years", 0),
                qualifications=json.dumps([])  # Add logic to extract qualifications
            )
            
            db.add(candidate)
            db.commit()
            db.refresh(candidate)
            
            logger.info(f"Candidate created successfully with ID: {candidate.id}")
            return JSONResponse(
                status_code=201,
                content={
                    "message": "Candidate created successfully",
                    "candidate_id": candidate.id
                }
            )
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            db.rollback()
            if file_path and file_path.exists():
                file_path.unlink()
            return JSONResponse(
                status_code=500,
                content={"detail": f"Error saving candidate: {str(e)}"}
            )
    except HTTPException as he:
        # Re-raise HTTP exceptions
        raise he
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        if file_path and file_path.exists():
            file_path.unlink()
        return JSONResponse(status_code=500, content={"detail": f"Error processing resume: {str(e)}"})

@app.post("/match/{job_id}/{candidate_id}")
async def match_candidate(
    job_id: int,
    candidate_id: int,
    db: Session = Depends(get_db)
):
    logger.info(f"Matching job {job_id} with candidate {candidate_id}")
    try:
        # Get job and candidate
        job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        
        if not job:
            logger.warning(f"Job {job_id} not found")
            return JSONResponse(
                status_code=404,
                content={"detail": f"Job with ID {job_id} not found"}
            )
            
        if not candidate:
            logger.warning(f"Candidate {candidate_id} not found")
            return JSONResponse(
                status_code=404,
                content={"detail": f"Candidate with ID {candidate_id} not found"}
            )
        
        # Parse job requirements
        try:
            job_dict = {
                "description": job.description,
                "required_skills": json.loads(job.required_skills) if job.required_skills else [],
                "required_experience": job.required_experience or 0,
                "required_qualifications": json.loads(job.required_qualifications) if job.required_qualifications else []
            }
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing job requirements: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid job requirements format"}
            )
        
        # Parse candidate data
        try:
            candidate_dict = {
                "resume_text": candidate.resume_text,
                "skills": json.loads(candidate.skills) if candidate.skills else [],
                "experience_years": candidate.experience_years or 0,
                "qualifications": json.loads(candidate.qualifications) if candidate.qualifications else []
            }
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing candidate data: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid candidate data format"}
            )
        
        # Get AI-powered match score first
        ai_score, ai_reasoning = await ai_matcher.analyze_match(job_dict, candidate_dict)
        
        # Generate interview questions for good matches
        interview_questions = await ai_matcher.get_interview_questions(
            job_dict, 
            candidate_dict, 
            ai_score
        )
        
        logger.info(f"AI match score: {ai_score}")
        logger.info(f"AI reasoning: {ai_reasoning}")
        logger.info(f"Generated {len(interview_questions)} interview questions")
        
        # Get traditional match score as backup
        matching_engine = MatchingEngine()
        match_score, detailed_scores = matching_engine.calculate_match(job_dict, candidate_dict)
        
        logger.info(f"Traditional match score: {match_score}")
        logger.info(f"Detailed scores: {detailed_scores}")
        
        # Use AI score if valid, otherwise fall back to traditional score
        final_score = ai_score if 0 <= ai_score <= 1 else match_score
        
        # Determine a message based on the score
        if final_score >= 0.8:
            message = "Excellent match! Strongly recommended for interview."
        elif final_score >= 0.6:
            message = "Good match. Consider for interview."
        else:
            message = "Below threshold. Not recommended."
        
        # Create a new match entry in database - only use fields that exist in the model
        match_entry = CandidateMatch(
            job_id=job_id,
            candidate_id=candidate_id,
            match_score=final_score,
            shortlisted=final_score >= 0.7
        )
        
        db.add(match_entry)
        db.commit()
        db.refresh(match_entry)
        
        # Return match results including details that aren't stored in the database
        return {
            "match_id": match_entry.id,
            "job_id": job_id,
            "candidate_id": candidate_id,
            "match_score": final_score,
            "detailed_scores": detailed_scores,
            "message": message,
            "ai_reasoning": ai_reasoning,
            "interview_questions": interview_questions
        }
        
    except Exception as e:
        logger.error(f"Error matching candidate: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error matching candidate: {str(e)}"}
        )

@app.post("/schedule-interview/{match_id}")
async def schedule_interview(
    match_id: int,
    interview_datetime: datetime,
    db: Session = Depends(get_db)
):
    # Get match details
    match = db.query(CandidateMatch).filter(CandidateMatch.id == match_id).first()
    
    if not match or not match.shortlisted:
        raise HTTPException(
            status_code=404, 
            detail="Match not found or candidate not shortlisted"
        )
    
    # Get job and candidate details
    job = db.query(JobDescription).filter(JobDescription.id == match.job_id).first()
    candidate = db.query(Candidate).filter(Candidate.id == match.candidate_id).first()
    
    # Schedule interview
    success = interview_scheduler.schedule_interview(
        {
            "id": candidate.id,
            "name": candidate.name,
            "contact": {"email": candidate.email}
        },
        {
            "id": job.id,
            "title": job.title,
            "company": job.company
        },
        interview_datetime
    )
    
    if success:
        # Update match record
        match.interview_scheduled = True
        match.interview_datetime = interview_datetime
        db.commit()
        
        return {"message": "Interview scheduled successfully"}
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to schedule interview"
        )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class JobDescription(Base):
    __tablename__ = "job_descriptions"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    required_skills = Column(Text, nullable=False)
    required_experience = Column(Integer)
    required_qualifications = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    candidates = relationship("CandidateMatch", back_populates="job")

class Candidate(Base):
    __tablename__ = "candidates"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    resume_text = Column(Text, nullable=False)
    skills = Column(Text)
    experience_years = Column(Integer)
    qualifications = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    matches = relationship("CandidateMatch", back_populates="candidate")

class CandidateMatch(Base):
    __tablename__ = "candidate_matches"
    
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("job_descriptions.id"))
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    match_score = Column(Float, nullable=False)
    shortlisted = Column(Boolean, default=False)
    interview_scheduled = Column(Boolean, default=False)
    interview_datetime = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    job = relationship("JobDescription", back_populates="candidates")
    candidate = relationship("Candidate", back_populates="matches")

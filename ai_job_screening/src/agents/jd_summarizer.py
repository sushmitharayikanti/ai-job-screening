import re
from typing import Dict, List

class JobDescriptionSummarizer:
    def __init__(self):
        # Common technical skills and keywords
        self.skill_patterns = [
            "python", "java", "javascript", "sql", "aws", "docker", "kubernetes",
            "machine learning", "ai", "data science", "agile", "scrum",
            "communication", "leadership", "problem solving"
        ]
        
    def extract_skills(self, text: str) -> List[str]:
        text = text.lower()
        skills = set()
        
        # Simple word matching for skills
        words = text.split()
        for word in words:
            if word in self.skill_patterns:
                skills.add(word)
                
        return list(skills)
    
    def extract_experience(self, text: str) -> int:
        # Look for patterns like "X years of experience"
        experience_patterns = [
            r"(\d+)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|exp)",
            r"minimum\s+of\s+(\d+)\s+years?",
            r"at\s+least\s+(\d+)\s+years?"
        ]
        
        text = text.lower()
        for pattern in experience_patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        return 0
    
    def extract_qualifications(self, text: str) -> List[str]:
        # Look for educational qualifications
        qualifications = set()
        text = text.lower()
        
        # Common qualification keywords
        edu_keywords = [
            "bachelor", "master", "phd", "doctorate",
            "bs", "ms", "ba", "ma", "mba"
        ]
        
        # Find degrees
        for keyword in edu_keywords:
            if keyword in text:
                # Try to find the complete degree mention
                pattern = f"{keyword}\\s*(?:'s)?(?:\\s+(?:degree|in)\\s+[\\w\\s]+)?"
                matches = re.finditer(pattern, text)
                for match in matches:
                    qual = match.group(0).strip()
                    if qual:
                        qualifications.add(qual)
        
        # Find certifications
        cert_pattern = r"certification\s+in\s+[\w\s]+"
        matches = re.finditer(cert_pattern, text)
        for match in matches:
            qualifications.add(match.group(0))
            
        return list(qualifications)
    
    def summarize(self, job_description: str) -> Dict:
        """Summarize a job description by extracting key information"""
        return {
            "skills": self.extract_skills(job_description),
            "experience": self.extract_experience(job_description),
            "qualifications": self.extract_qualifications(job_description)
        }

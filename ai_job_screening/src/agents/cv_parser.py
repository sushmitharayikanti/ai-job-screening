from typing import Dict
import PyPDF2
import docx
import re
from datetime import datetime

class CVParser:
    def __init__(self):
        # Technical skills and frameworks
        self.skill_keywords = {
            # Programming Languages
            "python": ["python", "django", "flask", "fastapi"],
            "javascript": ["javascript", "js", "node.js", "typescript"],
            "java": ["java", "spring", "hibernate"],
            "c++": ["c++", "cpp"],
            
            # Web Technologies
            "react": ["react", "reactjs", "react.js"],
            "angular": ["angular", "angularjs"],
            "vue": ["vue", "vuejs", "vue.js"],
            
            # Databases
            "sql": ["sql", "mysql", "postgresql", "oracle"],
            "mongodb": ["mongodb", "mongo", "nosql"],
            
            # Cloud & DevOps
            "aws": ["aws", "amazon web services", "ec2", "s3", "lambda"],
            "docker": ["docker", "container"],
            "kubernetes": ["kubernetes", "k8s"],
            
            # AI/ML
            "machine learning": ["machine learning", "ml", "deep learning", "dl"],
            "tensorflow": ["tensorflow", "tf"],
            "pytorch": ["pytorch", "torch"],
            "nlp": ["nlp", "natural language processing"],
            "computer vision": ["computer vision", "cv", "image processing"],
            
            # Big Data
            "spark": ["spark", "pyspark"],
            "hadoop": ["hadoop", "hdfs", "mapreduce"],
            "kafka": ["kafka", "event streaming"],
            
            # Other
            "git": ["git", "github", "gitlab"],
            "agile": ["agile", "scrum", "kanban"],
            "devops": ["devops", "ci/cd", "jenkins"]
        }
        
    def read_pdf(self, file_path: str) -> str:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text
    
    def read_docx(self, file_path: str) -> str:
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text += paragraph.text.strip() + "\n"
            return text
        except Exception as e:
            raise ValueError(f"Error reading Word document: {str(e)}")
    
    def extract_contact_info(self, text: str) -> Dict:
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email = re.search(email_pattern, text)
        
        # Extract phone
        phone_pattern = r'\b\+?[\d\s-]{10,}\b'
        phone = re.search(phone_pattern, text)
        
        return {
            "email": email.group(0) if email else None,
            "phone": phone.group(0) if phone else None
        }
    
    def extract_experience(self, text: str) -> Dict:
        # Extract work experience using date patterns
        experience = []
        date_pattern = r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}'
        
        # Find all dates in the text
        dates = re.finditer(date_pattern, text, re.IGNORECASE)
        for date in dates:
            # Get surrounding context (100 characters before and after)
            start = max(0, date.start() - 100)
            end = min(len(text), date.end() + 100)
            context = text[start:end]
            experience.append(context.strip())
        
        return {
            "timeline": experience,
            "years": self._calculate_total_years(text)
        }
    
    def _calculate_total_years(self, text: str) -> int:
        # Extract years of experience from text
        experience_patterns = [
            # Direct year mentions (e.g., "5 years experience")
            r"(\d+)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|exp)",
            # Date ranges (e.g., "2020 - Present")
            r"(?:since|from)\s+(\d{4})",
            # Job duration (e.g., "2018 - 2020")
            r"(\d{4})\s*(?:-|to|–)\s*(?:present|current|\d{4})"
        ]
        
        total_years = 0
        current_year = datetime.now().year
        
        # First look for explicit mentions
        for pattern in experience_patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                try:
                    year = int(match.group(1))
                    if year > 1900:  # Assuming it's a year
                        years = current_year - year
                    else:  # Assuming it's number of years
                        years = year
                    total_years = max(total_years, years)
                except ValueError:
                    continue
        
        # If no explicit mentions found, try to calculate from job history
        if total_years == 0:
            # Look for date ranges in experience section
            date_ranges = re.finditer(r"(\d{4})\s*(?:-|to|–)\s*(\d{4}|present|current)", text.lower())
            for date_range in date_ranges:
                start_year = int(date_range.group(1))
                end_str = date_range.group(2)
                
                if end_str in ["present", "current"]:
                    end_year = current_year
                else:
                    end_year = int(end_str)
                
                total_years += end_year - start_year
                    
        return total_years
    
    def extract_skills(self, text: str) -> list:
        """Extract skills from text using keyword matching"""
        skills = set()
        text_lower = text.lower()
        
        # Look for skill keywords and their variations
        for main_skill, variations in self.skill_keywords.items():
            if any(variation in text_lower for variation in variations):
                skills.add(main_skill)
        
        return list(skills)
    
    def read_txt(self, file_path: str) -> str:
        """Read content from a text file"""
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()

    def parse(self, file_path: str) -> Dict:
        """Parse a CV file and extract relevant information"""
        # Read file based on extension
        if file_path.endswith('.pdf'):
            text = self.read_pdf(file_path)
        elif file_path.endswith('.docx'):
            text = self.read_docx(file_path)
        elif file_path.endswith('.txt'):
            text = self.read_txt(file_path)
        else:
            raise ValueError("Unsupported file format. Please upload a PDF, DOCX, or TXT file.")
        
        # Extract information
        contact_info = self.extract_contact_info(text)
        experience = self.extract_experience(text)
        skills = self.extract_skills(text)
        
        return {
            "contact": contact_info,
            "experience": experience,
            "skills": skills,
            "raw_text": text
        }

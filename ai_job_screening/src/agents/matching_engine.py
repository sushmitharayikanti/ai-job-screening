from typing import Dict, List, Tuple
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MatchingEngine:
    def __init__(self):
        # Initialize skill variations dictionary for better matching
        self.skill_variations = {
            'python': ['py', 'python3'],
            'javascript': ['js', 'ecmascript', 'node.js', 'nodejs'],
            'java': ['java programming', 'core java', 'java ee'],
            'c++': ['cpp', 'c plus plus'],
            'react': ['reactjs', 'react.js'],
            'angular': ['angularjs', 'angular.js'],
            'vue': ['vuejs', 'vue.js'],
            'aws': ['amazon web services', 'amazon aws'],
            'docker': ['containerization'],
            'kubernetes': ['k8s'],
            'machine learning': ['ml', 'machine-learning'],
            'artificial intelligence': ['ai'],
            'natural language processing': ['nlp'],
            'tensorflow': ['tf'],
            'pytorch': ['torch'],
            'sql': ['mysql', 'postgresql', 'oracle', 'tsql', 'sql server'],
            'mongodb': ['mongo', 'nosql'],
            'bigdata': ['big data', 'hadoop', 'spark'],
            'devops': ['ci/cd', 'continuous integration'],
            'git': ['github', 'gitlab', 'version control'],
            'data science': ['data analysis', 'data analytics', 'analytics'],
            'web development': ['web dev', 'frontend', 'backend', 'fullstack'],
            'api': ['rest api', 'graphql', 'web services']
        }

    def calculate_skill_match(self, required_skills: List[str], candidate_skills: List[str]) -> float:
        if not required_skills or not candidate_skills:
            return 0.0
            
        # Convert skills to lowercase for comparison
        required_skills = [skill.lower() for skill in required_skills]
        candidate_skills = [skill.lower() for skill in candidate_skills]
        
        # Group skills into categories
        categories = {
            'programming': ['python', 'java', 'javascript', 'c++'],
            'web': ['react', 'angular', 'vue'],
            'database': ['sql', 'mongodb'],
            'cloud': ['aws', 'docker', 'kubernetes'],
            'ai_ml': ['machine learning', 'tensorflow', 'pytorch', 'nlp', 'computer vision'],
            'big_data': ['spark', 'hadoop', 'kafka'],
            'other': ['git', 'agile', 'devops']
        }
        
        # Calculate category scores
        category_scores = {}
        for category, skills in categories.items():
            req_skills_in_category = [s for s in required_skills if s in skills]
            if not req_skills_in_category:
                continue
                
            cand_skills_in_category = [s for s in candidate_skills if s in skills]
            matches = set(req_skills_in_category) & set(cand_skills_in_category)
            
            if req_skills_in_category:
                category_scores[category] = len(matches) / len(req_skills_in_category)
        
        if not category_scores:
            return 0.0
            
        # Calculate weighted average across categories
        weights = {
            'programming': 0.25,
            'web': 0.15,
            'database': 0.15,
            'cloud': 0.15,
            'ai_ml': 0.25,
            'big_data': 0.15,
            'other': 0.1
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for category, score in category_scores.items():
            weight = weights.get(category, 0.1)
            total_score += score * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def calculate_experience_match(self, required_years: int, candidate_years: int) -> float:
        if required_years <= 0:
            return 1.0
            
        # Calculate base score
        if candidate_years >= required_years:
            base_score = 1.0
        else:
            base_score = candidate_years / required_years
        
        # Add bonus for exceeding requirements (up to 20% bonus)
        if candidate_years > required_years:
            excess_years = candidate_years - required_years
            bonus = min(0.2, excess_years * 0.05)  # 5% per extra year, max 20%
            base_score = min(1.0, base_score + bonus)
        
        return base_score
    
    def calculate_qualification_match(self, required_qualifications: List[str], 
                                   candidate_qualifications: List[str]) -> float:
        if not required_qualifications:
            return 1.0
            
        # Convert to lowercase for comparison
        required_quals = [q.lower() for q in required_qualifications]
        candidate_quals = [q.lower() for q in candidate_qualifications]
        
        # Calculate matching qualifications
        matching_quals = set(required_quals) & set(candidate_quals)
        
        return len(matching_quals) / len(required_qualifications)
    
    def calculate_keyword_match(self, job_description: str, cv_text: str) -> float:
        """Simple keyword matching between job description and CV"""
        if not job_description or not cv_text:
            return 0.0
            
        # Convert to lowercase for comparison
        job_words = set(job_description.lower().split())
        cv_words = set(cv_text.lower().split())
        
        # Calculate matching words
        matching_words = job_words & cv_words
        
        # Return score based on percentage of job keywords found in CV
        return len(matching_words) / len(job_words) if job_words else 0.0
    
    def calculate_match_score(self, job: Dict, candidate: Dict) -> Tuple[float, Dict]:
        """Calculate match score between job and candidate"""
        # Calculate individual scores
        skill_score = self.calculate_skill_match(
            job.get("required_skills", []),
            candidate.get("skills", [])
        )
        
        experience_score = self.calculate_experience_match(
            job.get("required_experience", 0),
            candidate.get("experience", {}).get("years", 0)
        )
        
        qualification_score = self.calculate_qualification_match(
            job.get("required_qualifications", []),
            candidate.get("qualifications", [])
        )
        
        keyword_score = self.calculate_keyword_match(
            job.get("description", ""),
            candidate.get("raw_text", "")
        )
        
        # Calculate weighted average with dynamic weights
        base_weights = {
            "skills": 0.4,       # Increased weight for skills
            "experience": 0.3,   # Slightly reduced but still important
            "qualifications": 0.2,
            "keywords": 0.1
        }
        
        # Adjust weights based on job requirements
        if "senior" in job.get("description", "").lower():
            base_weights["experience"] += 0.1
            base_weights["skills"] -= 0.1
        elif "junior" in job.get("description", "").lower():
            base_weights["experience"] -= 0.1
            base_weights["skills"] += 0.1
        
        # Normalize weights
        total_weight = sum(base_weights.values())
        weights = {k: v/total_weight for k, v in base_weights.items()}
        
        # Calculate overall score
        overall_score = (
            skill_score * weights["skills"] +
            experience_score * weights["experience"] +
            qualification_score * weights["qualifications"] +
            keyword_score * weights["keywords"]
        )
        
        # Apply bonus for exceptional matches
        if skill_score > 0.8 and experience_score > 0.8 and qualification_score > 0.8:
            bonus = 0.1  # 10% bonus for exceptional candidates
            overall_score = min(1.0, overall_score * (1 + bonus))
        
        # Determine shortlisting
        shortlisted = (
            overall_score >= 0.7 and   # Good overall match
            skill_score >= 0.6 and     # Must have most required skills
            experience_score >= 0.8     # Must meet experience requirements
        )
        
        detailed_scores = {
            "overall": overall_score,
            "skills": skill_score,
            "experience": experience_score,
            "qualifications": qualification_score,
            "keywords": keyword_score,
            "shortlisted": shortlisted
        }
        
        return overall_score, detailed_scores
    
    def calculate_match(self, job: Dict, candidate: Dict) -> Tuple[float, Dict]:
        """Calculate match score between job and candidate"""
        try:
            # Process skills with better error handling
            try:
                required_skills = json.loads(job.get('required_skills', '[]'))
            except json.JSONDecodeError:
                required_skills = [s.strip() for s in job.get('required_skills', '').split(',')]

            try:
                candidate_skills = json.loads(candidate.get('skills', '[]'))
            except json.JSONDecodeError:
                candidate_skills = [s.strip() for s in candidate.get('skills', '').split(',')]

            # Normalize skills
            req_skills_norm = self.normalize_skills(required_skills)
            cand_skills_norm = self.normalize_skills(candidate_skills)

            # Calculate skill match with variations
            matching_skills = req_skills_norm & cand_skills_norm
            skill_score = len(matching_skills) / len(req_skills_norm) if req_skills_norm else 0

            # Calculate experience match with bonus for extra experience
            required_exp = float(job.get('required_experience', 0))
            candidate_exp = float(candidate.get('experience_years', 0))
            if required_exp > 0:
                exp_score = min(1.2, candidate_exp / required_exp)  # Allow 20% bonus
            else:
                exp_score = 1.0 if candidate_exp > 0 else 0.0

            # Calculate qualification match
            try:
                required_quals = json.loads(job.get('required_qualifications', '[]'))
            except json.JSONDecodeError:
                required_quals = [q.strip() for q in job.get('required_qualifications', '').split(',')]

            try:
                candidate_quals = json.loads(candidate.get('qualifications', '[]'))
            except json.JSONDecodeError:
                candidate_quals = [q.strip() for q in candidate.get('qualifications', '').split(',')]

            # Normalize and match qualifications
            req_quals_norm = {q.lower().strip() for q in required_quals}
            cand_quals_norm = {q.lower().strip() for q in candidate_quals}
            matching_quals = req_quals_norm & cand_quals_norm
            qual_score = len(matching_quals) / len(req_quals_norm) if req_quals_norm else 1

            # Calculate keyword match
            resume_text = candidate.get('resume_text', '').lower()
            job_desc = job.get('description', '').lower()
            
            # Extract keywords from job description
            keywords = self.extract_keywords(job_desc)
            found_keywords = sum(1 for k in keywords if k in resume_text)
            keyword_score = found_keywords / len(keywords) if keywords else 0

            # Calculate final score with weights
            final_score = (skill_score * 0.5) + (exp_score * 0.3) + (qual_score * 0.1) + (keyword_score * 0.1)

            # Add small bonus for exceeding minimum requirements
            if skill_score > 0.8 and exp_score > 1.0 and qual_score > 0.8:
                final_score = min(1.0, final_score * 1.1)  # 10% bonus capped at 1.0
                
            # Determine if shortlisted
            shortlisted = final_score >= 0.7
                
            # Create detailed scores dictionary
            detailed_scores = {
                "overall": round(final_score, 2),
                "skills": round(skill_score, 2),
                "experience": round(exp_score, 2),
                "qualifications": round(qual_score, 2),
                "keywords": round(keyword_score, 2),
                "shortlisted": shortlisted,
                "matching_skills": list(matching_skills)
            }

            return final_score, detailed_scores
            
        except Exception as e:
            logger.error(f"Error calculating match: {str(e)}")
            # Return a fallback score and empty details
            return 0.5, {"error": str(e)}

    def normalize_skills(self, skills: List[str]) -> set:
        """Normalize skills for better matching across variations"""
        normalized = set()
        
        for skill in skills:
            skill = skill.lower().strip()
            normalized.add(skill)
            
            # Add common variations
            if skill in self.skill_variations:
                for variation in self.skill_variations[skill]:
                    normalized.add(variation)
                    
        return normalized
        
    def extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        # Define common technical keywords
        tech_keywords = [
            'algorithm', 'analytics', 'api', 'architecture', 'automation',
            'cloud', 'database', 'deploy', 'design', 'development',
            'devops', 'distributed', 'framework', 'infrastructure', 'integration',
            'machine learning', 'microservices', 'optimization', 'pipeline', 'platform',
            'programming', 'scalable', 'security', 'software', 'system',
            'testing', 'tool', 'web', 'agile', 'data'
        ]
        
        # Find all keywords in the text
        found_keywords = []
        for keyword in tech_keywords:
            if keyword in text:
                found_keywords.append(keyword)
                
        # If we found very few keywords, try some basic word extraction
        if len(found_keywords) < 5:
            words = [w.strip().lower() for w in text.split() if len(w) > 5]
            words = [w for w in words if not w in ['their', 'there', 'these', 'those', 'about', 'would', 'should']]
            found_keywords.extend(words[:10])  # Add up to 10 additional words
            
        return list(set(found_keywords))  # Remove duplicates

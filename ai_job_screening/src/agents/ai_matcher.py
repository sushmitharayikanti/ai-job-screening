import ollama
import json
from typing import Dict, List, Tuple
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIMatchingEngine:
    def __init__(self, model_name="llama2"):
        self.model_name = model_name
        
    async def analyze_match(self, job: Dict, candidate: Dict) -> Tuple[float, str]:
        """
        Use Ollama to analyze the match between a job and candidate
        Returns a tuple of (score, reasoning)
        """
        try:
            # Process skills and qualifications
            job_skills = job.get('required_skills', [])
            if isinstance(job_skills, str):
                try:
                    job_skills = json.loads(job_skills)
                except json.JSONDecodeError:
                    job_skills = [s.strip() for s in job_skills.split(',')]
                    
            job_quals = job.get('required_qualifications', [])
            if isinstance(job_quals, str):
                try:
                    job_quals = json.loads(job_quals)
                except json.JSONDecodeError:
                    job_quals = [q.strip() for q in job_quals.split(',')]
                    
            candidate_skills = candidate.get('skills', [])
            if isinstance(candidate_skills, str):
                try:
                    candidate_skills = json.loads(candidate_skills)
                except json.JSONDecodeError:
                    candidate_skills = [s.strip() for s in candidate_skills.split(',')]
                
            # Prepare the prompt
            # Log input data
            logger.info(f"Job Skills: {job_skills}")
            logger.info(f"Candidate Skills: {candidate_skills}")
            
            # Calculate preliminary score based on skill matching
            # This helps provide a more accurate score even if AI analysis fails
            matching_skills = set([s.lower() for s in job_skills]) & set([s.lower() for s in candidate_skills])
            skill_match_score = len(matching_skills) / len(job_skills) if job_skills else 0.0
            logger.info(f"Preliminary skill match score: {skill_match_score}")
            
            # Extract job experience requirement and candidate experience
            job_exp = job.get('required_experience', 0)
            candidate_exp = candidate.get('experience_years', 0)
            
            # Calculate experience match
            exp_match_score = min(1.0, candidate_exp / job_exp) if job_exp > 0 else 0.5
            logger.info(f"Experience match score: {exp_match_score}")
            
            prompt = f"""
            You are an expert AI recruiter. Your task is to evaluate if this candidate is a good match for the job.
            Focus especially on technical skills and experience in machine learning and AI.
            
            JOB POSTING:
            Title: {job.get('title', '')}
            Company: {job.get('company', '')}
            Key Requirements:
            1. Technical Skills Required: {', '.join(job_skills)}
            2. Years of Experience Needed: {job.get('required_experience', 0)}
            3. Required Qualifications: {', '.join(job_quals)}
            4. Full Description: {job.get('description', '')}
            
            CANDIDATE:
            Name: {candidate.get('name', '')}
            Technical Skills: {', '.join(candidate_skills)}
            Years of Experience: {candidate.get('experience_years', 0)}
            Full Resume:
            {candidate.get('resume_text', '')}
            
            EVALUATION INSTRUCTIONS:
            1. Score each category:
               a) SKILLS (40 points):
                  - Award points for each matching technical skill
                  - Extra points for ML/AI framework expertise
                  - Bonus for additional relevant skills
               
               b) EXPERIENCE (30 points):
                  - Points for years of experience
                  - Extra points for ML/AI specific experience
                  - Bonus for leadership roles
               
               c) QUALIFICATIONS (20 points):
                  - Points for matching education level
                  - Extra points for relevant certifications
                  - Bonus for advanced degrees in ML/AI
               
               d) ACHIEVEMENTS (10 points):
                  - Points for relevant projects
                  - Extra points for quantified improvements
                  - Bonus for innovations/patents
            
            2. Calculate final score:
               - Add up all points and divide by 100
               - This gives a score between 0.0 and 1.0
               - Round to 2 decimal places
            
            YOUR RESPONSE MUST BE IN THIS EXACT FORMAT:
            SCORE: [number between 0.0 and 1.0]
            REASONING: [detailed point breakdown and explanation]
            """
            
            # Get response from Ollama
            system_msg = """You are an expert AI recruitment system specialized in technical roles.
            Your task is to accurately evaluate candidates for technical positions.
            You must be thorough in your analysis and provide scores based on concrete evidence.
            Always format your response with SCORE: and REASONING: on separate lines."""
            
            logger.info("Sending request to Ollama...")
            try:
                response = await ollama.chat(
                    model=self.model_name,
                    messages=[{
                        "role": "system",
                        "content": system_msg
                    }, {
                        "role": "user",
                        "content": prompt
                    }]
                )
                
                # Parse the response
                response_text = response['message']['content']
                logger.info("Received response from Ollama")
                logger.info(f"Raw AI response:\n{response_text}")
                
                # Extract score and reasoning with better error handling
                try:
                    # First try to find exact SCORE: and REASONING: lines
                    lines = [line.strip() for line in response_text.split('\n') if line.strip()]
                    
                    # Log all lines for debugging
                    logger.info("Response lines:")
                    for line in lines:
                        logger.info(f"Line: {line}")
                    
                    score_line = next(line for line in lines if line.startswith('SCORE:'))
                    reasoning_line = next(line for line in lines if line.startswith('REASONING:'))
                    
                    score = float(score_line.split(':')[1].strip())
                    reasoning = reasoning_line.split(':')[1].strip()
                    
                    logger.info(f"Extracted score: {score}")
                    logger.info(f"Extracted reasoning: {reasoning}")
                    
                except Exception as e:
                    logger.error(f"Error parsing AI response: {str(e)}")
                    logger.error(f"Full response text: {response_text}")
                    
                    # More aggressive fallback parsing
                    try:
                        # Try to find any number in the response
                        import re
                        numbers = re.findall(r'\d+\.\d+', response_text)
                        if numbers:
                            score = float(numbers[0])  # Take the first number found
                        else:
                            # Use our preliminary score calculation instead of a static default
                            combined_score = (skill_match_score * 0.6) + (exp_match_score * 0.4)
                            score = round(combined_score, 2)
                            logger.info(f"Using calculated fallback score: {score}")
                        
                        # Use everything else as reasoning
                        reasoning = f"Score calculated based on skill match ({skill_match_score:.2f}) and experience match ({exp_match_score:.2f}). AI analysis failed to provide detailed scoring."
                    except:
                        # If all else fails, use our preliminary score calculation
                        combined_score = (skill_match_score * 0.6) + (exp_match_score * 0.4)
                        score = round(combined_score, 2)
                        logger.info(f"Using calculated fallback score: {score}")
                        reasoning = f"Score calculated based on skill match ({skill_match_score:.2f}) and experience match ({exp_match_score:.2f}). AI analysis failed to provide detailed scoring."
                
            except Exception as e:
                logger.error(f"Error calling Ollama: {str(e)}")
                # If Ollama call fails, use our preliminary calculation
                combined_score = (skill_match_score * 0.6) + (exp_match_score * 0.4)
                score = round(combined_score, 2)
                logger.info(f"Using calculated fallback score (Ollama unavailable): {score}")
                reasoning = f"Score calculated based on skill match ({skill_match_score:.2f}) and experience match ({exp_match_score:.2f}). AI service unavailable for detailed analysis."
                
            return score, reasoning
            
        except Exception as e:
            logger.error(f"Error in AI matching: {str(e)}")
            return 0.5, f"Error in AI analysis: {str(e)}"
    
    async def get_interview_questions(self, job: Dict, candidate: Dict, match_score: float) -> List[str]:
        """
        Generate personalized interview questions based on the job and candidate profile.
        Only generates detailed questions for candidates with good match scores.
        
        Args:
            job: Dictionary containing job details
            candidate: Dictionary containing candidate details
            match_score: The calculated match score (0.0 to 1.0)
            
        Returns:
            List of interview questions
        """
        logger = logging.getLogger(__name__)
        logger.info(f"Generating interview questions for match score: {match_score}")
        
        # Only generate detailed questions for good matches
        if match_score < 0.6:
            return ["No interview questions generated for low match scores."]
            
        job_skills = job.get('required_skills', [])
        if isinstance(job_skills, str):
            try:
                job_skills = json.loads(job_skills)
            except json.JSONDecodeError:
                job_skills = [s.strip() for s in job_skills.split(',')]
                
        candidate_skills = candidate.get('skills', [])
        if isinstance(candidate_skills, str):
            try:
                candidate_skills = json.loads(candidate_skills)
            except json.JSONDecodeError:
                candidate_skills = [s.strip() for s in candidate_skills.split(',')]
        
        # Find skill gaps for targeted questions
        if job_skills and candidate_skills:
            job_skills_lower = [s.lower() for s in job_skills]
            candidate_skills_lower = [s.lower() for s in candidate_skills]
            missing_skills = [s for s in job_skills_lower if s not in candidate_skills_lower]
        else:
            missing_skills = []
        
        prompt = f"""
        You are an expert technical interviewer for a {job.get('title', 'technical')} position.
        
        JOB DETAILS:
        Title: {job.get('title', '')}
        Description: {job.get('description', '')}
        Required Skills: {', '.join(job_skills)}
        
        CANDIDATE PROFILE:
        Experience: {candidate.get('experience_years', 0)} years
        Skills: {', '.join(candidate_skills)}
        
        MATCH ANALYSIS:
        Overall Match Score: {match_score:.2f} (scale of 0.0 to 1.0)
        Potential skill gaps: {', '.join(missing_skills) if missing_skills else 'None identified'}
        
        TASK:
        Generate 5 thoughtful technical interview questions that:
        1. Evaluate the candidate's proficiency in their claimed skills
        2. Assess their problem-solving abilities relevant to the job
        3. Address any potential skill gaps identified
        4. Allow them to demonstrate depth of knowledge in key areas
        5. Include at least one scenario-based question relevant to the job role
        
        FORMAT YOUR RESPONSE AS A SIMPLE LIST OF QUESTIONS ONLY, ONE PER LINE.
        DO NOT include any explanations, bullet points, numbers or other text.
        """
        
        # Get response from Ollama
        system_msg = """You are an expert technical interviewer who creates insightful, job-specific interview questions.
        Keep your questions clear, concise and directly relevant to the job requirements.
        Format your response as a simple list of questions, one per line, with no additional text."""
        
        try:
            response = await ollama.chat(
                model=self.model_name,
                messages=[{
                    "role": "system",
                    "content": system_msg
                }, {
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Parse the response
            response_text = response['message']['content']
            logger.info("Received interview questions from Ollama")
            
            # Clean and extract questions
            questions = [line.strip() for line in response_text.split('\n') if line.strip()]
            
            # Filter out any non-question lines
            questions = [q for q in questions if q and (q.endswith('?') or 'describe' in q.lower() or 'explain' in q.lower())]
            
            # Limit to 5 questions maximum
            questions = questions[:5]
            
            if not questions:
                questions = ["How would you apply your experience to this role?",
                           "What challenges have you faced in similar positions?",
                           "How do you stay updated with developments in this field?"]
            
            logger.info(f"Generated {len(questions)} interview questions")
            return questions
            
        except Exception as e:
            logger.error(f"Error generating interview questions: {str(e)}")
            return [
                "Describe your most challenging project and how you overcame obstacles.",
                "How do you stay updated with the latest developments in your field?",
                "Explain your approach to problem-solving in a technical environment."
            ]

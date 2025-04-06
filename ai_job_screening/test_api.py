import requests
import json

def test_job_creation():
    url = "http://localhost:8000/job-descriptions/"
    data = {
        "title": "Senior Software Engineer",
        "company": "Tech Innovations Inc",
        "description": """We are seeking a Senior Software Engineer with 5+ years of experience in Python development. 
        The ideal candidate should have:
        - Strong experience with Python, JavaScript, and SQL
        - Experience with AWS and Docker
        - Bachelor's degree in Computer Science or related field
        - Strong problem-solving and communication skills
        - Experience with agile development methodologies"""
    }
    
    response = requests.post(url, json=data)
    print("Job Creation Response:", response.json())
    return response.json()["job_id"]

def test_candidate_upload():
    url = "http://localhost:8000/candidates/"
    files = {
        "resume": ("sample_resume.docx", open("data/sample_resume.docx", "rb"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    }
    data = {
        "name": "John Smith",
        "email": "john.smith@email.com"
    }
    
    response = requests.post(url, files=files, data=data)
    print("Candidate Upload Response:", response.json())
    return response.json()["candidate_id"]

def test_match(job_id, candidate_id):
    url = f"http://localhost:8000/match/{job_id}/{candidate_id}"
    response = requests.post(url)
    print("Match Response:", response.json())

if __name__ == "__main__":
    job_id = test_job_creation()
    candidate_id = test_candidate_upload()
    test_match(job_id, candidate_id)

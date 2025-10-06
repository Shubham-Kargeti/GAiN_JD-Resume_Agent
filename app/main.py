from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from utils import extract_text
import os
from typing import Dict, Optional
from openai import OpenAI

app = FastAPI(title="Resume Validator")

memory_store: Dict[str, Optional[bytes]] = {}

ALLOWED_EXTENSIONS = {".pdf", ".docx"}

def allowed_file(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS

@app.post("/upload-jd/")
async def upload_jd(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file sent")
    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Only .docx and .pdf files are allowed")

    memory_store["jd"] = await file.read()
    return {"info": f"Uploaded Job Description '{file.filename}' successfully."}

@app.post("/upload-resume/")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file sent")
    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Only .docx and .pdf files are allowed")

    memory_store["resume"] = await file.read()
    return {"info": f"Uploaded Resume '{file.filename}' successfully."}

@app.get("/process")
async def process():
    if "resume" not in memory_store or "jd" not in memory_store:
        return JSONResponse(status_code=400, content={"error": "Both resume and job description files must be uploaded first."})

    # Provide fake filenames/extensions to preserve compatibility
    resume_text = extract_text(memory_store["resume"], "resume.pdf")
    jd_text = extract_text(memory_store["jd"], "jd.pdf")

    
    client = OpenAI(
        # api_key=os.environ.get("OPENAI_API_KEY"),
        api_key="",
        base_url="https://api.groq.com/openai/v1",
    )
    
    user_input = f"""
    You are an experienced recruiter, career strategist, and resume analyst.
    Your task is to evaluate how well a given resume aligns with a specific job description. Assess the compatibility based on key factors such as skills, experience, education, and keywords relevant to the job role.
    Given the job description and the resume text, provide the following:
    Compatibility Score: Rate the overall match on a scale of 1 to 10, where 10 = excellent match and 1 = poor match.
    Summary Evaluation (2-3 sentences): Briefly explain the reasoning behind the score, highlighting key strengths or gaps.
    Key Matches: List up to 5 major points where the resume strongly aligns with the job description (skills, experiences, certifications, etc.).
    Key Gaps: List up to 5 notable areas where the resume lacks alignment with the job description.
    Recommendation: Suggest 1-2 ways the candidate could improve the resume to better match this job.

    --- Job Description ---
    {jd_text}

    --- Resume ---
    {resume_text}

    Respond in the following format:

    Score: X/10  
    Explanation: <your explanation here>
    """

    response = client.responses.create(
        input=user_input,
        model="openai/gpt-oss-20b",
    )
    return {"combined_text": response.output_text}


    # # combined = jd_text + "\n\n--- Combined With ---\n\n" + resume_text
    # # return {"combined_text": combined}
    # return {"combined_text": "hello hello"}

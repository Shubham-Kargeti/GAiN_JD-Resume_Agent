from fastapi import APIRouter, HTTPException
from app.utils.text_extract import extract_text
from app.config import memory_store
from openai import OpenAI

router = APIRouter()

@router.get("/process/")
async def process():
    if "resume" not in memory_store or "jd" not in memory_store:
        raise HTTPException(status_code=400, detail="Both resume and job description files must be uploaded first.")

    resume_info = memory_store["resume"]
    jd_info = memory_store["jd"]

    resume_text = extract_text(resume_info["bytes"], resume_info["filename"])
    jd_text = extract_text(jd_info["bytes"], jd_info["filename"])

    client = OpenAI(base_url="https://api.groq.com/openai/v1")

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

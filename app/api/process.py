from fastapi import APIRouter, HTTPException, Request, Depends
from app.utils.text_extract import extract_text
from app.config import memory_store
from openai import OpenAI

router = APIRouter()

# Dependency injection function
def get_question_suggester(request: Request):
    return request.app.state.question_suggester

@router.get("/process/")
async def process(suggester=Depends(get_question_suggester)):
    if "resume" not in memory_store or "jd" not in memory_store:
        raise HTTPException(status_code=400, detail="Both resume and job description files must be uploaded first.")

    resume_info = memory_store["resume"]
    jd_info = memory_store["jd"]

    resume_text = extract_text(resume_info["bytes"], resume_info["filename"])
    jd_text = extract_text(jd_info["bytes"], jd_info["filename"])

    combined_text = resume_text + " " + jd_text   

    client = OpenAI(base_url="https://api.groq.com/openai/v1")

    # Main evaluation prompt
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

    # Shrink combined text for semantic matching prompt
    user_input_2 = f"""
    You are an experienced recruiter, career strategist, and resume analyst.
    Your job is to shrink down given combined text from JD and resume into very precise and consise text focusing on technology names, skills required, possible question topics.
    This result will be used in Semantic matching with Interview questions.
    Return just the final text.

    combined_text:
    {jd_text}
    """

    response_2 = client.responses.create(
        input=user_input_2,
        model="openai/gpt-oss-20b",
    )

    suggested_questions = suggester.suggest_questions(response_2.output_text, top_k=15)

    # New detailed language and client name check prompt (resume only)
    grammar_check_prompt = f"""
    You are an expert proofreader and recruiter.

    Your task is to analyze the given resume text and:

    1. Identify any grammatical errors or awkward phrasing.
    2. Detect spelling mistakes and offer corrections.
    3. Look for any mention of client or organization names that an employee should avoid disclosing publicly or in resumes, and list them.

    Return your response as a structured report with these sections:

    Grammatical Errors:
    - List each error with context and suggested correction.

    Spelling Mistakes:
    - List each mistake with suggested correct spelling.

    Client Names:
    - List any detected client names that should be removed.

    Only analyze the following resume text (do NOT analyze job description text):

    Resume Text:
    {resume_text}

    Please provide a clear, concise report.
    """

    grammar_check_response = client.responses.create(
        input=grammar_check_prompt,
        model="openai/gpt-oss-20b",
    )

    detailed_report = grammar_check_response.output_text

    return {
        "combined_text": response.output_text,
        "Questions": suggested_questions,
        "detailed_report": detailed_report
    }

#1) JD_MatchScore
#2) Score_Explaination
#3) Key_Matches
#4) KeyGaps
#5) Recommendations
#6) Suggested_Interview_Question
#7) Gramatical_Errors

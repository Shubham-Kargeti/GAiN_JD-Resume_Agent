from fastapi import APIRouter, HTTPException, Request, Depends
from app.utils.text_extract import extract_text
from app.config import memory_store
from app.schemas.schemas import ResumeAnalysisResponse
import json
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from langchain.schema.runnable import RunnableMap
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq

router = APIRouter()

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

    llm = ChatGroq(model="openai/gpt-oss-20b")
    pydantic_parser = PydanticOutputParser(pydantic_object=ResumeAnalysisResponse)
    fixing_parser = OutputFixingParser.from_llm(parser=pydantic_parser, llm=llm)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert recruiter, resume strategist, and proofreader."),
        ("user", """You will return JSON matching this schema:
        {format_instructions}

        Then, analyze:
        --- JOB DESCRIPTION ---
        {jd_text}
        --- RESUME ---
        {resume_text}
        """)
         ])

    format_instructions = fixing_parser.get_format_instructions()

    prompt_with_instructions = prompt.partial(format_instructions=format_instructions)

    chain = (
        RunnableMap({
            "jd_text": lambda x: x["jd_text"],
            "resume_text": lambda x: x["resume_text"],
        })
        | prompt_with_instructions
        | llm
        | fixing_parser
    )

    resp: ResumeAnalysisResponse = chain.invoke({
        "jd_text": jd_text,
        "resume_text": resume_text
    })

    shrink_prompt = PromptTemplate(
        input_variables=["combined_text"],
        template="""
    You are an experienced recruiter, career strategist, and resume analyst.
    Your job is to shrink down the given combined text from JD and resume into very precise and concise text focusing on technology names, skills required, and possible question topics.
    This result will be used in Semantic matching with Interview questions.
    Return just the final text.

    combined_text:
    {combined_text}
    """
    )

    shrink_chain = shrink_prompt | llm
    combined_text = f"{jd_text}"
    shrinked_output = shrink_chain.invoke({"combined_text": combined_text})

    suggested_questions = suggester.suggest_questions(shrinked_output.content, top_k=20)

    response  = resp.model_dump()
    merged = {**response["Evaluation"], **response["Grammar_Check"]}

    merged["Suggested_Questions"] = suggested_questions

    json_merged = json.dumps(merged, indent=2)
    print(json_merged)

    return json_merged

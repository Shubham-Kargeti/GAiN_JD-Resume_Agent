from fastapi import APIRouter, HTTPException, Request, Depends
from app.utils.text_extract import extract_text
from app.config import memory_store
from app.schemas.schemas import ResumeAnalysisResponse,JDAnalysisResponse
import json
import asyncio
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from langchain.schema.runnable import RunnableMap
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq

router = APIRouter()


def get_question_suggester(request: Request):
    return request.app.state.question_suggester

@router.get("/process/jd_resume_match")
async def process(suggester=Depends(get_question_suggester)):
    if "resume" not in memory_store or "jd" not in memory_store:
        raise HTTPException(status_code=400, detail="Both resume and job description files must be uploaded first.")

    resume_info = memory_store["resume"]
    jd_store = memory_store.get("jd", {})
    jd_info = jd_store['jd_resume_match']

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

    shrink_prompt = PromptTemplate(
        input_variables=["combined_text"],
        template="""
    You are an expert recruiter, career strategist, and resume analyst.
    Your task is to extract and generate a concise, semantically rich summary from a combined job description and resume. Focus only on:
        Key technologies and tools,Core technical and soft skills,Relevant domains or frameworks
    The output will be used as a query input for retrieving the most relevant interview questions from a vector database.
    Ensure the result is embedding-friendly, using keywords and phrases suitable for semantic search.
    Avoid full sentences, explanations, or formatting.Return only the final keyword-rich text.

    combined_text:
    {combined_text}
    """
    )

    shrink_chain = shrink_prompt | llm
    combined_text = f"{jd_text}"

    resp_task = chain.ainvoke({
        "jd_text": jd_text,
        "resume_text": resume_text
    })

    shrink_task = shrink_chain.ainvoke({
        "combined_text": combined_text
    })

    resp, shrinked_output = await asyncio.gather(resp_task, shrink_task)

    suggested_questions = suggester.suggest_questions(shrinked_output.content, top_k=20)

    question_reframming_prompt = PromptTemplate(
        input_variables=["suggested_questions"],
        template="""
   You are an expert recruiter, career strategist, and English language specialist.
   You are given a list of raw interview questions retrieved from a database. These questions may be incomplete, repetitive, unpolished, or poorly worded.

    Your task is to:
    - Analyze and refine the list.
    - Rephrase the questions using clear, professional, and grammatically correct language.
    - Remove duplicates or near-duplicates.
    - Ensure the final set is well-structured and suitable for sharing directly with a candidate.
    - Make sure the questions collectively cover all key skills and topics represented in the input.
    - Only return the formated questions. Do not return anything else in prefix or suffix of questions

    Focus on improving clarity, tone, and relevance while preserving the original intent behind each question.

    suggested_questions:
    {suggested_questions}
    """
    )

    question_reframming = question_reframming_prompt | llm
    question_reframming_task = question_reframming.ainvoke({
        "suggested_questions": suggested_questions
    })

    reframmed_questions = await asyncio.gather(question_reframming_task)
    print(reframmed_questions)
    response  = resp.model_dump()
    merged = {**response["Evaluation"], **response["Grammar_Check"]}

    merged["Suggested_Questions"] = reframmed_questions[0].content

    json_merged = json.dumps(merged, indent=2)
    print(json_merged)

    return json_merged


@router.get("/process/analyze_jd/")
async def analyzejd():
    jd_store = memory_store.get("jd", {})
    jd_info = jd_store['analyze_jd']
    jd_text = extract_text(jd_info["bytes"], jd_info["filename"])

    llm = ChatGroq(model="openai/gpt-oss-20b")

    # Set up the output parser for JDAnalysisResponse
    pydantic_parser = PydanticOutputParser(pydantic_object=JDAnalysisResponse)
    fixing_parser = OutputFixingParser.from_llm(parser=pydantic_parser, llm=llm)

    prompt = PromptTemplate(
        input_variables=["jd_text", "format_instructions"],
        template="""
            You are an HR Analyst AI assistant. Given the following Job Description (JD), perform the following tasks:

            1. Sanitize the JD: Remove any sensitive or customer-identifiable info (like client names, company names, emails, phone numbers).
            2. Extract:
            - Must-have skills (3–5)
            - Good-to-have skills (2–3)
            - Location
            - Duration

            Respond in JSON using this schema:
            {format_instructions}

            --- JOB DESCRIPTION ---
            {jd_text}
            """
    )

    format_instructions = fixing_parser.get_format_instructions()

    # Combine prompt and model
    chain = (
        prompt.partial(format_instructions=format_instructions)
        | llm
        | fixing_parser
    )

    result = await chain.ainvoke({"jd_text": jd_text})

    # Final response is already a validated JDAnalysisResponse
    return result.dict()
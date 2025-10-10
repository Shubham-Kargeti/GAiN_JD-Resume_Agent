from pydantic import BaseModel, Field
from typing import List

class ResumeReport(BaseModel):
    result: str

class EvaluationSection(BaseModel):
    JD_MatchScore: str = Field(
        description="Overall match score between the job description and the candidate's resume. Should be a out of 10 score"
    )
    Score_Explanation: str = Field(
        description="Explanation of how the JD match score was determined, highlighting key evaluation criteria used."
    )
    Key_Matches: List[str] = Field(
        default_factory=list,
        description="Important skills, experiences, or technologies that are present in both the resume and the job description."
    )
    Key_Gaps: List[str] = Field(
        default_factory=list,
        description="Missing or underrepresented qualifications or skills in the resume that are mentioned in the job description."
    )
    Recommendations: List[str] = Field(
        default_factory=list,
        description="Suggestions for improving the resume to better match the job description. These may include skill additions, rephrasing, or formatting improvements."
    )

class GrammarCheckSection(BaseModel):
    Grammatical_Errors: List[str] = Field(
        default_factory=list,
        description="List of grammatical errors found in the text."
    )
    Spelling_Mistakes: List[str] = Field(
        default_factory=list,
        description="List of spelling mistakes detected in the text."
    )
    Client_Names: List[str] = Field(
        default_factory=list,
        description="List of client or company names identified in the resume."
    )

class ResumeAnalysisResponse(BaseModel):
    Evaluation: EvaluationSection
    Grammar_Check: GrammarCheckSection

from fastapi import FastAPI
from app.api import resume, jd, process,suggestQA
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    app.state.question_suggester = suggestQA.QuestionSuggester(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        faiss_path="app/vector_db/vector_store/faiss_index2"
    )
    yield

app = FastAPI(title="Resume Validator",lifespan=lifespan)

#Define CORS
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["http://localhost:5173"],
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register routers
app.include_router(resume.router, prefix="/resume", tags=["Resume"])
app.include_router(jd.router, prefix="/jd", tags=["Job Description"])
app.include_router(process.router, prefix="/process", tags=["Process"])

# Optionally, add more general routes or a health check route
@app.get("/")
def read_root():
    return {"message": "Welcome to the Resume Validator API!"}


@app.get("/health")
def health_check():
    return {"message": "Healthy!"}


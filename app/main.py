from fastapi import FastAPI
from app.api import resume, jd, process 

app = FastAPI(title="Resume Validator")

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


from fastapi import APIRouter, File, UploadFile, HTTPException
from app.utils.text_extract import extract_text
from app.config import ALLOWED_EXTENSIONS, memory_store

router = APIRouter()

@router.post("/upload/")
async def upload_jd(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file sent")
    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Only .docx and .pdf files are allowed")

    # Save JD to memory
    memory_store["jd"] = {"bytes": await file.read(), "filename": file.filename}
    return {"info": f"Uploaded Job Description '{file.filename}' successfully."}

def allowed_file(filename: str) -> bool:
    ext = filename.split(".")[-1].lower()
    return ext in ALLOWED_EXTENSIONS

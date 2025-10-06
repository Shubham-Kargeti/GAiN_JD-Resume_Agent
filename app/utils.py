import io
# from docx import Document
import pdfplumber

def extract_text_from_pdf(file_bytes: bytes) -> str:
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)

# def extract_text_from_docx(file_bytes: bytes) -> str:
#     document = Document(io.BytesIO(file_bytes))
#     text_parts = []
#     for para in document.paragraphs:
#         if para.text:
#             text_parts.append(para.text)
#     return "\n".join(text_parts)

def extract_text(file_bytes: bytes, name: str) -> str:
    ext = name.lower().split('.')[-1]
    if ext == "pdf":
        return extract_text_from_pdf(file_bytes)
    # elif ext == "docx":
    #     return extract_text_from_docx(file_bytes)
    else:
        raise ValueError(f"Unsupported file extension")

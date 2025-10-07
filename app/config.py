from dotenv import load_dotenv

load_dotenv()

# Allowed file extensions
ALLOWED_EXTENSIONS = {"pdf", "docx"}

# In-memory store for files (you can use a proper database in production)
memory_store = {}

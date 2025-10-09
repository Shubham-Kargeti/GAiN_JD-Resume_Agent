from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.vectorstores import VectorStore
from typing import List, Dict

class QuestionSuggester:
    def __init__(self, model_name: str, faiss_path: str):
        self.embedding_model = HuggingFaceEmbeddings(model_name=model_name)
        self.vectorstore: VectorStore = FAISS.load_local(
            faiss_path,
            self.embedding_model,
            allow_dangerous_deserialization=True
        )

    def suggest_questions(self, input_text: str, top_k: int = 15) -> List[Dict[str, float]]:
        results = self.vectorstore.similarity_search_with_score(input_text, k=top_k)
        return [
            {
                "question": doc.page_content,
                "score": float(score)
            }
            for doc, score in results
        ]

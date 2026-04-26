import os
from datetime import datetime
from langchain.tools import tool
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document

class MemoryTool:
    def __init__(self, collection: str = "memory"):
        self.collection = collection
        self.embeddings = OllamaEmbeddings(
            model=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        )
        self.db = Chroma(
            collection_name=self.collection,
            embedding_function=self.embeddings,
            persist_directory=".chroma"
        )

    def save(self, user_input: str, answer: str):
        self.db.add_documents([
            Document(
                page_content=f"시청자: {user_input}\n하루: {answer}",
                metadata={"timestamp": datetime.now().isoformat()}
            )
        ])

    def build(self):
        db = self.db

        @tool
        def memory_search(query: str) -> str:
            """과거 대화 기록에서 관련 맥락을 찾을 때 사용."""
            results = db.similarity_search(query, k=3)
            if not results:
                return "관련 대화 기록이 없어요."
            return "\n".join(
                f"- [{r.metadata.get('timestamp', '')}] {r.page_content}"
                for r in results
            )

        return memory_search
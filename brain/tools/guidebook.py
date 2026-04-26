import os
from langchain.tools import tool
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader

class GuidebookTool:
    def __init__(self, docs_path: str = "docs/", collection: str = "guidebook"):
        self.docs_path = docs_path
        self.collection = collection
        self.embeddings = OllamaEmbeddings(
            model=os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        )
        self.db = self._load_or_create()

    def _load_or_create(self) -> Chroma:
        if os.path.exists(f".chroma/{self.collection}"):
            return Chroma(
                collection_name=self.collection,
                embedding_function=self.embeddings,
                persist_directory=".chroma"
            )

        loader = DirectoryLoader(self.docs_path, loader_cls=TextLoader)
        docs = loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500, chunk_overlap=50
        )
        chunks = splitter.split_documents(docs)

        return Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            collection_name=self.collection,
            persist_directory=".chroma"
        )

    def build(self):
        db = self.db

        @tool
        def guidebook_search(query: str) -> str:
            """VTuber 운영 가이드북에서 정보를 찾을 때 사용. 캐릭터 설정, 규칙, 방송 가이드 등."""
            results = db.similarity_search(query, k=3)
            if not results:
                return "가이드북에서 관련 내용을 찾지 못했어요."
            return "\n".join(
                f"- {doc.page_content}" for doc in results
            )

        return guidebook_search
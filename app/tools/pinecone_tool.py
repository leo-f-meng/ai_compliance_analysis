from langchain.tools import BaseTool
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from pydantic import BaseModel
from app.config import settings


class PineconeInput(BaseModel):
    query: str
    namespace: str = "gdpr"
    top_k: int = 3


class PineconeRetrieverTool(BaseTool):
    name: str = "pinecone_retriever"
    description: str = (
        "Retrieve relevant GDPR regulatory guidance from the knowledge base. "
        "Use for grey-area clauses where the requirement is ambiguous. "
        "Provide a natural language query describing what you need to verify. "
        "Returns up to 3 relevant regulatory text passages with source references."
    )
    args_schema: type[BaseModel] = PineconeInput
    _store: PineconeVectorStore = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=settings.openai_api_key,
        )
        self._store = PineconeVectorStore(
            index_name=settings.pinecone_index_name,
            embedding=embeddings,
            pinecone_api_key=settings.pinecone_api_key,
        )

    def _run(self, query: str, namespace: str = "gdpr", top_k: int = 3) -> str:
        docs = self._store.similarity_search(query, k=top_k, namespace=namespace)
        if not docs:
            return "No relevant regulatory guidance found for this query."
        parts = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "unknown")
            parts.append(f"[{i}] Source: {source}\n{doc.page_content}")
        return "\n\n".join(parts)

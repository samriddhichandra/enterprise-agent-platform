"""
RAG pipeline: loads documents, splits them into chunks, embeds them into
ChromaDB, and retrieves the most relevant chunks for a given query.

This is deliberately kept as plain, readable LangChain primitives rather than
a black-box wrapper, so every step here is something you can explain in an
interview:

    load documents -> split into chunks -> embed -> store in Chroma
    query -> embed query -> similarity search -> return top-k chunks
"""
import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

from backend.config import settings


class RAGPipeline:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            openai_api_key=settings.openai_api_key,
        )
        self.vectorstore = Chroma(
            collection_name="enterprise_docs",
            embedding_function=self.embeddings,
            persist_directory=settings.chroma_persist_dir,
        )
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
        )

    def _load_file(self, path: str):
        if path.lower().endswith(".pdf"):
            return PyPDFLoader(path).load()
        return TextLoader(path, encoding="utf-8").load()

    def ingest_directory(self, directory: str | None = None) -> int:
        """
        Walks a directory, loads every .pdf/.txt/.md file, splits it into
        chunks, and adds those chunks to the Chroma collection.

        Returns the number of chunks indexed.
        """
        directory = directory or settings.docs_dir
        if not os.path.isdir(directory):
            raise FileNotFoundError(f"Docs directory not found: {directory}")

        all_chunks = []
        for filename in os.listdir(directory):
            if not filename.lower().endswith((".pdf", ".txt", ".md")):
                continue
            filepath = os.path.join(directory, filename)
            docs = self._load_file(filepath)
            chunks = self.splitter.split_documents(docs)
            for chunk in chunks:
                chunk.metadata["source"] = filename
            all_chunks.extend(chunks)

        if all_chunks:
            self.vectorstore.add_documents(all_chunks)

        return len(all_chunks)

    def retrieve(self, query: str, k: int = settings.top_k) -> list[dict]:
        """
        Returns the top-k most relevant chunks for a query, each as a dict
        with the text and its source filename (so answers can be traced
        back to a document).
        """
        results = self.vectorstore.similarity_search(query, k=k)
        return [
            {"text": doc.page_content, "source": doc.metadata.get("source", "unknown")}
            for doc in results
        ]


# Single shared instance used across the app
rag_pipeline = RAGPipeline()

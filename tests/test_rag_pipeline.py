"""
Tests for the RAG pipeline's document splitting behavior.
Uses the text splitter directly (no OpenAI/Chroma calls needed) so this
runs without an API key.
"""
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document


def test_splitter_chunks_long_document():
    splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
    long_text = "This is a sentence. " * 50  # ~1000 chars
    doc = Document(page_content=long_text)

    chunks = splitter.split_documents([doc])

    assert len(chunks) > 1
    assert all(len(c.page_content) <= 120 for c in chunks)  # allow overlap slack


def test_splitter_keeps_short_document_as_one_chunk():
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    short_text = "Short document content."
    doc = Document(page_content=short_text)

    chunks = splitter.split_documents([doc])

    assert len(chunks) == 1
    assert chunks[0].page_content == short_text

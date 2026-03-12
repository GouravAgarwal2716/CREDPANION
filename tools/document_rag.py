"""
tools/document_rag.py
RAG tool for parsing uploaded PDFs, creating an ephemeral in-memory
Chroma vector store, and retrieving context for agents.
"""
from __future__ import annotations
import os
import glob
from typing import List, Optional

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# A global dictionary to cache vector stores by a hash of the file paths so we 
# don't re-embed the same documents repeatedly per request.
_vectorstore_cache = {}

def get_embeddings():
    """Returns the Google Generative AI embeddings model."""
    return GoogleGenerativeAIEmbeddings(model="models/embedding-001")


def create_or_get_vectorstore(file_paths: List[str]) -> Optional[Chroma]:
    """
    Given a list of PDF file paths, extracts the text, creates embeddings,
    and returns an ephemeral Chroma vector store. Uses an in-memory cache.
    """
    # Filter out non-existent or non-PDF files
    valid_pdfs = [f for f in file_paths if os.path.exists(f) and f.lower().endswith(".pdf")]
    
    if not valid_pdfs:
        return None

    # Create a unique cache key based on the sorted file sizes and paths
    # (In a real production system, this would be a hash of the file content or an actual persistent DB)
    cache_key = tuple(sorted([(f, os.path.getsize(f)) for f in valid_pdfs]))
    if cache_key in _vectorstore_cache:
        return _vectorstore_cache[cache_key]

    docs: List[Document] = []
    for pdf_path in valid_pdfs:
        try:
            loader = PyPDFLoader(pdf_path)
            loaded_docs = loader.load()
            docs.extend(loaded_docs)
        except Exception as e:
            print(f"Error loading PDF {pdf_path}: {e}")

    if not docs:
        return None

    # Split text into manageable chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    splits = text_splitter.split_documents(docs)

    # Note: We rely on the GOOGLE_API_KEY environment variable being set.
    embeddings = get_embeddings()

    # Create in-memory Chroma vector store
    vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings)
    
    # Store in cache
    _vectorstore_cache[cache_key] = vectorstore
    return vectorstore


def query_documents(query: str, file_paths: List[str], k: int = 4) -> str:
    """
    Creates a vector store for the provided PDFs and runs a similarity search.
    Returns a unified string of the most relevant document chunks.
    If no PDFs are provided or valid, returns an empty string.
    """
    vectorstore = create_or_get_vectorstore(file_paths)
    if not vectorstore:
        return ""

    results = vectorstore.similarity_search(query, k=k)
    
    if not results:
        return ""
        
    context_chunks = []
    for i, doc in enumerate(results):
        source = os.path.basename(doc.metadata.get("source", "Unknown"))
        page = doc.metadata.get("page", "?")
        context_chunks.append(f"--- Excerpt from {source} (Page {page}) ---\n{doc.page_content.strip()}")

    return "\n\n".join(context_chunks)

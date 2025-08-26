import os
import logging
from langchain_community.vectorstores import Pinecone as PineconeStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.schema import Document
from pinecone import Pinecone, ServerlessSpec
from backend.utils.config import settings

# Initialize embeddings safely
try:
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=settings.GOOGLE_API_KEY,
    )
except Exception as e:
    logging.error(f"Failed to initialize embeddings: {e}")

# Initialize Pinecone safely
try:
    pc = Pinecone(
        api_key=settings.PINECONE_API_KEY,
        environment=settings.PINECONE_ENV,
    )
except Exception as e:
    logging.error(f"Failed to initialize Pinecone: {e}")

INDEX_NAME = "financial-filings"

# Ensure index exists with correct dimension
def ensure_index():
    """Ensure Pinecone index exists, create if missing."""
    if not pc or not embeddings:
        logging.error("Pinecone or embeddings not initialized.")
        return

    try:
        if INDEX_NAME not in pc.list_indexes():
            dim = len(embeddings.embed_query("dimension test"))
            pc.create_index(
                name=INDEX_NAME,
                dimension=dim,
                metric="euclidean",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1",
                ),
            )
            logging.info(f"Created Pinecone index {INDEX_NAME} with dimension {dim}")
        else:
            logging.info(f"Index {INDEX_NAME} already exists, skipping creation")
    except Exception as e:
        logging.error(f"Error ensuring Pinecone index: {e}")

def init_vector_store():
    """Return Pinecone vector store wrapper."""
    return PineconeStore.from_existing_index(INDEX_NAME, embeddings)

def store_embeddings(metadata: dict, section: str, content: str):
    """
    Store embeddings for a filing section in Pinecone.
    """
    if not content or content == "Not Found":
        return

    db = init_vector_store()
    doc = Document(
        page_content=content,
        metadata={
            "title": metadata.get("title"),
            "date": metadata.get("date"),
            "filing_url": metadata.get("filing_url"),
            "section": section,
        },
    )
    try:
        db.add_documents([doc])
        logging.info(f"Stored section '{section}' for filing {metadata.get('title')}")
    except Exception as e:
        logging.error(f"Error storing embeddings: {e}")

def store_embeddings_batch(metadata: dict, sections: dict):
    """
    Store multiple sections at once.
    sections: dict {section_name: content}
    """
    docs = []
    for section, content in sections.items():
        if content and content != "Not Found":
            docs.append(
                Document(
                    page_content=content,
                    metadata={
                        "title": metadata.get("title"),
                        "date": metadata.get("date"),
                        "filing_url": metadata.get("filing_url"),
                        "section": section,
                    },
                )
            )

    if docs:
        db = init_vector_store()
        try:
            db.add_documents(docs)
            logging.info(f"Stored {len(docs)} sections for filing {metadata.get('title')}")
        except Exception as e:
            logging.error(f"Error storing batch embeddings: {e}")

def query_vector_db(query: str, k: int = 3):
    """Query Pinecone vector store."""
    try:
        db = init_vector_store()
        docs = db.similarity_search(query, k=k)
        return [
            {"content": doc.page_content, "metadata": doc.metadata}
            for doc in docs
        ]
    except Exception as e:
        logging.error(f"Error querying vector DB: {e}")
        return []


import logging
from backend.data.parser import fetch_and_parse_full_filing
from backend.db.mongo import save_filing
from backend.db.vector_store import (store_embeddings_batch, ensure_index)
from backend.utils.config import settings



def run_etl(cik: str, filing_type: str = "10-K"):
    """
    Orchestrates the ETL process:
    1. Fetch & parse filing
    2. Store metadata + sections in Mongo
    3. Store embeddings (batch) in Pinecone
    """
    
    try:
        cik = cik or settings.SEC_CIK
        logging.info(f"Starting ETL for CIK: {cik}, Filing Type: {filing_type}")
        
        # ensure that Pinecone exists
        ensure_index()
        logging.info("Verified Pinecone index is ready.")
        
        # Fetch and parse filing
        filing_data = fetch_and_parse_full_filing(cik, filing_type)
        if "error" in filing_data:
            logging.error(f"Parsing failed: {filing_data['error']}")
            return filing_data

        metadata = filing_data["metadata"]
        sections = filing_data["sections"]
        logging.info(f"Fetched and parsed filing: {metadata.get('title')} ({metadata.get('date')})")
        logging.info(f"Parsed {len(sections)} sections")

        # Store in Mongo
        save_filing(metadata, sections)
        logging.info(f"Saved filing '{metadata.get('title')}' to MongoDB")

        # Store all sections in Pinecone (batch)
        store_embeddings_batch(metadata, sections)
        logging.info(f"Stored embeddings for {len(sections)} sections in Pinecone")

    
        logging.info("ETL pipeline completed successfully")
        return {"status": "success", "metadata": metadata}

    except Exception as e:
        logging.error(f"ETL failed: {e}", exc_info=True)
        return {"error": str(e)}

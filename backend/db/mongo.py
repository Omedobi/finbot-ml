import os
import logging
from pymongo import MongoClient
from backend.utils.config import settings


MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = "financial_chatbot"
COLLECTION_NAME = "filings"

def init_mongo():
    """Initialize MongoDB client and return the collection."""
    try:
        client = MongoClient(MONGO_URL)
        db = client[DB_NAME]
        return db[COLLECTION_NAME]
    except Exception as e:
        logging.error(f"MongoDB connection failed: {e}")
        raise
    
def save_filing(filing_json: dict):
    """
    Save parsed filing JSON into MongoDB.
    Avoid duplicate entries by using filing_url as unique key.
    """
    try:
        collection = init_mongo()
        if not filing_json.get("metadata"):
            raise ValueError("Filing JSON must contain 'metadata' field.")

        query = {"metadata.filing_url": filing_json["metadata"].get("filing_url")}
        collection.update_one(query, {"$set": filing_json}, upsert=True)
        logging.info(f"filing saved: {filing_json['metadata'].get('title')}")
    except Exception as e:
        logging.error(f"Error saving filing: {e}")
        raise
    
def get_filing_by_clk(clk: str, limit: int= 5):
    """
    Retrieve filings for a given CIK, newest first
    """
    try:
        collection = init_mongo()
        return list(collection.find({"metadata.cik": clk}).sort("metadata.date", -1).limit(limit))
    except Exception as e:
        logging.error(f"Error retrieving filings: {e}")
        raise

def get_latest_filing(cik: str):
    """
    Retrieve the latest filing for a given CIK
    """
    try:
        collection = init_mongo()
        return collection.find_one({"metadata.cik": cik}, sort=[("metadata.date", -1)])
    except Exception as e:
        logging.error(f"Error retrieving latest filing: {e}")
        raise

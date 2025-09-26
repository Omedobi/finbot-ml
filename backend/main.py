import logging
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.agents.financial_agent import FinancialAgent
from backend.data.scraper import fetch_latest_filings
from backend.data.parser import fetch_and_parse_full_filing
from backend.data.etl import run_etl
from backend.utils.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

app = FastAPI(title="Financial Chatbot Backend")

# Initialize financial agent (CrewAI/LLM pipeline)
agent = FinancialAgent()

# Add CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Schemas
class ChatRequest(BaseModel):
    query: str
    cik: str | None = None  # Restrict search to a company

class ETLRequest(BaseModel):
    cik: str | None = None
    filing_type: str = "10-K"

# Endpoints
@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        response = agent.run(request.query, cik=request.cik)
        return {"answer": response}
    except Exception as e:
        logging.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scrape")
async def scrape_endpoint():
    try:
        filings = fetch_latest_filings(
            settings.SEC_CIK,
            filing_type="10-K",
            count=5,
        )
        return {"filings": filings}
    except Exception as e:
        logging.error(f"Scrape endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/etl")
async def etl_endpoint(request: ETLRequest):
    """
    Trigger ETL for a given CIK and filing type.
    Stores parsed sections in Mongo + Pinecone.
    """
    try:
        logging.info(f"Received ETL request for cik={request.cik}, filing_type={request.filing_type}")
        result = run_etl(request.cik, request.filing_type)
        return result
    except Exception as e:
        logging.error(f"ETL endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Local Debug Mode
if __name__ == "__main__":
    logging.info("Starting FastAPI app in debug mode...")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)

# backend/data/parser.py
import re
import logging
import spacy
from backend.data.scraper import (fetch_latest_filings, fetch_filing_document_url, fetch_filing_text)

# Load spaCy model once
try:
    nlp = spacy.load("en_core_web_sm")
except Exception:
    nlp = None
    logging.warning("spaCy model not available, fallback will be skipped.")


def parse_filing_sections(filing_text: str) -> dict:
    """
    Parse filing text to extract key 10-K sections.
    Returns dictionary with section names as keys and text as values.
    """
    sections = {}
    text = re.sub(r"\s+", " ", filing_text)

    patterns = {
        "risk_factors": r"ITEM\s+1A\.*\s+RISK FACTORS(.*?)(ITEM\s+[1-9]|SIGNATURES)",
        "management_discussion": r"ITEM\s+7\.*\s+MANAGEMENT.*?DISCUSSION(.*?)(ITEM\s+8|FINANCIAL STATEMENTS)",
        "financial_statements": r"ITEM\s+8\.*\s+FINANCIAL STATEMENTS(.*?)(ITEM\s+9|CHANGES IN)",
    }

    # Try regex extraction
    for section, pattern in patterns.items():
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        sections[section] = match.group(1).strip() if match else None

    # If regex failed for all, try spaCy fallback
    if not any(sections.values()) and nlp:
        try:
            current_section = None
            paragraphs = filing_text.split("\n\n")
            for paragraph in paragraphs:
                paragraph = paragraph.strip()
                if not paragraph:
                    continue

                # Use uppercase heuristic for section headers
                if paragraph.isupper():
                    current_section = paragraph
                    sections[current_section] = ""
                elif current_section:
                    sections[current_section] += paragraph + "\n"
        except Exception as e:
            logging.error(f"spaCy fallback parsing failed: {e}")

    return sections


def fetch_and_parse_full_filing(cik: str, filing_type: str = "10-K"):
    """
    Fetch and parse the full text of a specific SEC filing.
    """
    try:
        filings = fetch_latest_filings(cik, filing_type=filing_type, count=1)
        if not filings:
            raise Exception("No filings found")

        filing = filings[0]
        doc_url = fetch_filing_document_url(filing["filing_url"])
        filing_text = fetch_filing_text(doc_url)
        sections = parse_filing_sections(filing_text)

        return {
            "metadata": filing,
            "sections": sections
        }
    except Exception as e:
        logging.error(f"Error occurred while fetching and parsing full filing: {e}")
        return {"error": str(e)}

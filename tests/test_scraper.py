import pytest
# import sys, os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.data.scraper import (fetch_latest_filings, 
                                  fetch_filing_document_url, 
                                  fetch_filing_text)


# Example CIK for Apple Inc.
APPLE_CIK = "0000320193"


def test_fetch_latest_filings():
    filings = fetch_latest_filings(APPLE_CIK, filing_type="10-K", count=2)
    assert isinstance(filings, list)
    assert len(filings) > 0
    assert "title" in filings[0]
    assert "filing_url" in filings[0]
    assert filings[0]["filing_url"].startswith("https://")


def test_fetch_filing_document_url():
    filings = fetch_latest_filings(APPLE_CIK, "10-K", count=1)
    assert len(filings) > 0
    filing_url = filings[0]["filing_url"]

    doc_url = fetch_filing_document_url(filing_url)
    assert isinstance(doc_url, str)
    assert doc_url.startswith("https://")


def test_fetch_filing_text():
    filings = fetch_latest_filings(APPLE_CIK, "10-K", count=1)
    filing_url = filings[0]["filing_url"]
    doc_url = fetch_filing_document_url(filing_url)

    text = fetch_filing_text(doc_url)
    assert isinstance(text, str)
    assert len(text) > 1000  # ensure non-empty filing

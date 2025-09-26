import requests
import logging
import typing, os
import xml.etree.ElementTree as ET
import re
from lxml import (etree, html)
from bs4 import BeautifulSoup
from io import BytesIO

SEC_BASE = "https://www.sec.gov"
HEADERS = {"user-agent": "FinancialChatbot/1.0 (ikennaanyawuike@gmail.com)"}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_latest_filings(cik: str, filing_type: str = "10-K", count: int = 10):
    try:
        url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type={filing_type}&count={count}&output=atom"
        response = requests.get(url, headers=HEADERS, timeout=15)

        if response.status_code != 200:
            raise Exception(f"SEC request failed: {response.status_code}")

        parser = etree.XMLParser(ns_clean=True, recover=True)
        root = etree.fromstring(response.content, parser=parser)
        entries = root.findall(".//{http://www.w3.org/2005/Atom}entry")

        filings = []
        for entry in entries:
            title = entry.findtext("{http://www.w3.org/2005/Atom}title")
            updated = entry.findtext("{http://www.w3.org/2005/Atom}updated")
            link_el = entry.find("{http://www.w3.org/2005/Atom}link")
            link = link_el.get("href") if link_el is not None else None

            filings.append({
                "title": title,
                "filing_url": link,
                "date": updated,
            })
        return filings
    except Exception as e:
        logger.error(f"Error fetching latest filings: {e}")
        return []
        

def fetch_filing_document_url(filing_url: str) -> str:
    """Get primary filing document URL from SEC filing detail page."""
    try:
        response = requests.get(filing_url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            raise Exception("Failed to fetch filing detail page")

        doc = html.fromstring(response.content)
        hrefs = doc.xpath("//table//tr/td/a/@href")

        # Usually the first .htm file is the main filing document
        for href in hrefs:
            if href.endswith((".htm",".html",".txt")):
                return SEC_BASE + href
        raise Exception("No primary filing document found")
    except Exception as e:
        logger.error(f"Error fetching filing document URL: {e}")
        return ""


def fetch_filing_text(filing_doc_url: str) -> str:
    """Download full filing text (raw)."""
    
    try:
        response = requests.get(filing_doc_url, headers=HEADERS, timeout=20)
        if response.status_code != 200:
            raise Exception("Failed to fetch filing document")
        return response.text
    except Exception as e:
        logger.error(f"Error fetching filing text: {e}")
        return ""
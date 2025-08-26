from crewai import Agent, Crew, Task
from backend.data.scraper import (fetch_latest_filings)
from backend.db.vector_store import query_vector_db

# Define individual agents
scraper_agent = Agent(
    role="SEC Scraper",
    goal="Fetch the latest SEC filings for a given company",
    backstory="Specialist in accessing SEC EDGAR XML feeds",
    verbose=True,
    allow_delegation=False
)

db_agent = Agent(
    role="Vector DB Searcher",
    goal="Retrieve and summarize relevant information from financial filings",
    backstory="Knows how to use embeddings and vector search to find insights",
    verbose=True,
    allow_delegation=False
)

# Crew that manages the workflow
class FinancialAgent:
    def __init__(self):
        self.crew = Crew(
            agents=[scraper_agent, db_agent],
            verbose=True
        )

    def run(self, query: str):
        task1 = Task(
            description="Scrape the latest 10-K filings from SEC",
            agent=scraper_agent,
            expected_output="List of latest SEC filings",
            func = lambda: fetch_latest_filings("789019")  # Microsoft by default
        )

        task2 = Task(
            description=f"Query the vector DB for: {query}",
            agent=db_agent,
            expected_output="Relevant financial filing sections",
            func = lambda: query_vector_db(query)
        )

        results = self.crew.kickoff([task1, task2])
        return results

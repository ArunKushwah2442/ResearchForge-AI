from langchain.tools import tool

import os
import requests

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

# ==========================================================
# Tavily Client
# ==========================================================

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


# ==========================================================
# Search Tool
# ==========================================================

@tool
def web_search(query: str) -> str:
    """
    Search the web for recent and reliable information.

    Returns:
        Title
        URL
        Snippet
    """

    try:

        results = tavily.search(
            query=query,
            max_results=5
        )

        output = []

        for result in results["results"]:

            title = result.get("title", "")
            url = result.get("url", "")
            snippet = result.get("content", "")

            output.append(
                f"Title: {title}\n"
                f"URL: {url}\n"
                f"Snippet: {snippet[:300]}\n"
            )

        return "\n-------------------------\n".join(output)

    except Exception as e:

        return f"Search Error: {str(e)}"


# ==========================================================
# Reader Tool
# ==========================================================

@tool
def scrape_url(url: str) -> str:
    """
    Scrape the given URL and return clean readable text.
    """

    try:

        response = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0"
            },
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # Remove unwanted tags
        for tag in soup([
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "noscript",
            "svg",
            "img",
            "aside",
        ]):
            tag.decompose()

        text = soup.get_text(
            separator=" ",
            strip=True,
        )

        # Remove extra spaces
        text = " ".join(text.split())

        if len(text) == 0:
            return "No readable content found."

        return text[:5000]

    except Exception as e:

        return f"Scraping Error: {str(e)}"





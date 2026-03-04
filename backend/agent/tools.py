import os

from tavily import TavilyClient


def get_tavily_client():
    return TavilyClient(api_key=os.environ.get("TAVILY_API_KEY", ""))


def search_web(query: str, max_results: int = 5) -> dict:
    client = get_tavily_client()
    response = client.search(query, search_depth="advanced", max_results=max_results)
    return response

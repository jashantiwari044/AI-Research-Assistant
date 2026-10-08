"""
web_search.py — DuckDuckGo Web Search Integration
====================================================
This module searches the web using DuckDuckGo (no API key needed!).

KEY CONCEPTS:
─────────────
1. WEB SEARCH vs REST API:
   Unlike Wikipedia (which has a structured API), DuckDuckGo's
   search library scrapes search results from the web. This is
   less reliable but gives broader results from many websites.

2. RATE LIMITING:
   Search engines don't want bots hammering them with requests.
   If you send too many requests too quickly, they'll block you.
   The duckduckgo-search library handles this internally, but
   we still add our own error handling for safety.

3. NO API KEY NEEDED:
   DuckDuckGo is privacy-focused and doesn't require registration.
   This makes it perfect for learning and prototyping!
"""

from typing import List
from duckduckgo_search import DDGS

from search.base import BaseSearcher
from models.schemas import SearchResult
from config import MAX_SEARCH_RESULTS


class WebSearcher(BaseSearcher):
    """
    Searches the web using DuckDuckGo for general web results.

    DuckDuckGo returns results from across the entire web,
    making it complementary to Wikipedia (which only has
    encyclopedia-style articles).

    Example:
        searcher = WebSearcher()
        results = searcher.search("latest quantum computing breakthroughs 2026")
        for r in results:
            print(r.title, r.url)
    """

    def search(self, query: str) -> List[SearchResult]:
        """
        Search DuckDuckGo for web results related to the query.

        Args:
            query: The research question or topic

        Returns:
            List of SearchResult objects from web search

        Note:
            Returns an empty list if the search fails or finds nothing.
        """
        results = []

        try:
            # ── Perform the web search ─────────────────────────────
            # DDGS() creates a DuckDuckGo search session
            # .text() searches for text results (not images/videos)
            #
            # Parameters:
            #   keywords:    The search query
            #   max_results: Cap the number of results
            with DDGS() as ddgs:
                search_results = ddgs.text(
                    keywords=query,
                    max_results=MAX_SEARCH_RESULTS,
                )

                # ── Process each result ────────────────────────────
                # Each result is a dictionary with keys:
                #   title: Page title
                #   href:  URL of the page
                #   body:  Snippet/description of the page
                for item in search_results:
                    result = SearchResult(
                        title=item.get("title", "No Title"),
                        snippet=item.get("body", "No description available."),
                        url=item.get("href", ""),
                        source="duckduckgo",
                    )
                    results.append(result)

            print(f"  ✓ DuckDuckGo: found {len(results)} result(s)")

        except Exception as e:
            # ── Error Handling ──────────────────────────────────────
            # Common errors:
            # - RatelimitException: Too many requests too fast
            # - TimeoutException: DuckDuckGo took too long to respond
            # - DuckDuckGoSearchException: General search failure
            #
            # We log the error and return whatever we have (possibly empty).
            # The main pipeline will still work with Wikipedia results.
            print(f"  ✗ DuckDuckGo search failed: {str(e)}")

        return results

    def get_source_name(self) -> str:
        """Return the name of this search source."""
        return "duckduckgo"

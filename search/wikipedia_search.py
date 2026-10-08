"""
wikipedia_search.py — Wikipedia Search Integration
=====================================================
This module searches Wikipedia for articles related to a research query.

KEY CONCEPTS:
─────────────
1. REST APIs:
   Wikipedia provides a free API that returns data in JSON format.
   You send a URL with your query → it sends back structured data.
   It's like asking a librarian a question and getting a neat answer card.

2. THE wikipedia-api PACKAGE:
   Instead of crafting raw HTTP requests, this package wraps the
   Wikipedia API into simple Python methods. This is called an
   "API client library" — it abstracts away the complexity.

3. ERROR HANDLING:
   Many things can go wrong when calling external APIs:
   - Network is down → requests.ConnectionError
   - Wikipedia is down → requests.HTTPError
   - Page doesn't exist → need to check API response
   - Ambiguous query (e.g., "Python") → disambiguation page

   We handle ALL of these gracefully so the app doesn't crash.

4. TRY/EXCEPT:
   Python's try/except lets you "catch" errors and handle them:
       try:
           risky_operation()      # This might fail
       except SomeError as e:
           handle_the_error(e)    # This runs if it fails
       else:
           success_path()         # This runs if it succeeds
"""

from typing import List
import wikipediaapi

from search.base import BaseSearcher
from models.schemas import SearchResult
from config import WIKIPEDIA_LANGUAGE, MAX_SEARCH_RESULTS


class WikipediaSearcher(BaseSearcher):
    """
    Searches Wikipedia for articles matching a research query.

    How it works:
    1. Uses the Wikipedia API to search for page titles matching the query
    2. For each matching page, fetches the title, summary, and URL
    3. Returns results as SearchResult objects

    Example:
        searcher = WikipediaSearcher()
        results = searcher.search("quantum computing")
        for r in results:
            print(r.title, r.url)
    """

    def __init__(self):
        """
        Initialize the Wikipedia API client.

        The user_agent identifies our application to Wikipedia's servers.
        Wikipedia requires this — it's good API citizenship!
        """
        self.wiki = wikipediaapi.Wikipedia(
            user_agent="AIResearchAssistant/1.0 (educational project)",
            language=WIKIPEDIA_LANGUAGE,
        )

    def search(self, query: str) -> List[SearchResult]:
        """
        Search Wikipedia for articles related to the query.

        Strategy:
        1. First, try to find the exact page matching the query
        2. If found, also search for related terms by splitting the query
        3. Collect unique results up to MAX_SEARCH_RESULTS

        Args:
            query: The research question or topic

        Returns:
            List of SearchResult objects from Wikipedia

        Note:
            Returns an empty list (not an error) if nothing is found.
            The caller can check len(results) and decide what to do.
        """
        results = []
        seen_titles = set()  # Track titles to avoid duplicates

        try:
            # ── Step 1: Search for key terms from the query ─────────
            # We extract meaningful words from the query to search
            search_terms = self._extract_search_terms(query)

            for term in search_terms:
                if len(results) >= MAX_SEARCH_RESULTS:
                    break

                # Try to find a Wikipedia page for this term
                page = self.wiki.page(term)

                # page.exists() checks if Wikipedia actually has this page
                if page.exists() and page.title not in seen_titles:
                    seen_titles.add(page.title)

                    # Create a SearchResult from the Wikipedia page
                    result = SearchResult(
                        title=page.title,
                        # page.summary gives first few sentences — perfect for context
                        snippet=self._truncate_text(page.summary, max_length=500),
                        url=page.fullurl,
                        source="wikipedia",
                    )
                    results.append(result)

            print(f"  ✓ Wikipedia: found {len(results)} result(s)")

        except Exception as e:
            # ── Error Handling ──────────────────────────────────────
            # If ANYTHING goes wrong (network, API, parsing), we catch
            # it here. We print a warning but DON'T crash the program.
            # This is "graceful degradation" — the app keeps working
            # with whatever results it has from other sources.
            print(f"  ✗ Wikipedia search failed: {str(e)}")

        return results

    def _extract_search_terms(self, query: str) -> List[str]:
        """
        Extract meaningful search terms from the query.

        We try multiple strategies to find relevant Wikipedia articles:
        1. The full query itself (might match a page directly)
        2. Key phrases from the query (skip common small words)

        Args:
            query: The user's research question

        Returns:
            List of terms to search for on Wikipedia
        """
        terms = []

        # Strategy 1: Try the full query as-is
        # Remove question marks and leading "what is" type phrases
        cleaned = query.strip().rstrip("?").strip()
        terms.append(cleaned)

        # Strategy 2: Extract individual meaningful words
        # Skip common words that won't match Wikipedia articles
        stop_words = {
            "what", "is", "are", "the", "a", "an", "how", "does", "do",
            "can", "could", "would", "should", "why", "when", "where",
            "which", "who", "in", "on", "at", "to", "for", "of", "and",
            "or", "but", "with", "about", "between", "into", "through",
            "during", "before", "after", "above", "below", "from", "up",
            "down", "out", "off", "over", "under", "again", "further",
            "then", "once", "here", "there", "all", "each", "every",
            "both", "few", "more", "most", "other", "some", "such",
            "no", "nor", "not", "only", "own", "same", "so", "than",
            "too", "very", "just", "because", "as", "until", "while",
            "it", "its", "this", "that", "these", "those", "was", "were",
            "been", "being", "have", "has", "had", "having", "did",
            "will", "shall", "might", "must", "need", "used", "latest",
            "recent", "new", "explain", "describe", "tell", "me",
        }

        words = cleaned.split()
        # Build multi-word phrases from remaining meaningful words
        meaningful_words = [w for w in words if w.lower() not in stop_words]

        # If we have multiple meaningful words, try them as a phrase
        if len(meaningful_words) >= 2:
            phrase = " ".join(meaningful_words)
            if phrase != cleaned:  # Avoid duplicate of full query
                terms.append(phrase)

        # Also try individual meaningful words
        for word in meaningful_words:
            if word not in terms and len(word) > 2:  # Skip very short words
                terms.append(word)

        return terms[:MAX_SEARCH_RESULTS + 2]  # Don't try too many terms

    def _truncate_text(self, text: str, max_length: int = 500) -> str:
        """
        Truncate text to a maximum length, ending at a sentence boundary.

        We don't want to cut off in the middle of a word or sentence,
        so we try to find the last period before the max length.

        Args:
            text: The text to truncate
            max_length: Maximum number of characters

        Returns:
            Truncated text, ending cleanly at a sentence if possible
        """
        if len(text) <= max_length:
            return text

        # Try to cut at the last sentence boundary (period + space)
        truncated = text[:max_length]
        last_period = truncated.rfind(". ")

        if last_period > max_length // 2:  # Only if the period isn't too early
            return truncated[: last_period + 1]

        return truncated.rstrip() + "..."

    def get_source_name(self) -> str:
        """Return the name of this search source."""
        return "wikipedia"

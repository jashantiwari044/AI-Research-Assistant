"""
base.py — Abstract Base Searcher
==================================
This module defines the INTERFACE that all search providers must follow.

KEY CONCEPT — THE STRATEGY PATTERN:
────────────────────────────────────
The Strategy Pattern lets you define a family of algorithms (in our case,
different search providers), put each in its own class, and make them
interchangeable.

    BaseSearcher (interface)
        ├── WikipediaSearcher  ← searches Wikipedia
        └── WebSearcher        ← searches DuckDuckGo

Because both implement the same search() method, the rest of our code
doesn't need to know WHICH searcher it's using. It just calls .search()
and gets back a list of SearchResults.

WHY THIS MATTERS:
- Want to add a new search source (e.g., arXiv)? Just create a new class
  that extends BaseSearcher. No other code changes needed!
- Want to swap Wikipedia for Google Scholar? Replace one class.
- This is how professional codebases stay maintainable.

KEY CONCEPT — ABSTRACT BASE CLASSES:
─────────────────────────────────────
An abstract class is a class that CANNOT be instantiated directly.
It exists only to define an interface that child classes MUST implement.

If you try:
    searcher = BaseSearcher()  # ❌ TypeError!

You must use a child class:
    searcher = WikipediaSearcher()  # ✅ Works!
"""

from abc import ABC, abstractmethod
from typing import List
from models.schemas import SearchResult


class BaseSearcher(ABC):
    """
    Abstract base class for all search providers.

    Any class that extends BaseSearcher MUST implement the search() method.
    If it doesn't, Python will raise a TypeError when you try to create
    an instance of it.

    Usage:
        class MyNewSearcher(BaseSearcher):
            def search(self, query: str) -> List[SearchResult]:
                # Your search logic here
                ...
    """

    @abstractmethod
    def search(self, query: str) -> List[SearchResult]:
        """
        Search for the given query and return results.

        Args:
            query: The search query string (e.g., "quantum computing breakthroughs")

        Returns:
            A list of SearchResult objects containing the found information.

        Raises:
            SearchError: If the search fails (network error, API error, etc.)
        """
        pass

    def get_source_name(self) -> str:
        """
        Return the name of this search source.
        Override this in child classes for a custom name.
        """
        return self.__class__.__name__

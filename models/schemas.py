"""
schemas.py — Data Models (Schemas)
====================================
This module defines all the data structures used in the application.
Think of each dataclass as a "blueprint" that describes what shape
your data should have.

KEY CONCEPTS:
─────────────
1. DATACLASSES:
   Python's @dataclass decorator automatically generates __init__,
   __repr__, and other methods. Instead of writing boilerplate,
   you just declare your fields.

   WITHOUT dataclass:
       class SearchResult:
           def __init__(self, title, snippet, url, source):
               self.title = title
               self.snippet = snippet
               ...

   WITH dataclass:
       @dataclass
       class SearchResult:
           title: str
           snippet: str
           ...

2. TYPE HINTS:
   The ': str', ': int', etc. after field names are type hints.
   They don't enforce types at runtime, but they:
   - Help your IDE catch bugs
   - Make code self-documenting
   - Are used by tools like mypy for static analysis

3. SERIALIZATION:
   Converting Python objects to dictionaries/JSON so they can be
   sent over the network or saved to files. Our to_dict() methods
   handle this conversion.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class SearchResult:
    """
    Represents a single result from a search source.

    This is what comes back from Wikipedia or DuckDuckGo
    before being processed by the LLM.

    Fields:
        title:   The title of the search result (e.g., article name)
        snippet: A brief excerpt or summary of the content
        url:     The URL where the full content can be found
        source:  Which search engine found this ("wikipedia" or "duckduckgo")
    """
    title: str
    snippet: str
    url: str
    source: str  # "wikipedia" or "duckduckgo"

    def to_dict(self) -> dict:
        """Convert this SearchResult to a plain dictionary (for JSON)."""
        return {
            "title": self.title,
            "snippet": self.snippet,
            "url": self.url,
            "source": self.source,
        }


@dataclass
class Citation:
    """
    Represents a source citation in the final report.

    Citations are numbered references (like [1], [2]) that appear
    in the report text and link back to the original source.

    Fields:
        id:          Numeric ID used in the report text (e.g., [1])
        title:       Title of the source
        url:         URL of the source
        source:      Which search engine found this
        accessed_at: When this source was accessed (auto-set to now)
    """
    id: int
    title: str
    url: str
    source: str
    accessed_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Convert this Citation to a plain dictionary (for JSON)."""
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "accessed_at": self.accessed_at,
        }


@dataclass
class ReportSection:
    """
    Represents one section of the research report.

    The LLM breaks its answer into logical sections, each with
    a heading and content. citation_ids tracks which sources
    were used in this section.

    Fields:
        heading:      Section title (e.g., "Background", "Key Findings")
        content:      The text content with [1], [2] citation markers
        citation_ids: List of citation IDs referenced in this section
    """
    heading: str
    content: str
    citation_ids: List[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert this ReportSection to a plain dictionary (for JSON)."""
        return {
            "heading": self.heading,
            "content": self.content,
            "citation_ids": self.citation_ids,
        }


@dataclass
class ResearchReport:
    """
    The complete research report — the final output of the system.

    This is the top-level data structure that holds everything:
    the original question, the AI-generated summary, detailed
    sections, and all source citations.

    Fields:
        question:  The original research question from the user
        summary:   A brief overview of the findings
        sections:  List of detailed sections with citations
        citations: List of all sources cited in the report
        metadata:  Extra info (timestamp, sources searched, etc.)
    """
    question: str
    summary: str
    sections: List[ReportSection] = field(default_factory=list)
    citations: List[Citation] = field(default_factory=list)
    metadata: Optional[dict] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """
        Convert the entire report to a nested dictionary.

        This is the structure that gets serialized to JSON
        and sent to the frontend or printed to the terminal.
        """
        return {
            "question": self.question,
            "summary": self.summary,
            "sections": [section.to_dict() for section in self.sections],
            "citations": [citation.to_dict() for citation in self.citations],
            "metadata": self.metadata,
        }

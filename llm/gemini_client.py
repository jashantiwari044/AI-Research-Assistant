"""
gemini_client.py — Google Gemini LLM Integration
===================================================
This module handles all communication with Google's Gemini AI model.

KEY CONCEPTS:
─────────────
1. PROMPT ENGINEERING:
   The art of crafting instructions that make an LLM produce exactly
   the output format you want. A good prompt is like giving clear
   instructions to a very capable but literal assistant.

   Components of our prompt:
   - System prompt: Sets the AI's role and behavior rules
   - User prompt: The specific question + search results to analyze

2. STRUCTURED OUTPUT:
   We instruct Gemini to respond in a specific JSON format.
   This is critical because we need to PARSE the response
   programmatically (split it into sections, extract citations).

3. API AUTHENTICATION:
   The API key proves you're allowed to use the service.
   - Keys are loaded from environment variables (never hardcoded!)
   - Each key has usage limits (free tier: ~60 requests/minute)

4. TEMPERATURE:
   Controls the "creativity" of the AI's responses:
   - 0.0 = Very deterministic, always picks the most likely word
   - 0.5 = Balanced (we use this for research — factual but readable)
   - 1.0 = Very creative, more random word choices
"""

import json
from typing import List

from google import genai
from google.genai import types

from models.schemas import (
    SearchResult,
    ResearchReport,
    ReportSection,
    Citation,
)
from config import GEMINI_API_KEY, GEMINI_MODEL


# ── System Prompt ──────────────────────────────────────────────────
# This prompt is sent to Gemini with EVERY request. It defines:
# 1. What role the AI should play
# 2. What format the output should be in
# 3. Rules for citing sources
#
# IMPORTANT: The quality of your output depends heavily on this prompt.
# Tweaking these instructions is "prompt engineering" in action.
SYSTEM_PROMPT = """You are an expert research analyst. Your task is to synthesize 
information from provided search results into a well-structured research report.

RULES:
1. Use ONLY the information from the provided search results. Do NOT use your own knowledge.
2. Cite sources using [1], [2], etc. markers in the text where you use information from that source.
3. If the search results don't contain enough information to answer the question, say so honestly.
4. If sources contain conflicting information, mention both viewpoints and cite each.
5. Be concise but thorough. Every claim must have a citation.

OUTPUT FORMAT — You MUST respond with ONLY valid JSON in this exact structure:
{
    "summary": "A 2-3 sentence overview of the key findings",
    "sections": [
        {
            "heading": "Section Title",
            "content": "Detailed content with [1] citation markers...",
            "citation_ids": [1, 2]
        }
    ]
}

SECTION GUIDELINES:
- Create 2-5 sections depending on the topic complexity
- Each section should have a clear, descriptive heading
- Use citation markers [1], [2] etc. to reference sources
- The citation_ids array should list all citation numbers used in that section
- Aim for 3-6 sentences per section
"""


class GeminiClient:
    """
    Client for interacting with Google's Gemini AI model.

    This class handles:
    - Initializing the API connection
    - Building prompts from search results
    - Parsing structured responses from the LLM
    - Error handling for API failures

    Example:
        client = GeminiClient()
        report = client.synthesize(
            question="What is quantum computing?",
            search_results=[SearchResult(...), ...]
        )
        print(report.summary)
    """

    def __init__(self):
        """
        Initialize the Gemini API client.

        The client is configured with:
        - API key from environment variables
        - Model name (default: gemini-2.0-flash — fast and capable)
        """
        if not GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is not set! "
                "Get your free key at https://aistudio.google.com/apikey "
                "and add it to your .env file."
            )

        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = GEMINI_MODEL

    def synthesize(
        self, question: str, search_results: List[SearchResult]
    ) -> ResearchReport:
        """
        Synthesize search results into a structured research report.

        This is the core method of the LLM module. It:
        1. Builds a prompt from the search results
        2. Sends it to Gemini
        3. Parses the JSON response
        4. Returns a structured ResearchReport

        Args:
            question: The user's original research question
            search_results: List of SearchResult objects from the search module

        Returns:
            A ResearchReport with sections and citations

        Raises:
            Exception: If the API call fails or response can't be parsed
        """
        # ── Step 1: Build the user prompt ──────────────────────────
        # We format the search results into a readable list so the LLM
        # knows which sources are available and can cite them by number.
        user_prompt = self._build_prompt(question, search_results)

        # ── Step 2: Call the Gemini API ────────────────────────────
        print("  ⟳ Asking Gemini to synthesize findings...")

        candidate_models = [self.model]
        for fallback in ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.5-flash-lite", "gemini-3.8-flash"]:
            if fallback not in candidate_models:
                candidate_models.append(fallback)

        last_error = None
        raw_text = None

        for model_name in candidate_models:
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.5,           # Balanced: factual but readable
                        max_output_tokens=2048,    # Max length of the response
                    ),
                )
                raw_text = response.text
                self.model = model_name
                print(f"  ✓ Gemini response received (model: {model_name})")
                break
            except Exception as e:
                last_error = e
                err_str = str(e)
                # If deprecated model, high demand, or rate limit, try the next candidate
                if any(k in err_str for k in ["404", "503", "UNAVAILABLE", "NOT_FOUND", "ResourceExhausted", "429"]):
                    continue
                else:
                    raise Exception(f"Gemini API call failed: {err_str}")

        if raw_text is None:
            raise Exception(f"Gemini API call failed across models: {str(last_error)}")

        # ── Step 3: Parse the JSON response ────────────────────────
        report = self._parse_response(raw_text, question, search_results)

        return report

    def _build_prompt(
        self, question: str, search_results: List[SearchResult]
    ) -> str:
        """
        Build the user prompt from the question and search results.

        The prompt format is crucial for getting good output:
        - Clear question statement
        - Numbered source list (so the LLM can cite by number)
        - Each source includes title, URL, and content snippet

        Args:
            question: The research question
            search_results: List of search results to include

        Returns:
            Formatted prompt string
        """
        # Build the numbered source list
        sources_text = ""
        for i, result in enumerate(search_results, start=1):
            sources_text += (
                f"\n[{i}] Title: {result.title}\n"
                f"    Source: {result.source}\n"
                f"    URL: {result.url}\n"
                f"    Content: {result.snippet}\n"
            )

        prompt = (
            f"RESEARCH QUESTION: {question}\n\n"
            f"AVAILABLE SOURCES ({len(search_results)} found):\n"
            f"{sources_text}\n\n"
            f"Please analyze these sources and create a structured research "
            f"report answering the question. Remember to cite sources using "
            f"[1], [2], etc. and respond with ONLY valid JSON."
        )

        return prompt

    def _parse_response(
        self,
        raw_text: str,
        question: str,
        search_results: List[SearchResult],
    ) -> ResearchReport:
        """
        Parse Gemini's JSON response into a ResearchReport.

        LLMs don't always produce perfect JSON, so we need robust parsing:
        1. Try to parse as-is
        2. If that fails, try to extract JSON from markdown code blocks
        3. If all parsing fails, create a basic report from raw text

        Args:
            raw_text: Raw text response from Gemini
            question: The original question (for the report)
            search_results: Original search results (for building citations)

        Returns:
            A structured ResearchReport object
        """
        # ── Attempt to parse JSON ──────────────────────────────────
        parsed_data = None

        try:
            # Attempt 1: Direct JSON parse
            parsed_data = json.loads(raw_text)
        except json.JSONDecodeError:
            # Attempt 2: LLMs sometimes wrap JSON in ```json ... ```
            # Let's try to extract it
            try:
                # Find JSON between code fences
                if "```json" in raw_text:
                    json_str = raw_text.split("```json")[1].split("```")[0]
                    parsed_data = json.loads(json_str.strip())
                elif "```" in raw_text:
                    json_str = raw_text.split("```")[1].split("```")[0]
                    parsed_data = json.loads(json_str.strip())
                else:
                    # Attempt 3: Try to find JSON object in the text
                    start = raw_text.find("{")
                    end = raw_text.rfind("}") + 1
                    if start != -1 and end > start:
                        parsed_data = json.loads(raw_text[start:end])
            except (json.JSONDecodeError, IndexError):
                pass

        # ── Build the report ───────────────────────────────────────
        if parsed_data:
            return self._build_report_from_json(
                parsed_data, question, search_results
            )
        else:
            # Fallback: If we can't parse JSON, wrap raw text in a report
            print("  ⚠ Could not parse JSON from Gemini — using raw text")
            return self._build_fallback_report(raw_text, question, search_results)

    def _build_report_from_json(
        self,
        data: dict,
        question: str,
        search_results: List[SearchResult],
    ) -> ResearchReport:
        """
        Build a ResearchReport from successfully parsed JSON.

        Args:
            data: Parsed JSON dictionary from Gemini
            question: The original question
            search_results: Original search results for building citations

        Returns:
            A structured ResearchReport
        """
        # Build sections from the parsed data
        sections = []
        for section_data in data.get("sections", []):
            section = ReportSection(
                heading=section_data.get("heading", "Untitled Section"),
                content=section_data.get("content", ""),
                citation_ids=section_data.get("citation_ids", []),
            )
            sections.append(section)

        # Build citations from the search results
        citations = []
        for i, result in enumerate(search_results, start=1):
            citation = Citation(
                id=i,
                title=result.title,
                url=result.url,
                source=result.source,
            )
            citations.append(citation)

        # Build metadata
        from datetime import datetime
        metadata = {
            "generated_at": datetime.now().isoformat(),
            "model": self.model,
            "sources_searched": list(set(r.source for r in search_results)),
            "total_sources_found": len(search_results),
        }

        return ResearchReport(
            question=question,
            summary=data.get("summary", "No summary available."),
            sections=sections,
            citations=citations,
            metadata=metadata,
        )

    def _build_fallback_report(
        self,
        raw_text: str,
        question: str,
        search_results: List[SearchResult],
    ) -> ResearchReport:
        """
        Build a basic report when JSON parsing fails.

        This is our "graceful degradation" — even if the LLM doesn't
        return perfect JSON, we still give the user something useful.

        Args:
            raw_text: The raw text from Gemini
            question: The original question
            search_results: Original search results

        Returns:
            A basic ResearchReport with the raw text as content
        """
        # Create a single section with the raw text
        sections = [
            ReportSection(
                heading="Research Findings",
                content=raw_text,
                citation_ids=list(range(1, len(search_results) + 1)),
            )
        ]

        # Build citations from search results
        citations = [
            Citation(
                id=i,
                title=r.title,
                url=r.url,
                source=r.source,
            )
            for i, r in enumerate(search_results, start=1)
        ]

        from datetime import datetime
        metadata = {
            "generated_at": datetime.now().isoformat(),
            "model": self.model,
            "sources_searched": list(set(r.source for r in search_results)),
            "total_sources_found": len(search_results),
            "note": "Response was not valid JSON — raw text used",
        }

        return ResearchReport(
            question=question,
            summary="See the findings section below for details.",
            sections=sections,
            citations=citations,
            metadata=metadata,
        )

"""
main.py — CLI Entry Point & Research Pipeline Orchestrator
============================================================
This is the heart of the application. It ties everything together:
Input → Validate → Search → Synthesize → Format → Output

KEY CONCEPTS:
─────────────
1. ARGPARSE — Command Line Argument Parsing:
   Python's built-in module for creating CLI interfaces.
   It automatically generates --help text, validates arguments,
   and provides a clean API for accessing user input.

   Example usage:
       python main.py --question "What is quantum computing?"
       python main.py -q "What is AI?" --output json --sources wiki

2. THE PIPELINE PATTERN:
   Data flows through a series of processing stages, each
   transforming it. Like an assembly line:
       Raw Question → Validated Question → Search Results →
       LLM Synthesis → Formatted Report → Display

3. ORCHESTRATION:
   This module doesn't DO the work — it COORDINATES the modules
   that do the work. It's like a conductor leading an orchestra:
   it tells the search module when to play, then the LLM module,
   then the formatter.
"""

import argparse
import sys

from search.wikipedia_search import WikipediaSearcher
from search.web_search import WebSearcher
from llm.gemini_client import GeminiClient
from utils.formatter import format_as_json, format_as_markdown, format_as_terminal
from utils.error_handler import (
    validate_question,
    ValidationError,
    SearchError,
    LLMError,
    ResearchAssistantError,
)


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create and configure the CLI argument parser.

    argparse.ArgumentParser handles:
    - Parsing command-line arguments
    - Generating --help documentation
    - Validating argument types and choices
    - Providing default values

    Returns:
        Configured ArgumentParser ready to parse arguments
    """
    parser = argparse.ArgumentParser(
        # ── Program Info ───────────────────────────────────────────
        prog="AI Research Assistant",
        description=(
            "🔬 AI Research Assistant — Ask a research question and get "
            "a structured answer with citations from multiple sources."
        ),
        epilog=(
            "Examples:\n"
            '  python main.py -q "What is quantum computing?"\n'
            '  python main.py -q "Latest AI breakthroughs" --output json\n'
            '  python main.py -q "Climate change effects" --sources wiki\n'
        ),
        # RawDescriptionHelpFormatter preserves our formatting in --help
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # ── Required Arguments ─────────────────────────────────────────
    parser.add_argument(
        "-q", "--question",
        type=str,
        required=True,
        help="The research question to investigate",
    )

    # ── Optional Arguments ─────────────────────────────────────────
    parser.add_argument(
        "-o", "--output",
        type=str,
        choices=["terminal", "json", "markdown"],
        default="terminal",
        help="Output format (default: terminal)",
    )

    parser.add_argument(
        "-s", "--sources",
        type=str,
        choices=["all", "wiki", "web"],
        default="all",
        help="Which sources to search (default: all)",
    )

    return parser


def run_research_pipeline(question: str, output_format: str, sources: str) -> None:
    """
    Execute the full research pipeline.

    This is the main orchestration function. It runs each stage
    of the pipeline in order, with error handling at each step.

    Pipeline stages:
    1. VALIDATE — Check the question is valid
    2. SEARCH — Query Wikipedia and/or DuckDuckGo
    3. SYNTHESIZE — Send results to Gemini for analysis
    4. FORMAT — Convert report to the requested format
    5. OUTPUT — Display the result

    Args:
        question: The user's research question
        output_format: How to format the output ("terminal", "json", "markdown")
        sources: Which sources to search ("all", "wiki", "web")
    """
    print("\n🔬 AI Research Assistant")
    print("=" * 40)

    # ── Stage 1: VALIDATE ──────────────────────────────────────────
    print("\n📝 Step 1: Validating question...")
    try:
        cleaned_question = validate_question(question)
        print(f'  ✓ Question: "{cleaned_question}"')
    except ValidationError as e:
        print(f"  ✗ {str(e)}")
        sys.exit(1)

    # ── Stage 2: SEARCH ────────────────────────────────────────────
    print("\n🔍 Step 2: Searching sources...")
    all_results = []

    # Choose which searchers to use based on --sources flag
    searchers = []
    if sources in ("all", "wiki"):
        searchers.append(WikipediaSearcher())
    if sources in ("all", "web"):
        searchers.append(WebSearcher())

    # Run each searcher and collect results
    # NOTE: We don't stop if one fails — graceful degradation!
    for searcher in searchers:
        try:
            results = searcher.search(cleaned_question)
            all_results.extend(results)
        except Exception as e:
            print(f"  ⚠ {searcher.get_source_name()} search failed: {str(e)}")
            print("    Continuing with other sources...")

    # Check if we found anything at all
    if not all_results:
        print("\n  ✗ No results found from any source.")
        print("  Try rephrasing your question or using different search sources.")
        sys.exit(1)

    print(f"\n  📊 Total results collected: {len(all_results)}")

    # ── Stage 3: SYNTHESIZE ────────────────────────────────────────
    print("\n🤖 Step 3: Synthesizing with AI...")
    try:
        llm_client = GeminiClient()
        report = llm_client.synthesize(cleaned_question, all_results)
        print("  ✓ Report generated successfully!")
    except Exception as e:
        print(f"\n  ✗ LLM synthesis failed: {str(e)}")
        print("  Make sure your GEMINI_API_KEY is set in the .env file.")
        sys.exit(1)

    # ── Stage 4 & 5: FORMAT & OUTPUT ───────────────────────────────
    print(f"\n📄 Step 4: Formatting as {output_format}...")

    # Choose the right formatter based on --output flag
    # This is like a simple factory pattern
    formatters = {
        "json": format_as_json,
        "markdown": format_as_markdown,
        "terminal": format_as_terminal,
    }

    formatter = formatters[output_format]
    formatted_output = formatter(report)

    # Display the result
    print(formatted_output)


def main():
    """
    Main entry point — parses arguments and starts the pipeline.

    This is what runs when you type: python main.py -q "your question"
    """
    parser = create_argument_parser()
    args = parser.parse_args()

    try:
        run_research_pipeline(
            question=args.question,
            output_format=args.output,
            sources=args.sources,
        )
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\n\n⚠ Research cancelled by user.")
        sys.exit(0)
    except ResearchAssistantError as e:
        # Catch any of our custom exceptions
        print(f"\n✗ Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        # Catch truly unexpected errors
        print(f"\n✗ Unexpected error: {str(e)}")
        print("  Please report this issue on GitHub.")
        sys.exit(1)


# ── This runs only when you execute the file directly ──────────────
# NOT when you import it as a module. This is a Python convention.
if __name__ == "__main__":
    main()

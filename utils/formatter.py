"""
formatter.py — Output Formatters
===================================
This module handles converting a ResearchReport into different
output formats: JSON, Markdown, and colorized terminal output.

KEY CONCEPTS:
─────────────
1. SEPARATION OF CONCERNS:
   The report data (ResearchReport) is separate from how it's displayed.
   This means we can add new formats (HTML, PDF, etc.) without changing
   the data model or the LLM module.

2. JSON (JavaScript Object Notation):
   A text format for structured data. Used everywhere in web development.
   Example: {"key": "value", "items": [1, 2, 3]}

3. MARKDOWN:
   A lightweight text format that uses symbols for formatting:
   # Heading    **bold**    - bullet    [link](url)

4. ANSI ESCAPE CODES:
   Special character sequences that terminals interpret as formatting
   instructions (colors, bold, etc.). They start with \\033[
   Example: \\033[1;34m makes text bold blue.
"""

import json
from models.schemas import ResearchReport


# ── ANSI Color Codes ───────────────────────────────────────────────
# These are escape sequences that tell the terminal to change text color.
# They work on macOS/Linux terminals and modern Windows terminals.
# Format: \033[<code>m   where <code> controls the style.
class Colors:
    """Terminal color codes for pretty output."""
    HEADER = "\033[95m"       # Magenta — for headers
    BLUE = "\033[94m"         # Blue — for section titles
    CYAN = "\033[96m"         # Cyan — for citations
    GREEN = "\033[92m"        # Green — for success messages
    YELLOW = "\033[93m"       # Yellow — for warnings
    RED = "\033[91m"          # Red — for errors
    BOLD = "\033[1m"          # Bold text
    DIM = "\033[2m"           # Dimmed text
    UNDERLINE = "\033[4m"     # Underlined text
    RESET = "\033[0m"         # Reset to default — ALWAYS use after coloring!


def format_as_json(report: ResearchReport) -> str:
    """
    Format the report as pretty-printed JSON.

    json.dumps() converts a Python dictionary to a JSON string.
    Parameters:
        indent=2:         Add 2-space indentation for readability
        ensure_ascii=False: Allow unicode characters (accents, emojis)

    Args:
        report: The ResearchReport to format

    Returns:
        A pretty-printed JSON string
    """
    return json.dumps(report.to_dict(), indent=2, ensure_ascii=False)


def format_as_markdown(report: ResearchReport) -> str:
    """
    Format the report as a Markdown document.

    Markdown is a lightweight markup language that's easy to read
    as plain text AND can be rendered as formatted HTML.

    Args:
        report: The ResearchReport to format

    Returns:
        A Markdown-formatted string
    """
    lines = []

    # ── Title ──────────────────────────────────────────────────────
    lines.append(f"# Research Report")
    lines.append("")
    lines.append(f"**Question:** {report.question}")
    lines.append("")

    # ── Summary ────────────────────────────────────────────────────
    lines.append("## Summary")
    lines.append("")
    lines.append(report.summary)
    lines.append("")

    # ── Sections ───────────────────────────────────────────────────
    for section in report.sections:
        lines.append(f"## {section.heading}")
        lines.append("")
        lines.append(section.content)
        lines.append("")

    # ── Citations ──────────────────────────────────────────────────
    if report.citations:
        lines.append("## Sources")
        lines.append("")
        for citation in report.citations:
            lines.append(
                f"- **[{citation.id}]** [{citation.title}]({citation.url}) "
                f"*({citation.source})*"
            )
        lines.append("")

    # ── Metadata ───────────────────────────────────────────────────
    if report.metadata:
        lines.append("---")
        lines.append(
            f"*Generated at: {report.metadata.get('generated_at', 'N/A')} | "
            f"Model: {report.metadata.get('model', 'N/A')} | "
            f"Sources found: {report.metadata.get('total_sources_found', 0)}*"
        )

    return "\n".join(lines)


def format_as_terminal(report: ResearchReport) -> str:
    """
    Format the report with ANSI colors for terminal display.

    This produces the most visually appealing output when using
    the CLI. Colors help distinguish headers, content, and citations.

    Args:
        report: The ResearchReport to format

    Returns:
        A colorized string for terminal output
    """
    c = Colors  # Shorthand for readability
    lines = []

    # ── Header ─────────────────────────────────────────────────────
    lines.append("")
    lines.append(f"{c.BOLD}{c.HEADER}{'═' * 60}{c.RESET}")
    lines.append(f"{c.BOLD}{c.HEADER}  🔬 RESEARCH REPORT{c.RESET}")
    lines.append(f"{c.BOLD}{c.HEADER}{'═' * 60}{c.RESET}")
    lines.append("")

    # ── Question ───────────────────────────────────────────────────
    lines.append(f"{c.BOLD}Question:{c.RESET} {report.question}")
    lines.append("")

    # ── Summary ────────────────────────────────────────────────────
    lines.append(f"{c.BOLD}{c.GREEN}📋 Summary{c.RESET}")
    lines.append(f"{c.DIM}{'─' * 40}{c.RESET}")
    lines.append(report.summary)
    lines.append("")

    # ── Sections ───────────────────────────────────────────────────
    for section in report.sections:
        lines.append(f"{c.BOLD}{c.BLUE}📌 {section.heading}{c.RESET}")
        lines.append(f"{c.DIM}{'─' * 40}{c.RESET}")
        lines.append(section.content)
        lines.append("")

    # ── Citations ──────────────────────────────────────────────────
    if report.citations:
        lines.append(f"{c.BOLD}{c.CYAN}📚 Sources{c.RESET}")
        lines.append(f"{c.DIM}{'─' * 40}{c.RESET}")
        for citation in report.citations:
            lines.append(
                f"  {c.CYAN}[{citation.id}]{c.RESET} {citation.title}"
            )
            lines.append(
                f"      {c.DIM}{citation.url}{c.RESET}"
            )
            lines.append(
                f"      {c.DIM}Source: {citation.source}{c.RESET}"
            )
        lines.append("")

    # ── Footer ─────────────────────────────────────────────────────
    lines.append(f"{c.DIM}{'═' * 60}{c.RESET}")
    if report.metadata:
        lines.append(
            f"{c.DIM}Generated: {report.metadata.get('generated_at', 'N/A')} | "
            f"Model: {report.metadata.get('model', 'N/A')} | "
            f"Sources: {report.metadata.get('total_sources_found', 0)}{c.RESET}"
        )
    lines.append("")

    return "\n".join(lines)

"""
app.py — Flask Web Server
============================
This module creates a web interface for the AI Research Assistant.

KEY CONCEPTS:
─────────────
1. FLASK — A Micro Web Framework:
   Flask is a lightweight Python web framework. "Micro" means it
   gives you just the essentials — routing, templates, request handling.
   Perfect for learning without overwhelming complexity.

2. ROUTES:
   A route maps a URL to a Python function.
   @app.route("/")       → when someone visits http://localhost:5000/
   @app.route("/api/..") → when the frontend sends an API request

3. HTTP METHODS:
   - GET:  "Give me data" (loading a page)
   - POST: "Here's some data, process it" (submitting a form)

4. REQUEST/RESPONSE CYCLE:
   Browser sends request → Flask calls your function → 
   Your function returns a response → Browser displays it

5. JSON API:
   Instead of returning HTML, our /api/research endpoint returns
   JSON data. The frontend JavaScript fetches this data and
   builds the HTML dynamically. This is how modern web apps work!
"""

from flask import Flask, render_template, request, jsonify

from search.wikipedia_search import WikipediaSearcher
from search.web_search import WebSearcher
from llm.gemini_client import GeminiClient
from utils.error_handler import validate_question, ValidationError
from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG


# ── Create the Flask App ───────────────────────────────────────────
# __name__ tells Flask where to find templates and static files.
# It uses the location of THIS file as the base directory.
app = Flask(__name__)


@app.route("/")
def index():
    """
    Serve the main page.

    render_template() loads templates/index.html and returns it.
    Flask automatically looks in the 'templates/' directory.
    """
    return render_template("index.html")


@app.route("/api/research", methods=["POST"])
def research():
    """
    API endpoint that processes a research question.

    This is called by the frontend JavaScript via fetch().
    
    Flow:
    1. Receive JSON with { "question": "...", "sources": "all" }
    2. Validate the question
    3. Search external sources
    4. Synthesize with Gemini
    5. Return the report as JSON

    Returns:
        JSON response with the research report, or an error message
    """
    try:
        # ── Step 1: Get the request data ───────────────────────────
        # request.get_json() parses the JSON body from the POST request
        data = request.get_json()

        if not data or "question" not in data:
            return jsonify({"error": "Please provide a 'question' field"}), 400

        question = data["question"]
        sources = data.get("sources", "all")  # Default to searching all

        # ── Step 2: Validate ───────────────────────────────────────
        cleaned_question = validate_question(question)

        # ── Step 3: Search ─────────────────────────────────────────
        all_results = []

        searchers = []
        if sources in ("all", "wiki"):
            searchers.append(WikipediaSearcher())
        if sources in ("all", "web"):
            searchers.append(WebSearcher())

        for searcher in searchers:
            try:
                results = searcher.search(cleaned_question)
                all_results.extend(results)
            except Exception as e:
                print(f"Search error ({searcher.get_source_name()}): {e}")

        if not all_results:
            return jsonify({
                "error": "No results found from any source. Try rephrasing your question."
            }), 404

        # ── Step 4: Synthesize ─────────────────────────────────────
        llm_client = GeminiClient()
        report = llm_client.synthesize(cleaned_question, all_results)

        # ── Step 5: Return as JSON ─────────────────────────────────
        return jsonify(report.to_dict())

    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


# ── Run the Server ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("🔬 AI Research Assistant — Web Interface")
    print(f"   Open http://{FLASK_HOST}:{FLASK_PORT} in your browser")
    print("   Press Ctrl+C to stop the server\n")
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)

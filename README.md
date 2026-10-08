# 🔬 AI Research Assistant

An intelligent research tool that accepts a research question, searches external sources (Wikipedia + Web), and uses Google Gemini AI to produce a **structured answer with citations**.

Built as a learning project to understand APIs, LLMs, prompt engineering, and full-stack development.

---

## ✨ Features

- **Multi-Source Search** — Searches Wikipedia and DuckDuckGo simultaneously
- **AI-Powered Synthesis** — Google Gemini analyzes and synthesizes findings
- **Structured Output** — Reports have sections, summaries, and numbered citations
- **Multiple Output Formats** — Terminal (colorized), JSON, and Markdown
- **Web UI** — Beautiful, responsive dark-themed interface
- **CLI Interface** — Full command-line support with argument parsing
- **Error Handling** — Graceful degradation when sources fail
- **Source Citations** — Every claim is backed by a clickable source

---

## 🏗️ Architecture

```
User Question
    ↓
Input Validation
    ↓
Parallel Search (Wikipedia + DuckDuckGo)
    ↓
Result Aggregation
    ↓
LLM Synthesis (Google Gemini)
    ↓
Output Formatting (Terminal / JSON / Markdown)
    ↓
Display Result
```

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/jashantiwari044/AI-Research-Assistant.git
cd AI-Research-Assistant
```

### 2. Set Up Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Key

```bash
cp .env.example .env
```

Open `.env` and add your Google Gemini API key:

```
GEMINI_API_KEY=your_actual_api_key_here
```

> 🔑 Get your free API key at [Google AI Studio](https://aistudio.google.com/apikey)

### 5. Run the Application

**CLI Mode:**

```bash
python main.py -q "What are the latest breakthroughs in quantum computing?"
```

**Web UI Mode:**

```bash
python app.py
# Open http://127.0.0.1:5000 in your browser
```

---

## 📖 CLI Usage

```bash
# Basic usage
python main.py -q "Your research question here"

# Output as JSON
python main.py -q "What is machine learning?" --output json

# Output as Markdown
python main.py -q "History of the internet" --output markdown

# Search only Wikipedia
python main.py -q "Quantum entanglement" --sources wiki

# Search only the web
python main.py -q "Latest AI news 2026" --sources web

# See all options
python main.py --help
```

---

## 📁 Project Structure

```
AI-Research-Assistant/
├── main.py                 # CLI entry point & pipeline orchestrator
├── app.py                  # Flask web server
├── config.py               # Centralized configuration
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
│
├── search/                 # Search module
│   ├── base.py             # Abstract base class (Strategy pattern)
│   ├── wikipedia_search.py # Wikipedia API integration
│   └── web_search.py       # DuckDuckGo search integration
│
├── llm/                    # LLM module
│   └── gemini_client.py    # Google Gemini client & prompt engineering
│
├── models/                 # Data models
│   └── schemas.py          # Dataclasses (SearchResult, Report, Citation)
│
├── utils/                  # Utilities
│   ├── error_handler.py    # Custom exceptions & validation
│   └── formatter.py        # Output formatters (JSON, Markdown, Terminal)
│
├── templates/              # Flask HTML templates
│   └── index.html          # Web UI page
│
└── static/                 # Frontend assets
    ├── style.css           # Dark theme styles
    └── script.js           # Frontend JavaScript logic
```

---

## 🧠 Key Concepts Covered

| Concept | Where It's Used |
|---------|----------------|
| **Dataclasses & Type Hints** | `models/schemas.py` |
| **Abstract Base Classes** | `search/base.py` |
| **Strategy Design Pattern** | `search/` module |
| **REST API Integration** | `search/wikipedia_search.py` |
| **Web Scraping** | `search/web_search.py` |
| **Prompt Engineering** | `llm/gemini_client.py` |
| **JSON Parsing** | `llm/gemini_client.py` |
| **Custom Exceptions** | `utils/error_handler.py` |
| **CLI with argparse** | `main.py` |
| **Flask Web Framework** | `app.py` |
| **Fetch API (JavaScript)** | `static/script.js` |
| **DOM Manipulation** | `static/script.js` |
| **CSS Custom Properties** | `static/style.css` |
| **Responsive Design** | `static/style.css` |

---

## 🔑 API Keys

| API | Required | How to Get |
|-----|----------|-----------|
| **Google Gemini** | ✅ Yes | [Google AI Studio](https://aistudio.google.com/apikey) (Free tier) |
| **DuckDuckGo** | ❌ No | No key needed |
| **Wikipedia** | ❌ No | No key needed |

---

## 🛠️ Tech Stack

- **Python 3.11+** — Core language
- **Google Gemini API** — LLM for research synthesis
- **wikipedia-api** — Wikipedia search
- **duckduckgo-search** — Web search
- **Flask** — Web server
- **HTML/CSS/JavaScript** — Frontend

---

## 📜 License

This project is built for educational purposes.
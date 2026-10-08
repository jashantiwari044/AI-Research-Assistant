/**
 * script.js — Frontend Logic
 * ============================
 * Handles form submission, API calls, and dynamic DOM updates.
 *
 * KEY CONCEPTS:
 * ─────────────
 * 1. EVENT LISTENERS:
 *    We "listen" for user actions (like clicking a button) and run
 *    code when they happen. This is event-driven programming.
 *
 * 2. FETCH API:
 *    The modern way to make HTTP requests from JavaScript.
 *    fetch() sends a request and returns a Promise.
 *
 * 3. PROMISES & ASYNC/AWAIT:
 *    Since API calls take time, JavaScript uses Promises to handle
 *    asynchronous operations. async/await makes them readable:
 *        const response = await fetch(url);  // waits for response
 *        const data = await response.json(); // waits for parsing
 *
 * 4. DOM MANIPULATION:
 *    The DOM (Document Object Model) is the browser's representation
 *    of the HTML. We use JavaScript to dynamically add, remove, and
 *    modify elements based on the API response.
 */

// ── DOM Element References ────────────────────────────────────────
// document.getElementById() finds an HTML element by its id attribute.
// We grab references once and reuse them (more efficient than searching each time).
const form = document.getElementById("research-form");
const questionInput = document.getElementById("question-input");
const searchBtn = document.getElementById("search-btn");
const loadingDiv = document.getElementById("loading");
const errorDiv = document.getElementById("error");
const errorMessage = document.getElementById("error-message");
const resultsDiv = document.getElementById("results");

// Loading step elements
const stepValidate = document.getElementById("step-validate");
const stepSearch = document.getElementById("step-search");
const stepSynthesize = document.getElementById("step-synthesize");
const stepFormat = document.getElementById("step-format");


// ── Form Submission Handler ───────────────────────────────────────
// addEventListener("submit", ...) runs our function when the form is submitted.
// "async" makes this function support await (for the API call).
form.addEventListener("submit", async (event) => {
    // preventDefault() stops the browser from reloading the page
    // (the default behavior when a form is submitted).
    event.preventDefault();

    const question = questionInput.value.trim();
    if (!question) return;

    // Get selected source option
    const sourcesRadio = document.querySelector('input[name="sources"]:checked');
    const sources = sourcesRadio ? sourcesRadio.value : "all";

    // ── Show loading, hide others ─────────────────────────────────
    showLoading();
    hideError();
    hideResults();
    disableForm();

    // ── Animate loading steps ─────────────────────────────────────
    await animateStep(stepValidate, 400);
    await animateStep(stepSearch, 600);
    await animateStep(stepSynthesize, 0);  // This one stays active until response

    try {
        // ── Make the API call ─────────────────────────────────────
        // fetch() sends an HTTP request to our Flask backend.
        // We use POST because we're sending data (the question).
        const response = await fetch("/api/research", {
            method: "POST",
            headers: {
                // Tell the server we're sending JSON data
                "Content-Type": "application/json",
            },
            // JSON.stringify() converts our JS object to a JSON string
            body: JSON.stringify({
                question: question,
                sources: sources,
            }),
        });

        // ── Parse the response ────────────────────────────────────
        // response.json() parses the JSON body into a JS object
        const data = await response.json();

        // Check if the response indicates an error
        if (!response.ok) {
            throw new Error(data.error || "An unexpected error occurred");
        }

        // ── Mark synthesis as done ────────────────────────────────
        markStepDone(stepSynthesize);
        await animateStep(stepFormat, 300);

        // ── Display the results ───────────────────────────────────
        displayResults(data);

    } catch (error) {
        // ── Handle errors ─────────────────────────────────────────
        showError(error.message);
    } finally {
        // ── Always run this (success or error) ────────────────────
        hideLoading();
        enableForm();
    }
});


// ── Display Results ───────────────────────────────────────────────
function displayResults(report) {
    /**
     * Take the report JSON and build HTML elements to display it.
     * This is DOM manipulation — creating elements with JavaScript
     * and inserting them into the page.
     */

    // Set the question
    document.getElementById("result-question-text").textContent = report.question;

    // Set the summary
    document.getElementById("result-summary").textContent = report.summary;

    // ── Build section cards ───────────────────────────────────────
    const sectionsContainer = document.getElementById("result-sections");
    sectionsContainer.innerHTML = ""; // Clear any previous results

    if (report.sections && report.sections.length > 0) {
        report.sections.forEach((section) => {
            const card = createSectionCard(section);
            sectionsContainer.appendChild(card);
        });
    }

    // ── Build citations list ──────────────────────────────────────
    const citationsContainer = document.getElementById("result-citations");
    citationsContainer.innerHTML = "";

    if (report.citations && report.citations.length > 0) {
        report.citations.forEach((citation) => {
            const item = createCitationItem(citation);
            citationsContainer.appendChild(item);
        });
    }

    // ── Build metadata ────────────────────────────────────────────
    const metaDiv = document.getElementById("result-metadata");
    if (report.metadata) {
        const generated = report.metadata.generated_at
            ? new Date(report.metadata.generated_at).toLocaleString()
            : "N/A";
        metaDiv.textContent = `Generated: ${generated} · Model: ${report.metadata.model || "N/A"} · Sources found: ${report.metadata.total_sources_found || 0}`;
    }

    // Show the results section
    showResults();
}


// ── Create Section Card ───────────────────────────────────────────
function createSectionCard(section) {
    /**
     * Creates an HTML card element for a report section.
     * Uses createElement() instead of innerHTML for security
     * (prevents XSS attacks from injected content).
     */
    const card = document.createElement("div");
    card.className = "result-card section-card";

    const header = document.createElement("div");
    header.className = "card-header";

    const icon = document.createElement("span");
    icon.className = "card-icon";
    icon.textContent = "📌";

    const title = document.createElement("h3");
    title.textContent = section.heading;

    header.appendChild(icon);
    header.appendChild(title);

    const content = document.createElement("div");
    content.className = "section-content";
    // Process citation markers [1], [2] etc. into clickable spans
    content.innerHTML = processCitationMarkers(section.content);

    card.appendChild(header);
    card.appendChild(content);

    return card;
}


// ── Create Citation Item ──────────────────────────────────────────
function createCitationItem(citation) {
    /**
     * Creates an HTML element for a single citation in the sources list.
     */
    const item = document.createElement("div");
    item.className = "citation-item";
    item.id = `citation-${citation.id}`;

    const idBadge = document.createElement("span");
    idBadge.className = "citation-id";
    idBadge.textContent = citation.id;

    const info = document.createElement("div");
    info.className = "citation-info";

    const title = document.createElement("div");
    title.className = "citation-title";
    title.textContent = citation.title;

    const url = document.createElement("a");
    url.className = "citation-url";
    url.href = citation.url;
    url.target = "_blank";         // Open in new tab
    url.rel = "noopener noreferrer"; // Security best practice
    url.textContent = citation.url;

    const source = document.createElement("span");
    source.className = "citation-source";
    source.textContent = citation.source;

    info.appendChild(title);
    info.appendChild(url);
    info.appendChild(source);

    item.appendChild(idBadge);
    item.appendChild(info);

    return item;
}


// ── Process Citation Markers ──────────────────────────────────────
function processCitationMarkers(text) {
    /**
     * Converts [1], [2] etc. in the text to clickable citation links.
     *
     * Uses a regular expression to find all [number] patterns:
     * - \[  : literal opening bracket
     * - (\d+): capture one or more digits
     * - \]  : literal closing bracket
     *
     * replace() with a function lets us build custom HTML for each match.
     */
    return text.replace(/\[(\d+)\]/g, (match, num) => {
        return `<a href="#citation-${num}" class="citation-marker" title="Go to source ${num}">${num}</a>`;
    });
}


// ── Loading Step Animation ────────────────────────────────────────
function animateStep(stepElement, delay) {
    /**
     * Animates a loading step: marks it as "active", waits,
     * then marks it as "done" with a checkmark.
     *
     * Returns a Promise that resolves after the delay,
     * allowing us to use await for sequential animations.
     */
    return new Promise((resolve) => {
        stepElement.classList.add("active");
        stepElement.querySelector(".step-icon").textContent = "⟳";

        if (delay > 0) {
            setTimeout(() => {
                markStepDone(stepElement);
                resolve();
            }, delay);
        } else {
            resolve();
        }
    });
}

function markStepDone(stepElement) {
    stepElement.classList.remove("active");
    stepElement.classList.add("done");
    stepElement.querySelector(".step-icon").textContent = "✓";
}


// ── UI State Helpers ──────────────────────────────────────────────
// These small functions manage showing/hiding UI sections.
// Keeping them separate makes the code more readable.

function showLoading() {
    loadingDiv.classList.remove("hidden");
    // Reset all steps
    [stepValidate, stepSearch, stepSynthesize, stepFormat].forEach((step) => {
        step.classList.remove("active", "done");
        step.querySelector(".step-icon").textContent = "⏳";
    });
}

function hideLoading() {
    loadingDiv.classList.add("hidden");
}

function showError(message) {
    errorMessage.textContent = message;
    errorDiv.classList.remove("hidden");
}

function hideError() {
    errorDiv.classList.add("hidden");
}

function showResults() {
    resultsDiv.classList.remove("hidden");
}

function hideResults() {
    resultsDiv.classList.add("hidden");
}

function disableForm() {
    searchBtn.disabled = true;
    questionInput.disabled = true;
    searchBtn.querySelector(".btn-text").textContent = "Researching...";
}

function enableForm() {
    searchBtn.disabled = false;
    questionInput.disabled = false;
    searchBtn.querySelector(".btn-text").textContent = "Research";
}

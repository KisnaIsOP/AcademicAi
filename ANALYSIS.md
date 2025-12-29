# Analysis of AcademicAi (Hecker)

## Overview
**Hecker** is an AI-powered learning companion designed to assist students with their studies. It leverages Google's Gemini Pro model to provide personalized explanations, with a strong focus on mathematical notation and scientific concepts.

## Architecture
- **Backend:** Python (Flask)
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **AI Engine:** Google Gemini Pro (`google-generativeai`)
- **Deployment:** Configured for platforms like Render (includes `Procfile` and keep-alive scripts).

## Key Features

### 1. AI Learning Companion
- **Persona:** "Hecker" - a patient, encouraging, and adaptable tutor.
- **Context Awareness:** The backend maintains a `ConversationContext` class that tracks:
    - Conversation history (last 5 interactions).
    - Current topic (Math, Science, Language, etc.).
    - Difficulty level (Beginner vs. Advanced).
- **Specialized Handling:** Includes specific logic for "Dimensional Analysis" queries, providing a structured, hardcoded response for demonstration or reliability purposes.

### 2. Advanced Math & Science Rendering
- **Backend:** `format_mathematical_notation` function standardizes symbols (e.g., converting `*` to `×`, `**` to `^`) and wraps equations in HTML classes.
- **Frontend:** 
    - Uses **MathJax** for rendering LaTeX equations.
    - Custom regex parsing in `script.js` to format steps, definitions, examples, and key points.
    - Supports symbolic representation (e.g., viscosity η, shear stress τ).

### 3. User Interface & Experience
- **Voice Input:** Integrated Web Speech API for voice-to-text functionality.
- **Theming:** Toggleable Light/Dark mode with persistence via `localStorage`.
- **Engagement Tools:** (Hidden by default in UI)
    - Journal Entry
    - Gratitude List
    - Mindfulness Timer
- **Custom Cursor:** A "glow" effect follows the mouse cursor.

### 4. Reliability
- **Keep-Alive Mechanism:** 
    - **Backend:** A background thread (`keep_alive`) pings the server URL every 5 minutes.
    - **Frontend:** A JavaScript interval pings `/ping` (though the route isn't explicitly defined in the provided `app.py`, which might cause 404s in the console).

## Setup Requirements
1. **Python 3.8+**
2. **Google Gemini API Key** (set in `.env` as `GEMINI_API_KEY`)
3. **Dependencies:** `flask`, `google-generativeai`, `python-dotenv`, `gunicorn`, `requests`

## Code Observations
- **Hardcoded Logic:** The `app.py` contains a specific hardcoded response for "dimensional analysis of viscosity" to ensure a perfect output for that complex query.
- **Frontend Logic:** The `script.js` handles a lot of the formatting heavy lifting, converting raw text into structured HTML (steps, definitions, examples).
- **Easter Eggs:** The AI persona is named "Hecker", and the footer credits "Kisna".

## Potential Issues
- **Missing Route:** The frontend tries to ping `/ping` to keep the server alive, but this route is not defined in `app.py`.
- **Hardcoded URLs:** The `keep_alive` function in `app.py` pings specific Render URLs (`hecker-ai.onrender.com`, etc.) which might not match your deployment.

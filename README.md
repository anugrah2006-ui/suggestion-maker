# Suggestion Maker (Gemini API)

A tiny web app to generate suggestions (ideas, tips, names, etc.) using Google's Gemini models.

## Features
- Clean single-page UI
- Choose how many suggestions to generate
- Optional tone and category helpers
- FastAPI backend calling Gemini (`gemini-1.5-flash` by default)
- Safe: API key stays on the server (env var)

## Quick Start
1. **Requirements**: Python 3.10+
2. **Install deps**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Set your API key** (never commit real keys):
   - Create a `.env` file (copy from `.env.example`) and set:
     ```env
     GOOGLE_API_KEY=YOUR_KEY_HERE
     ```
   Or export it in your shell:
   ```bash
   export GOOGLE_API_KEY=YOUR_KEY_HERE
   ```
4. **Run the server**:
   ```bash
   uvicorn server:app --reload --port 8000
   ```
5. **Open the app**: visit http://localhost:8000

## API
`POST /api/suggest`
```json
{
  "topic": "cool startup names for a food delivery app",
  "count": 7,
  "tone": "playful",
  "category": "startup-names"
}
```
Response:
```json
{
  "suggestions": ["...", "..."]
}
```

## Notes
- Default model is `gemini-1.5-flash`. You can change it via `MODEL_NAME` env var.
- The server does light post-processing to turn Gemini output into a clean bullet list.
- This is a teaching/demo app; harden before production (rate-limit, auth, logging, etc.).

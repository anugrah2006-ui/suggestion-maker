import os
import re
from typing import List, Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, conint
from dotenv import load_dotenv
import google.generativeai as genai

# Load .env if present
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-1.5-flash")
if not API_KEY:
    raise RuntimeError("GOOGLE_API_KEY is not set. Put it in .env or export it before running.")

genai.configure(api_key=API_KEY)

# Initialize model once
model = genai.GenerativeModel(MODEL_NAME)

app = FastAPI(title="Suggestion Maker (Gemini)")

# Serve static files (index.html, js, css)
app.mount("/static", StaticFiles(directory="static"), name="static")

class SuggestBody(BaseModel):
    topic: str = Field(..., min_length=2, max_length=500, description="Describe what you want suggestions for")
    count: conint(ge=1, le=20) = 8
    tone: Optional[str] = Field(default=None, max_length=40)
    category: Optional[str] = Field(default=None, max_length=40)

def build_prompt(topic: str, count: int, tone: Optional[str], category: Optional[str]) -> str:
    tone_part = f" with a {tone} tone" if tone else ""
    cat_part = f" focused on {category}" if category else ""
    return (
        f"You are a suggestion generator. Provide exactly {count} concise, distinct bullet-point suggestions"
        f"{tone_part}{cat_part} for the following request:\n\n"
        f"Request: {topic}\n\n"
        "Rules:\n"
        "- Output ONLY the list, one per line, no numbers, no extra commentary.\n"
        "- Each suggestion <= 12 words.\n"
        "- No duplicates. Avoid clichés.\n"
    )

bullet_like = re.compile(r"^\s*[-•\*\u2022]?\s*(.+)$")

def parse_suggestions(text: str) -> List[str]:
    # Split on lines and strip bullets; drop empties; de-duplicate while preserving order
    out, seen = [], set()
    for line in text.splitlines():
        m = bullet_like.match(line)
        if not m:
            continue
        s = m.group(1).strip()
        if not s:
            continue
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
    # Fallback: if model returned a paragraph, split on semicolons or periods
    if not out:
        parts = re.split(r"[;\n\.]+", text)
        for p in parts:
            s = p.strip(" \t-•*")
            if s and s not in seen:
                out.append(s)
                seen.add(s)
    return out

@app.get("/", response_class=HTMLResponse)
def root():
    return FileResponse("static/index.html")

@app.post("/api/suggest")
async def suggest(body: SuggestBody):
    prompt = build_prompt(body.topic, body.count, body.tone, body.category)
    try:
        resp = model.generate_content(prompt)
        text = resp.text or ""
        suggestions = parse_suggestions(text)[: body.count]
        # Ensure we return exactly count items if possible; pad if underflow
        if len(suggestions) < body.count and text:
            # Try a secondary pass by splitting more aggressively
            parts = [p.strip() for p in re.split(r"[\n;\.\u2022\-]+", text) if p.strip()]
            for p in parts:
                if len(suggestions) >= body.count:
                    break
                if p not in suggestions:
                    suggestions.append(p)
        return JSONResponse({"suggestions": suggestions})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

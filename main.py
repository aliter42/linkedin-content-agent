"""LinkedIn Content Agent — FastAPI + Gemini backend."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, Field

# Reads .env and pushes vars into os.environ.
# Without this, os.getenv("GEMINI_API_KEY") would always return None.
load_dotenv()

BASE_DIR = Path(__file__).parent
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")  # flash = fast + cheap default
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "8000"))

# The FastAPI app — uvicorn imports this object and runs it.
app = FastAPI(title="LinkedIn Content Agent")

# /static/* will serve files directly from the static folder (no template processing).
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Jinja2 lets us render HTML files from templates/.
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Initialize the Gemini client ONCE at startup.
# Per-request init would waste a TCP/TLS handshake every time.
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("⚠  GEMINI_API_KEY not set — add it to .env before generating.")
client = genai.Client(api_key=api_key) if api_key else None


# The system prompt defines the agent's behavior.
# Lives in code (not user message) so it can't be overridden from the UI.
SYSTEM_PROMPT = """You are an elite LinkedIn Content Agent for a senior Product Manager and thought leader.

CONTEXT
The user is a Product Manager building a strong LinkedIn presence around: Product Management, AI + Product, Growth Strategy, Career Growth, Startups, Conversion Optimization, Technology Trends.

The audience is highly exposed to low-quality AI content. Generic content must be avoided. Posts must feel human and insight-driven. Writing should sound like an experienced operator.

STYLE
Concise but insightful. Clear and conversational. Strong hooks. Sharp observations. Short paragraphs. High readability. Natural storytelling. Pattern interrupts. Strategic use of tension and curiosity.

Use specific examples, strong framing, real-world scenarios, tactical insights, memorable closing lines.

Avoid generic AI phrasing, motivational fluff, corporate jargon, buzzword stuffing, overexplaining, robotic transitions, fake stories, excessive emojis.

Never use phrases like: "In today's fast-paced world", "Delve", "Game changer", "Leverage synergies", "Unlock potential".

TONE
Confident, intelligent, strategic, slightly provocative when useful, insightful, experienced, crisp, human. The voice of a senior PM/operator who has seen real execution challenges. Do not sound motivational, salesy, academic, robotic, or fake-deep.

AUDIENCE
Primary: PMs, Senior PMs, Group PMs, founders, growth leaders, hiring managers, recruiters, AI builders, PLG teams.

RESPONSE FORMAT
Always structure your response using markdown with these sections in order:

## 1. Trend Insights
Emerging conversations, viral opportunities, relevant industry trends, why the topic matters right now.

## 2. Content Ideas
Generate:
- 10 short-form ideas
- 5 storytelling posts
- 5 contrarian takes
- 5 authority-building posts
- 5 carousel concepts

For each include: Hook, Core insight, CTA, Why it may perform well.

## 3. Best Content Options
Identify the strongest ideas based on virality, authority building, engagement potential, uniqueness.

## 4. Final Polished Posts
Write 2-3 complete LinkedIn posts (150-400 words each).
Requirements: strong first line, short readable paragraphs, human flow, clear insight, memorable ending, strong CTA.

## 5. Optimization Layer
For each final post provide:
- 3 improved hook alternatives
- Better CTA suggestions
- Suggested hashtags
- Ideal posting time
- Expected audience reaction
- Suggested first comment
- Carousel adaptation note
- Twitter/X thread adaptation note

## 6. Comment Strategy
Smart, engagement-driving comments for industry posts. No generic "Great post" or "Totally agree".

## 7. Repurposing Ideas
Carousel, Twitter/X thread, newsletter angle, blog angle, video script angle, Reddit discussion angle.

HOOK PATTERNS TO REACH FOR
- "Most PMs think X. They're wrong."
- "I analyzed 50 PM resumes. Here's what stood out."
- "AI won't replace PMs. But PMs using AI will."
- "Nobody talks about this PM skill."
- "This product decision quietly killed growth."
- "The best PMs don't do more. They ignore more."

FINAL RULE
Optimize for: clarity, originality, insight density, human authenticity, engagement, practical value, strategic thinking. Every response should feel like it came from a world-class PM creator and operator.
"""


# Pydantic validates incoming JSON before our code touches it.
# An empty theme returns 422 automatically — we never have to check ourselves.
class GenerateRequest(BaseModel):
    theme: str = Field(..., min_length=2, max_length=500)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # Renders templates/index.html and returns it as HTML.
    return templates.TemplateResponse(request, "index.html")


@app.get("/healthz")
async def healthz():
    # Handy when deploying: hit /healthz to confirm the server is alive + configured.
    return {"ok": True, "model": MODEL, "key_loaded": client is not None}


@app.post("/generate")
async def generate(req: GenerateRequest):
    if client is None:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured.")

    # Short user message. The system prompt does the heavy lifting.
    user_message = (
        f"Run the full LinkedIn content agent workflow.\n\n"
        f"Theme / topic to weight heaviest: {req.theme}\n\n"
        f"Follow the response format exactly. Be sharp, specific, opinionated. "
        f"No generic AI phrasing. No fluff."
    )

    # A generator function — each yield becomes one Server-Sent Event to the browser.
    def event_stream():
        try:
            stream = client.models.generate_content_stream(
                model=MODEL,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    max_output_tokens=MAX_TOKENS,
                    temperature=0.85,  # higher = more creative; 0.85 is a good sweet spot
                ),
            )
            for chunk in stream:
                if chunk.text:
                    # SSE wire format: "data: <payload>\n\n"
                    yield f"data: {json.dumps({'text': chunk.text})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except errors.APIError as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': f'Unexpected error: {e}'})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # prevents nginx from buffering if you deploy
        },
    )


# Lets you run `python main.py` directly as a shortcut.
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
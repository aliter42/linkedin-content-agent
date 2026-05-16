# LinkedIn Content Agent

A FastAPI + Gemini web app that generates high-authority LinkedIn content briefs for senior PMs. Drop a theme, get trend insights, 30+ ideas, polished posts, hooks, hashtags, comment strategy, and repurposing angles—streamed live.

**Built to sound human. Zero generic AI phrasing tolerated.**

---

## What it does

You input a topic (e.g., "Why most PMs misuse AI in their workflow"). The agent:

1. **Scans emerging trends** around that topic
2. **Generates 30+ content ideas** (short-form, storytelling, contrarian, authority-building, carousels)
3. **Writes 2–3 polished LinkedIn posts** (150–400 words, publish-ready)
4. **Optimizes each post** with hook alternatives, CTA variants, hashtags, ideal posting time, expected reactions, first-comment seeds
5. **Suggests smart comments** for engagement on others' posts
6. **Repurposing angles** (Twitter threads, carousels, newsletters, blogs, video scripts)

All streamed live to your browser as the model generates.

---

## Why this exists

The LinkedIn feed is flooded with generic "AI-generated" advice. This agent is designed differently:

- **System prompt built for operators, not influencers.** Emphasizes sharp observations, tactical insights, real-world context—not motivational fluff.
- **Streaming, not batch responses.** Watch output appear in real time. 4–8K tokens flows smoothly.
- **High-signal defaults.** Assumes you're a serious PM building credibility, not chasing viral vanity metrics.

---

## Tech stack

- **Backend:** FastAPI (Python) + Uvicorn
- **Frontend:** HTML + CSS + vanilla JS
- **LLM:** Google Gemini 2.5 Flash (with streaming)
- **Real-time:** Server-Sent Events (SSE) for live output

---

## Quick start

### Prerequisites

- Python 3.10+
- A Gemini API key (free tier is generous for `gemini-2.5-flash`)

### Setup

```bash
git clone <repo-url>
cd linkedin_agent

# Create + activate virtualenv
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Add your API key
cp .env.example .env
# Edit .env, paste your GEMINI_API_KEY

# Run the server
uvicorn main:app --reload
```

Open http://127.0.0.1:8000 in your browser.

---

## How to use

1. **Type a theme** in the textarea (or click a preset chip)
   - Good: "How early-stage PMs should validate AI feature ideas before scoping"
   - Bad: "AI in product"
2. **Hit RUN AGENT** (or `⌘/Ctrl + Enter`)
3. **Watch the brief stream** into the output panel
4. **Copy markdown** to paste into your notes, or **New Run** to try another theme

---

## Configuration

All via `.env`:

| Variable | Default | Notes |
|---|---|---|
| `GEMINI_API_KEY` | *(required)* | Get from [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Swap to `gemini-2.5-pro` for higher quality (slower, costs more) |
| `MAX_TOKENS` | `8000` | Bump if outputs get truncated |

---

## Project structure

```
linkedin_agent/
├── main.py                 # FastAPI app + system prompt + /generate endpoint
├── requirements.txt        # Python dependencies
├── .env.example            # Template for .env
├── templates/
│   └── index.html          # Single-page UI
└── static/
    ├── style.css           # Editorial dark theme
    └── app.js              # SSE streaming + markdown render
```

---

## System prompt

The agent operates under a detailed system prompt that enforces:

- **No generic AI phrasing** ("In today's fast-paced world", "Delve", "Leverage synergies", etc.)
- **Operator voice** — confident, strategic, slightly provocative, human
- **Insight density** — specific examples, strong framing, real-world scenarios
- **Tactical execution** — posts readers can act on, not abstract motivation

The prompt is baked into `main.py` so users can't override it from the UI.

---

## Extending this

A few natural next moves:

- **History sidebar** — persist runs to SQLite, browse + re-edit past briefs
- **Voice samples** — let users paste past LinkedIn posts; pre-prompt the agent to mirror their voice
- **Multi-theme weighting** — UI picks multiple themes and weights them (`AI x Product: 60%, Career Growth: 40%`)
- **Scheduled posting** — integrate Buffer or Typefully APIs to push polished posts directly to draft queue
- **Eval loop** — log which posts users actually publish vs. discard; use that signal to refine the system prompt

---

## Costs

- **Gemini API pricing:** Check [ai.google.dev/pricing](https://ai.google.dev/pricing)
- **Rough cost per run:** A full brief is 4–8K output tokens. On `gemini-2.5-flash`, that's typically $0.01–$0.03 per run
- **Free tier:** Generous rate limits; won't be charged for normal testing

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError` | Activate venv: `source .venv/bin/activate` |
| `GEMINI_API_KEY not configured` | Check `.env` exists at project root with your real key; restart server |
| Output looks generic | Theme is too vague. Be specific: "How PMs should approach X" not just "X" |
| 429 rate limit error | Hit free-tier ceiling; wait 60 sec or use `gemini-2.5-pro` with paid access |
| Server won't start | Run `pip install -r requirements.txt` again; confirm `.venv` is active |

---

## License

MIT. Use freely, fork boldly, improve relentlessly.

---

## Questions?

Open an issue. Contributions welcome.

Built by a PM for PMs who refuse to sound like an AI.

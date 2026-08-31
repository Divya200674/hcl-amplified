# LearnPath AI — Personalized Learning Path Recommender

Hackathon-ready assistant that turns a learner's **goal, level, hours, and style** into a **sequenced roadmap** of courses, projects, and assessments — with explanations, progress tracking, and intensity variants.

## Why this is not "just ChatGPT"

Recommendations come from a **9-signal hybrid ranker** (TF-IDF + career skill maps + skill-gap + domain + level + style + time + popularity + feedback). Paths are **graphs**: missing prerequisites are injected, then **NetworkX topological sort** + **hour packing** against your weekly budget and deadline.

OpenAI is optional. The full product works in **rule-based + sklearn** mode.

## Features

- Career templates (Data Scientist, Full-Stack, ML Engineer, Cloud, Security, Mobile)
- Natural-language chat + profile sliders (hours, style, level)
- Hybrid recommender with visible score breakdown
- Fast-track / Balanced / Deep path comparison
- Prerequisite injection and milestone calendar
- "Why this item" explanations (LLM or transparent rules)
- 👍/👎 adaptive re-ranking
- Progress cockpit with skill radar; completing an item **rebuilds the remaining path**
- Export roadmap as Markdown
- Dark premium Streamlit theme

## Setup

```powershell
cd "C:\Users\LASYA SRI\Desktop\hcl challenge-"
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000** — custom HTML/CSS UI.

Backup Streamlit UI (optional): `streamlit run streamlit_app.py`

Optional `.env`:

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
USE_LLM=false
```

Keep `USE_LLM=false` if you have no OpenAI quota. The demo still scores well.

## Demo flow (3 minutes)

1. Home → **Use Data Scientist**
2. Learning Path → Generate **balanced**, expand first two items (why + score bars)
3. Compare & Insights → **Compute all three paths**, switch to fast-track
4. Dashboard → mark first item completed (path adapts)
5. Download Markdown

## Project layout

```
app.py
pages/
  1_Chat_Assistant.py
  2_Learning_Path.py
  3_Dashboard.py
  4_Compare_Insights.py
src/
  career/          # role → skill maps
  recommendation/  # TF-IDF hybrid scorer
  path_generator/  # graph + time packing
  ai_assistant/    # parser + explainer
  ui/              # theme
  export/          # markdown export
data/              # 65 catalog items
docs/              # solution document + demo script
```

## Deploy (optional)

[Streamlit Community Cloud](https://streamlit.io/cloud): connect the GitHub repo, main file `app.py`. Do not upload `.env`.

## ZIP for judges

Include `app.py`, `pages`, `src`, `data/*.json` (not `learner.db`), `docs`, `.streamlit`, `requirements.txt`, `README.md`, `.env.example`. Exclude `venv` and `__pycache__`.

# LearnPath AI — Solution Documentation

## 1. Problem understanding

Online platforms recommend **courses**. Learners need a **journey**: the right order, the right difficulty, enough practice, and a calendar that fits real life.

A one-size-fits-all list fails because learners differ in:

- starting skill level
- career target (data scientist vs cloud engineer)
- weekly hours and deadlines
- preference for projects vs lectures
- what they already finished

**LearnPath AI** builds a personal roadmap of courses, projects, and assessments, explains every pick, and adapts when the learner gives feedback or completes work.

## 2. Solution design

### Workflow

1. Intake — career template or natural language + sliders  
2. Profile — interests, level, skills, hours, style, deadline  
3. Rank — 9-signal hybrid score for every catalog item  
4. Path — inject prerequisites, topological order, pack hours  
5. Explain — LLM if available, otherwise transparent rule text + score bars  
6. Adapt — 👍/👎, progress completion, intensity switch (fast / balanced / deep)

### Architecture

- **UI:** Streamlit multi-page app (Home, Chat, Path, Dashboard, Compare)
- **Catalog:** 65 JSON items (40 courses, 15 projects, 10 assessments) with skills and prerequisites
- **Persistence:** SQLite (profile, progress, chat)
- **ML:** scikit-learn TF-IDF (unigrams + bigrams) + cosine similarity
- **Graph:** NetworkX DAG + topological sort
- **Optional LLM:** OpenAI for parsing and richer explanations; **full fallback without API**

## 3. AI / ML techniques (judges)

| Technique | Role |
|-----------|------|
| TF-IDF + cosine | Content match between profile text and item text |
| Career skill maps | Role → required skills; coverage metric |
| Skill-gap ratio | Prefer items that teach missing skills |
| Domain / level / style / time scores | Fit to stated constraints |
| Popularity prior | Weak quality signal |
| Feedback boost | Explicit preference learning |
| Weighted hybrid | Interpretable linear combination (not a black box) |
| Prerequisite injection | Incomplete top-k lists become valid curricula |
| Topological sort | Legal learning order |
| Hour packing | `study_hours = content_weeks × 8`; calendar = hours / weekly_hours; trim to deadline |
| Adaptive rebuild | Completing an item updates skills and regenerates the tail |

**This is not an LLM wrapper.** The LLM is an optional interface. The ranking and sequencing run locally.

## 4. Key features

- Six one-click career templates for cold start
- Conversational profile + manual sliders
- Visible per-item score breakdown
- Fast-track vs balanced vs deep comparison
- Milestone calendar and weekly load chart
- Markdown export of the path
- Skill radar vs career target
- Next-action card
- Dark theme tuned for live demo

## 5. Innovation

1. **Constraint-aware paths** — hours and deadline change the actual sequence, not just the copy  
2. **Curriculum validity** — graph repair so recommended advanced courses never appear without foundations  
3. **Intensity as a product** — same goal, three life-fit options  
4. **Closed loop** — feedback and completion change the next ranking  
5. **Explainable hybrid** — every weight is documented on the Compare page  

## 6. Challenges and mitigations

| Challenge | Mitigation |
|-----------|------------|
| OpenAI 429 / no quota | `USE_LLM=false` + rule parser/explainer |
| Cold start | Career templates |
| Prerequisite holes in top-k | Inject ancestors from full catalog |
| Over-long paths | Intensity + hour packing + deadline trim |
| Opaque scores | Breakdown bars + Compare page table |

## 7. Tech stack

Python 3.10+, Streamlit, pandas, numpy, scikit-learn, NetworkX, Plotly, Pydantic, SQLite, python-dotenv, optional OpenAI.

## 8. How to run

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 9. Future work

Collaborative filtering from many learners, live LMS catalogs, spaced-repetition quizzes, PDF export, Streamlit Cloud deploy.

## 10. Conclusion

LearnPath AI treats personalization as **ranking + curriculum design + calendar**, not as a chat that lists course names. That is the gap the problem statement asked to close.

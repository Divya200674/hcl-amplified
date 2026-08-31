from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file
from io import BytesIO

from src.ai_assistant.explainer import answer_learner_query
from src.ai_assistant.goal_parser import parse_user_goal
from src.career.roles import CAREER_ROLES, apply_role_template
from src.database.db import get_progress, save_chat_message, save_profile, save_progress
from src.export.path_export import path_to_markdown
from src.models.learner import LearnerProfile, LearningGoal, SkillLevel
from src.profiling.profiler import apply_feedback, update_profile_from_completion
from web import state
from web.serialize import path_dict, profile_dict
from src.planning.quiz import QUIZ, score_quiz

ROOT = Path(__file__).resolve().parent.parent

app = Flask(
    __name__,
    template_folder=str(ROOT / "templates"),
    static_folder=str(ROOT / "static"),
)


def _ensure_profile() -> LearnerProfile:
    p = state.profile()
    if p is None:
        p = LearnerProfile()
        save_profile(p)
    return p


@app.context_processor
def inject_nav():
    return {"nav_roles": list(CAREER_ROLES.keys())}


@app.get("/")
def home():
    return render_template("index.html", page="home")


@app.get("/chat")
def chat_page():
    return render_template("chat.html", page="chat")


@app.get("/path")
def path_page():
    return render_template("path.html", page="path")


@app.get("/dashboard")
def dashboard_page():
    return render_template("dashboard.html", page="dashboard")


@app.get("/quiz")
def quiz_page():
    return render_template("quiz.html", page="quiz")


@app.get("/api/state")
def api_state():
    p = _ensure_profile()
    return jsonify(
        {
            "profile": profile_dict(p),
            "path": path_dict(p, state.learning_path, get_progress("default_user")),
            "messages": state.messages,
            "roles": {k: {"domain": v["domain"], "skills": v["skills"]} for k, v in CAREER_ROLES.items()},
            "catalog_size": len(state.CATALOG),
            "llm": state.LLM.available,
            "progress": get_progress("default_user"),
            "variants": {
                k: {
                    "count": len(v.items),
                    "calendar_weeks": v.calendar_weeks,
                    "study_hours": v.study_hours,
                    "coverage": v.coverage,
                    "milestones": len(v.milestones),
                }
                for k, v in (state.path_variants or {}).items()
            },
        }
    )


@app.post("/api/template")
def api_template():
    data = request.get_json(force=True)
    role = data.get("role", "")
    if role not in CAREER_ROLES:
        return jsonify({"error": "Unknown role"}), 400
    meta = CAREER_ROLES[role]
    p = LearnerProfile(
        skill_level=SkillLevel.BEGINNER,
        preferred_style="hands-on",
        weekly_hours=10,
        goals=[
            LearningGoal(
                title=role.title(),
                description=f"Become a {role}",
                target_domain=meta["domain"],
                deadline_weeks=24,
            )
        ],
    )
    p = apply_role_template(p, role)
    save_profile(p)
    state.learning_path = state.GENERATOR.generate(p, state.CATALOG, intensity="balanced")
    state.path_variants = None
    state.messages.append({"role": "assistant", "content": f"Mapped you to **{role.title()}** and built a balanced path."})
    return jsonify({"ok": True, "profile": profile_dict(p), "path": path_dict(p, state.learning_path, get_progress("default_user"))})


@app.post("/api/chat")
def api_chat():
    data = request.get_json(force=True)
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Empty message"}), 400
    p = _ensure_profile()
    state.messages.append({"role": "user", "content": message})
    save_chat_message("default_user", "user", message)
    p, summary = parse_user_goal(message, p, state.LLM)
    save_profile(p)
    state.messages.append({"role": "assistant", "content": summary})
    save_chat_message("default_user", "assistant", summary)
    return jsonify({"ok": True, "reply": summary, "profile": profile_dict(p), "messages": state.messages})


@app.post("/api/ask")
def api_ask():
    data = request.get_json(force=True)
    query = (data.get("query") or "").strip()
    p = _ensure_profile()
    titles = state.learning_path.titles() if state.learning_path else []
    extra = ""
    if state.learning_path:
        extra = f"Calendar weeks: {state.learning_path.calendar_weeks}"
    answer = answer_learner_query(query, p, titles, state.LLM, extra_context=extra)
    state.messages.append({"role": "user", "content": query})
    state.messages.append({"role": "assistant", "content": answer})
    return jsonify({"ok": True, "reply": answer, "messages": state.messages})


@app.post("/api/profile")
def api_profile():
    data = request.get_json(force=True)
    p = _ensure_profile()
    if data.get("name"):
        p.name = data["name"]
    if data.get("skill_level"):
        p.skill_level = SkillLevel(data["skill_level"])
    if data.get("weekly_hours"):
        p.weekly_hours = int(data["weekly_hours"])
    if data.get("preferred_style"):
        p.preferred_style = data["preferred_style"]
    save_profile(p)
    return jsonify({"ok": True, "profile": profile_dict(p)})


@app.post("/api/path")
def api_path():
    intensity = (request.get_json(force=True) or {}).get("intensity", "balanced")
    p = _ensure_profile()
    if not p.goals:
        return jsonify({"error": "Set a goal first (home template or chat)."}), 400
    state.learning_path = state.GENERATOR.generate(p, state.CATALOG, intensity=intensity)
    return jsonify({"ok": True, "path": path_dict(p, state.learning_path, get_progress("default_user"))})


@app.post("/api/variants")
def api_variants():
    p = _ensure_profile()
    if not p.goals:
        return jsonify({"error": "Set a goal first."}), 400
    state.path_variants = state.GENERATOR.compare_intensities(p, state.CATALOG)
    intensity = (request.get_json(silent=True) or {}).get("intensity", "balanced")
    state.learning_path = state.path_variants.get(intensity) or list(state.path_variants.values())[1]
    return jsonify(
        {
            "ok": True,
            "variants": {
                k: {
                    "count": len(v.items),
                    "calendar_weeks": v.calendar_weeks,
                    "study_hours": v.study_hours,
                    "coverage": v.coverage,
                    "milestones": len(v.milestones),
                }
                for k, v in state.path_variants.items()
            },
            "path": path_dict(p, state.learning_path, get_progress("default_user")),
        }
    )


@app.post("/api/use-variant")
def api_use_variant():
    key = (request.get_json(force=True) or {}).get("intensity")
    if not state.path_variants or key not in state.path_variants:
        return jsonify({"error": "Compute variants first."}), 400
    state.learning_path = state.path_variants[key]
    return jsonify({"ok": True, "path": path_dict(_ensure_profile(), state.learning_path, get_progress("default_user"))})


@app.post("/api/feedback")
def api_feedback():
    data = request.get_json(force=True)
    p = apply_feedback(_ensure_profile(), data["item_id"], int(data["score"]))
    save_profile(p)
    return jsonify({"ok": True})


@app.post("/api/progress")
def api_progress():
    data = request.get_json(force=True)
    item_id = data["item_id"]
    status = data["status"]
    save_progress("default_user", item_id, status)
    p = _ensure_profile()
    if status == "completed":
        by_id = {i.id: i for i in state.CATALOG}
        p = update_profile_from_completion(p, item_id, by_id)
        save_profile(p)
        intensity = state.learning_path.intensity if state.learning_path else "balanced"
        state.learning_path = state.GENERATOR.generate(p, state.CATALOG, intensity=intensity)
    return jsonify(
        {
            "ok": True,
            "profile": profile_dict(p),
            "path": path_dict(p, state.learning_path, get_progress("default_user")),
            "progress": get_progress("default_user"),
        }
    )


@app.get("/api/export.md")
def api_export():
    p = _ensure_profile()
    if not state.learning_path:
        return jsonify({"error": "No path"}), 400
    md = path_to_markdown(p, state.learning_path)
    buf = BytesIO(md.encode("utf-8"))
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="learning-path.md", mimetype="text/markdown")


@app.get("/api/quiz")
def api_quiz_get():
    return jsonify({"questions": QUIZ})


@app.post("/api/quiz")
def api_quiz_post():
    answers = (request.get_json(force=True) or {}).get("answers") or {}
    result = score_quiz(answers)
    meta = CAREER_ROLES[result["role"]]
    p = LearnerProfile(
        skill_level=SkillLevel(result["skill_level"]),
        preferred_style=result["preferred_style"],
        weekly_hours=result["weekly_hours"],
        current_skills=result["skills"],
        goals=[
            LearningGoal(
                title=result["role"].title(),
                description="Set from diagnostic quiz",
                target_domain=meta["domain"],
                deadline_weeks=24,
            )
        ],
    )
    p = apply_role_template(p, result["role"])
    save_profile(p)
    state.learning_path = state.GENERATOR.generate(p, state.CATALOG, intensity="balanced")
    state.path_variants = None
    return jsonify(
        {
            "ok": True,
            "result": result,
            "profile": profile_dict(p),
            "path": path_dict(p, state.learning_path, get_progress("default_user")),
        }
    )


@app.get("/api/alternatives/<item_id>")
def api_alternatives(item_id: str):
    p = _ensure_profile()
    if not state.learning_path:
        return jsonify({"error": "No path"}), 400
    alts = state.GENERATOR.alternatives(p, state.CATALOG, state.learning_path, item_id)
    return jsonify(
        {
            "ok": True,
            "alternatives": [
                {
                    "id": s.item.id,
                    "title": s.item.title,
                    "domain": s.item.domain,
                    "level": s.item.level,
                    "score": round(s.score, 3),
                    "description": s.item.description,
                    "skills_taught": s.item.skills_taught,
                }
                for s in alts
            ],
        }
    )


@app.post("/api/swap")
def api_swap():
    data = request.get_json(force=True) or {}
    p = _ensure_profile()
    if not state.learning_path:
        return jsonify({"error": "No path"}), 400
    try:
        state.learning_path = state.GENERATOR.swap_item(
            p, state.CATALOG, state.learning_path, data["old_id"], data["new_id"]
        )
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"ok": True, "path": path_dict(p, state.learning_path, get_progress("default_user"))})


def create_app() -> Flask:
    return app

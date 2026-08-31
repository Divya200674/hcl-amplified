import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.express as px
import streamlit as st

from src.ai_assistant.explainer import explain_recommendation
from src.ai_assistant.llm_client import LLMClient
from src.database.db import save_profile
from src.export.path_export import path_to_markdown
from src.path_generator.path_builder import LearningPathGenerator
from src.profiling.profiler import apply_feedback, load_all_items
from src.ui.theme import apply_theme, kpi

st.set_page_config(page_title="Learning Path", page_icon="🗺️", layout="wide")
apply_theme()

if "profile" not in st.session_state:
    st.session_state.profile = None
if "learning_path" not in st.session_state:
    st.session_state.learning_path = None
if "catalog" not in st.session_state:
    st.session_state.catalog = load_all_items()
if "llm" not in st.session_state:
    st.session_state.llm = LLMClient()
if "path_variants" not in st.session_state:
    st.session_state.path_variants = None

st.markdown('<p class="hero-title">Your roadmap</p>', unsafe_allow_html=True)
st.caption("Prerequisite-aware sequence packed to your weekly hours. Feedback re-ranks the next generation.")

if not st.session_state.profile or not st.session_state.profile.goals:
    st.warning("Complete a profile first — use a career template on Home or Chat Assistant.")
    st.stop()

profile = st.session_state.profile
generator = LearningPathGenerator()

ctrl1, ctrl2, ctrl3 = st.columns([1.4, 1, 1])
with ctrl1:
    intensity = st.selectbox("Path intensity", ["fast-track", "balanced", "deep"], index=1)
with ctrl2:
    if st.button("Generate / refresh path", type="primary", use_container_width=True):
        st.session_state.learning_path = generator.generate(
            profile, st.session_state.catalog, intensity=intensity
        )
        st.rerun()
with ctrl3:
    if st.button("Build 3 variants", use_container_width=True):
        st.session_state.path_variants = generator.compare_intensities(profile, st.session_state.catalog)
        st.session_state.learning_path = st.session_state.path_variants[intensity]
        st.rerun()

if st.session_state.learning_path is None:
    st.info("Choose intensity, then generate. Fast-track fits tight deadlines; deep covers more career skills.")
    st.stop()

path = st.session_state.learning_path
m1, m2, m3, m4 = st.columns(4)
m1.markdown(kpi("Items", str(len(path.items))), unsafe_allow_html=True)
m2.markdown(kpi("Calendar", f"{path.calendar_weeks} weeks"), unsafe_allow_html=True)
m3.markdown(kpi("Study hours", f"{path.study_hours:.0f}"), unsafe_allow_html=True)
m4.markdown(kpi("Career skill cover", f"{path.coverage:.0%}"), unsafe_allow_html=True)

if profile.goals and profile.goals[0].deadline_weeks:
    deadline = profile.goals[0].deadline_weeks
    if path.calendar_weeks > deadline:
        st.warning(
            f"This path needs ~{path.calendar_weeks} calendar weeks but your deadline is {deadline}. "
            "Switch to **fast-track** or increase weekly hours, then regenerate."
        )
    else:
        st.success(f"Fits your {deadline}-week goal at {profile.weekly_hours} hours/week.")

md = path_to_markdown(profile, path)
st.download_button("Download path as Markdown", md, file_name="learning-path.md", mime="text/markdown")

timeline = []
hour_cursor = 0.0
for item in path.items:
    hour_cursor += max(2.0, item.duration_weeks * 8)
    week = max(1, int((hour_cursor + profile.weekly_hours - 1) // profile.weekly_hours))
    timeline.append({"Week": week, "Title": item.title, "Type": item.item_type.value, "Hours": item.duration_weeks * 8})
if timeline:
    fig = px.bar(
        pd.DataFrame(timeline),
        x="Week",
        y="Hours",
        color="Type",
        hover_data=["Title"],
        color_discrete_map={"course": "#6C5CE7", "project": "#00CEC9", "assessment": "#FDCB6E"},
        title="Weekly study load",
    )
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#F4F6FB", height=320)
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Sequenced roadmap")
week = 0
for idx, item in enumerate(path.items):
    week += max(1, int(item.duration_weeks))
    score = path.scores.get(item.id, 0)
    breakdown = path.breakdowns.get(item.id, {})
    icons = {"course": "📘", "project": "🔨", "assessment": "📝"}
    icon = icons.get(item.item_type.value, "📌")
    with st.expander(
        f"{icon} {item.title}  ·  {item.item_type.value}  ·  match {score:.0%}",
        expanded=idx < 2,
    ):
        c1, c2 = st.columns([3, 1])
        with c1:
            st.write(
                f"**Domain:** {item.domain} · **Level:** {item.level.title()} · "
                f"**Duration:** {item.duration_weeks} content-weeks"
            )
            st.write(item.description)
            chips = "".join(f'<span class="chip">{s}</span>' for s in item.skills_taught)
            st.markdown(chips, unsafe_allow_html=True)
            if item.prerequisites:
                st.caption("Prerequisites: " + ", ".join(item.prerequisites))
            explanation = explain_recommendation(item, profile, score, st.session_state.llm, breakdown)
            st.markdown("**Why this is here**")
            st.markdown(explanation)
        with c2:
            st.metric("Score", f"{score:.0%}")
            if breakdown:
                st.caption("Signals")
                for k, v in sorted(breakdown.items(), key=lambda kv: kv[1], reverse=True)[:4]:
                    st.progress(min(1.0, max(0.0, v)), text=f"{k} {v:.0%}")
            b1, b2 = st.columns(2)
            with b1:
                if st.button("👍", key=f"up_{item.id}"):
                    st.session_state.profile = apply_feedback(profile, item.id, 1)
                    save_profile(st.session_state.profile)
                    st.toast("We'll boost similar items next time.")
            with b2:
                if st.button("👎", key=f"down_{item.id}"):
                    st.session_state.profile = apply_feedback(profile, item.id, -1)
                    save_profile(st.session_state.profile)
                    st.toast("We'll down-rank this next generation.")

if path.milestones:
    st.subheader("Milestones")
    for ms in path.milestones:
        st.markdown(f"- **Week {ms.week}** — {ms.title}")

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.path_generator.path_builder import INTENSITY_CONFIG, LearningPathGenerator
from src.profiling.profiler import load_all_items
from src.ui.theme import apply_theme, kpi

st.set_page_config(page_title="Compare & Insights", page_icon="🔬", layout="wide")
apply_theme()

if "profile" not in st.session_state:
    st.session_state.profile = None
if "catalog" not in st.session_state:
    st.session_state.catalog = load_all_items()
if "path_variants" not in st.session_state:
    st.session_state.path_variants = None
if "learning_path" not in st.session_state:
    st.session_state.learning_path = None

st.markdown('<p class="hero-title">Compare intensities</p>', unsafe_allow_html=True)
st.caption("Fast-track vs balanced vs deep — same goal, different time and coverage. Pick the one that fits your life.")

profile = st.session_state.profile
if not profile or not profile.goals:
    st.warning("Set a goal on Home or Chat first.")
    st.stop()

if st.button("Compute all three paths", type="primary"):
    st.session_state.path_variants = LearningPathGenerator().compare_intensities(
        profile, st.session_state.catalog
    )

variants = st.session_state.path_variants
if not variants:
    st.info("Click **Compute all three paths** to score Fast-track, Balanced, and Deep side by side.")
    st.stop()

cols = st.columns(3)
for col, key in zip(cols, INTENSITY_CONFIG):
    path = variants[key]
    with col:
        st.markdown(f"#### {key.title()}")
        st.markdown(kpi("Calendar weeks", str(path.calendar_weeks)), unsafe_allow_html=True)
        st.write(f"Items: **{len(path.items)}**")
        st.write(f"Study hours: **{path.study_hours:.0f}**")
        st.write(f"Career coverage: **{path.coverage:.0%}**")
        st.write(f"Milestones: **{len(path.milestones)}**")
        if st.button(f"Use {key}", key=f"use_{key}", use_container_width=True):
            st.session_state.learning_path = path
            st.success(f"Active path set to {key}. Open Learning Path.")

chart = pd.DataFrame(
    [
        {
            "Intensity": k.title(),
            "Calendar weeks": v.calendar_weeks,
            "Items": len(v.items),
            "Coverage %": round(v.coverage * 100),
            "Hours": v.study_hours,
        }
        for k, v in variants.items()
    ]
)
st.dataframe(chart, hide_index=True, use_container_width=True)

fig = go.Figure()
fig.add_bar(x=chart["Intensity"], y=chart["Calendar weeks"], name="Weeks")
fig.add_bar(x=chart["Intensity"], y=chart["Coverage %"], name="Coverage %")
fig.update_layout(
    barmode="group",
    title="Time vs career-skill coverage",
    paper_bgcolor="rgba(0,0,0,0)",
    font_color="#F4F6FB",
    height=360,
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("How scoring works")
st.markdown(
    """
The hybrid engine does **not** just ask a chatbot for a list. Each catalog item gets a weighted score:

| Signal | Weight | What it captures |
|--------|--------|------------------|
| Content (TF-IDF + bigrams) | 28% | Goal/interest language vs course text |
| Career skill map | 18% | Role-specific skills (e.g. Data Scientist) |
| Skill gap | 16% | Skills you still lack |
| Domain fit | 12% | Data Science vs Web vs Cloud… |
| Level fit | 10% | Beginner / intermediate / advanced |
| Learning style | 6% | Hands-on projects vs lecture-style |
| Time fit | 5% | Item length vs your weekly hours |
| Popularity | 3% | Catalog quality prior |
| Feedback | 2% | Your 👍 / 👎 |

The path builder then **injects missing prerequisites**, **topologically sorts** the graph, and **packs hours** into your deadline.
"""
)

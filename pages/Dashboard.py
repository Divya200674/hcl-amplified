import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.career.roles import target_skills_for_profile
from src.database.db import get_progress, save_progress, save_profile
from src.path_generator.path_builder import LearningPathGenerator
from src.profiling.profiler import load_all_items, update_profile_from_completion
from src.ui.theme import apply_theme, kpi

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
apply_theme()

if "profile" not in st.session_state:
    st.session_state.profile = None
if "learning_path" not in st.session_state:
    st.session_state.learning_path = None
if "catalog" not in st.session_state:
    st.session_state.catalog = load_all_items()

st.markdown('<p class="hero-title">Progress cockpit</p>', unsafe_allow_html=True)
st.caption("Skill coverage, milestones, and the single next action. Completing an item unlocks skills and can rebuild the tail of the path.")

profile = st.session_state.profile
path = st.session_state.learning_path
catalog = st.session_state.catalog
items_by_id = {item.id: item for item in catalog}

if not profile:
    st.warning("Create a profile on Home or Chat first.")
    st.stop()

progress = get_progress("default_user")

if path and path.items:
    completed = sum(1 for item in path.items if progress.get(item.id, {}).get("status") == "completed")
    total = len(path.items)
    pct = (completed / total * 100) if total else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi("Path complete", f"{pct:.0f}%"), unsafe_allow_html=True)
    c2.markdown(kpi("Done", f"{completed}/{total}"), unsafe_allow_html=True)
    c3.markdown(kpi("Skills logged", str(len(profile.current_skills))), unsafe_allow_html=True)
    c4.markdown(kpi("Hours / week", f"{profile.weekly_hours}h"), unsafe_allow_html=True)
    st.progress(min(1.0, pct / 100))

    target_skills = {s.lower() for s in target_skills_for_profile(profile)}
    for item in path.items:
        target_skills.update(s.lower() for s in item.skills_taught)
    current = {s.lower() for s in profile.current_skills}
    labels = sorted(target_skills)[:14]
    if labels:
        fig = go.Figure()
        fig.add_trace(
            go.Scatterpolar(
                r=[1.0 if s in current else 0.15 for s in labels] + [1.0 if labels[0] in current else 0.15],
                theta=labels + [labels[0]],
                fill="toself",
                name="Current",
                line_color="#6C5CE7",
            )
        )
        fig.add_trace(
            go.Scatterpolar(
                r=[1] * (len(labels) + 1),
                theta=labels + [labels[0]],
                fill="toself",
                name="Target",
                line_color="#00CEC9",
                opacity=0.35,
            )
        )
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            showlegend=True,
            title="Skill radar (current vs path/career target)",
            height=460,
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#F4F6FB",
        )
        st.plotly_chart(fig, use_container_width=True)

    missing = [s for s in target_skills_for_profile(profile) if s.lower() not in current]
    have = [s for s in target_skills_for_profile(profile) if s.lower() in current]
    g1, g2 = st.columns(2)
    with g1:
        st.markdown("**Career skills you have**")
        st.write(", ".join(have) or "None yet — complete the first courses.")
    with g2:
        st.markdown("**Still to cover**")
        st.write(", ".join(missing) or "All mapped career skills are covered.")

    rows = []
    for item in path.items:
        status = progress.get(item.id, {}).get("status", "not_started")
        rows.append(
            {
                "Item": item.title,
                "Type": item.item_type.value.title(),
                "Domain": item.domain,
                "Status": status.replace("_", " ").title(),
                "Content weeks": item.duration_weeks,
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.subheader("Update progress")
    item_options = {item.title: item.id for item in path.items}
    selected_title = st.selectbox("Item", list(item_options.keys()))
    selected_id = item_options[selected_title]
    status = st.radio("Status", ["in_progress", "completed"], horizontal=True)
    if st.button("Save progress", type="primary"):
        save_progress("default_user", selected_id, status)
        if status == "completed":
            profile = update_profile_from_completion(profile, selected_id, items_by_id)
            st.session_state.profile = profile
            save_profile(profile)
            rebuilt = LearningPathGenerator().generate(
                profile, catalog, intensity=path.intensity or "balanced"
            )
            st.session_state.learning_path = rebuilt
            st.success("Completed — skills unlocked and remaining path adapted.")
        else:
            st.success("Marked in progress.")
        st.rerun()

    remaining = [
        item for item in path.items if progress.get(item.id, {}).get("status") != "completed"
    ]
    if remaining:
        nxt = remaining[0]
        st.markdown(
            f'<div class="next-action"><strong>Next action:</strong> {nxt.title} '
            f"({nxt.item_type.value}) — {nxt.description}<br>"
            f"<span style='color:#A0A8C0'>~{nxt.duration_weeks} content-weeks · {nxt.domain}</span></div>",
            unsafe_allow_html=True,
        )
else:
    st.info("Generate a path on **Learning Path** to unlock tracking.")
    if profile.interests:
        fig = px.bar(
            x=profile.interests,
            y=[1] * len(profile.interests),
            labels={"x": "Domain", "y": ""},
            title="Interest areas",
        )
        fig.update_layout(showlegend=False, yaxis_visible=False, height=280, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

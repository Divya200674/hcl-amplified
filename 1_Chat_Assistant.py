import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from src.ai_assistant.explainer import answer_learner_query
from src.ai_assistant.goal_parser import parse_user_goal
from src.ai_assistant.llm_client import LLMClient
from src.database.db import save_chat_message, save_profile
from src.models.learner import LearnerProfile, SkillLevel
from src.ui.theme import apply_theme

st.set_page_config(page_title="Chat Assistant", page_icon="💬", layout="wide")
apply_theme()

if "profile" not in st.session_state:
    st.session_state.profile = None
if "llm" not in st.session_state:
    st.session_state.llm = LLMClient()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "learning_path" not in st.session_state:
    st.session_state.learning_path = None
if "catalog" not in st.session_state:
    from src.profiling.profiler import load_all_items

    st.session_state.catalog = load_all_items()

st.markdown('<p class="hero-title">Learning coach</p>', unsafe_allow_html=True)
st.caption("Describe a goal in plain English. We extract level, domain, hours, and style — then you generate a path.")

if st.session_state.profile is None:
    st.session_state.profile = LearnerProfile()

left, right = st.columns([1.6, 1])
with right:
    st.markdown("#### Tune profile")
    name = st.text_input("Name", st.session_state.profile.name)
    level = st.selectbox(
        "Skill level",
        ["beginner", "intermediate", "advanced"],
        index=["beginner", "intermediate", "advanced"].index(st.session_state.profile.skill_level.value),
    )
    hours = st.slider("Hours per week", 3, 30, int(st.session_state.profile.weekly_hours))
    style = st.selectbox(
        "Learning style",
        ["hands-on", "video", "reading"],
        index=["hands-on", "video", "reading"].index(
            st.session_state.profile.preferred_style
            if st.session_state.profile.preferred_style in ("hands-on", "video", "reading")
            else "hands-on"
        ),
    )
    if st.button("Save profile settings", use_container_width=True):
        p = st.session_state.profile
        p.name = name
        p.skill_level = SkillLevel(level)
        p.weekly_hours = hours
        p.preferred_style = style
        save_profile(p)
        st.session_state.profile = p
        st.success("Saved. Regenerating a path will respect hours and style.")

with left:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    SAMPLE_PROMPTS = [
        "I know Python basics and want to become a data scientist in 6 months, 10 hours per week, hands-on",
        "I'm a beginner interested in web development, prefer building projects",
        "I have intermediate JavaScript skills and want to learn React and Node.js in 16 weeks",
        "Help me transition to cloud computing with AWS, I can study 8 hours per week",
    ]
    st.markdown("**Try a prompt**")
    g1, g2 = st.columns(2)
    for i, prompt in enumerate(SAMPLE_PROMPTS):
        col = g1 if i % 2 == 0 else g2
        with col:
            if st.button(prompt[:52] + "…", key=f"prompt_{i}", use_container_width=True):
                st.session_state._pending_prompt = prompt

    if user_input := st.chat_input("Tell me about your learning goals..."):
        st.session_state._pending_prompt = user_input

    if getattr(st.session_state, "_pending_prompt", None):
        prompt = st.session_state._pending_prompt
        del st.session_state._pending_prompt
        st.session_state.messages.append({"role": "user", "content": prompt})
        save_chat_message("default_user", "user", prompt)
        profile, summary = parse_user_goal(prompt, st.session_state.profile, st.session_state.llm)
        profile.name = name
        profile.skill_level = SkillLevel(level)
        profile.weekly_hours = hours
        profile.preferred_style = style
        st.session_state.profile = profile
        save_profile(profile)
        st.session_state.messages.append({"role": "assistant", "content": summary})
        save_chat_message("default_user", "assistant", summary)
        st.rerun()

st.divider()
qcol, acol = st.columns([3, 1])
with qcol:
    query = st.text_input("Ask about next steps, skill gaps, or why a course was picked")
with acol:
    ask = st.button("Ask", type="primary", use_container_width=True)
if ask and query:
    path_titles = st.session_state.learning_path.titles() if st.session_state.learning_path else []
    extra = ""
    if st.session_state.learning_path:
        extra = f"Calendar weeks: {st.session_state.learning_path.calendar_weeks}; intensity: {st.session_state.learning_path.intensity}"
    answer = answer_learner_query(
        query, st.session_state.profile, path_titles, st.session_state.llm, extra_context=extra
    )
    st.session_state.messages.append({"role": "user", "content": query})
    st.session_state.messages.append({"role": "assistant", "content": answer})
    save_chat_message("default_user", "user", query)
    save_chat_message("default_user", "assistant", answer)
    st.rerun()

if st.button("Reset conversation"):
    st.session_state.messages = []
    st.rerun()

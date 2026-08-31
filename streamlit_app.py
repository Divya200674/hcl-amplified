"""Optional Streamlit UI. Primary product UI is Flask: python app.py"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from src.ai_assistant.llm_client import LLMClient
from src.career.roles import CAREER_ROLES, apply_role_template
from src.database.db import init_db, load_profile, save_profile
from src.models.learner import LearnerProfile, LearningGoal, SkillLevel
from src.path_generator.path_builder import LearningPathGenerator
from src.profiling.profiler import load_all_items
from src.ui.theme import apply_theme, kpi

st.set_page_config(page_title="LearnPath AI (Streamlit)", page_icon="🎓", layout="wide")
init_db()
apply_theme()
st.info("This is the backup Streamlit UI. For the designed HTML/CSS app run: python app.py")
st.markdown('<p class="hero-title">LearnPath AI</p>', unsafe_allow_html=True)

if "catalog" not in st.session_state:
    st.session_state.catalog = load_all_items()
if "llm" not in st.session_state:
    st.session_state.llm = LLMClient()
if "profile" not in st.session_state:
    st.session_state.profile = load_profile("default_user")
if "learning_path" not in st.session_state:
    st.session_state.learning_path = None

st.write("Use career templates on the designed web app for the full experience.")
for role_key, meta in CAREER_ROLES.items():
    if st.button(role_key.title()):
        p = st.session_state.profile or LearnerProfile()
        p.goals = [LearningGoal(title=role_key.title(), target_domain=meta["domain"], deadline_weeks=24)]
        p.interests = []
        p = apply_role_template(p, role_key)
        save_profile(p)
        st.session_state.profile = p
        st.session_state.learning_path = LearningPathGenerator().generate(p, st.session_state.catalog)
        st.success("Path generated — open pages in the sidebar.")

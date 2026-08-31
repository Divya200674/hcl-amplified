"""Shared visual theme for the Streamlit app."""

import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }

.block-container { padding-top: 1.4rem; max-width: 1200px; }

.hero-title {
    font-size: 2.4rem; font-weight: 700; letter-spacing: -0.03em;
    background: linear-gradient(90deg, #A29BFE 0%, #74B9FF 55%, #55EFC4 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 0.25rem;
}
.hero-sub { color: #B8C0D4; font-size: 1.05rem; margin-bottom: 1.4rem; }

.kpi {
    background: linear-gradient(160deg, #2B3154 0%, #1A1F35 100%);
    border: 1px solid rgba(162, 155, 254, 0.25);
    border-radius: 16px; padding: 1rem 1.1rem; text-align: center;
}
.kpi h3 { margin: 0; font-size: 1.45rem; color: #F4F6FB; }
.kpi p { margin: 0.25rem 0 0; color: #A0A8C0; font-size: 0.85rem; }

.card {
    background: #1A1F35; border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px; padding: 1rem 1.15rem; margin: 0.5rem 0 1rem;
}
.card-accent { border-left: 4px solid #6C5CE7; }

.chip {
    display: inline-block; padding: 0.2rem 0.65rem; border-radius: 999px;
    background: rgba(108, 92, 231, 0.22); color: #D6D1FF; font-size: 0.78rem;
    margin: 0.15rem 0.2rem 0.15rem 0;
}

.next-action {
    background: linear-gradient(120deg, rgba(108,92,231,0.25), rgba(85,239,196,0.12));
    border: 1px solid rgba(85,239,196,0.3);
    border-radius: 16px; padding: 1.1rem 1.3rem;
}

div[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #151933 0%, #0F1221 100%);
}

.stButton>button {
    border-radius: 10px; font-weight: 600;
}
</style>
"""


def apply_theme() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def kpi(title: str, value: str) -> str:
    return f'<div class="kpi"><h3>{value}</h3><p>{title}</p></div>'

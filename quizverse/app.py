import os
from pathlib import Path
import streamlit as st
from pages.quiz_creator import quiz_creator_page
from pages.quiz import quiz_page
from pages.results import results_page
from services.gemini_service import GeminiService
from metrics import PAGE_VIEWS, start_metrics_server

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
# Load .env securely
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")

def load_css(file_name):
    css_path = BASE_DIR / file_name
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def main():
    st.set_page_config(
        page_title="QuizVerse AI — Real-Time Quiz & Coach",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    load_css("static/style.css")

    # Expose Prometheus metrics on port 8001 (started once per process)
    start_metrics_server()

    # Session state initialization
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'home'

    # Sidebar: Controls & Gemini API Configuration
    with st.sidebar:
        st.title("⚡ QuizVerse AI")
        st.caption("On-demand test generator & AI coach")
        st.markdown("---")

        if st.button("🏠 New Quiz / Topics", use_container_width=True, type="primary"):
            st.session_state.current_page = 'home'
            st.rerun()

        st.markdown("---")
        st.markdown("---")
        st.caption("🤖 **AI Engine Active**")
        st.caption("🎯 **Instant & Frictionless:** No accounts, no logins, no database. Anyone can test their knowledge in real time.")

    # Page Routing
    page = st.session_state.get('current_page', 'home')

    # Prometheus: count a page view whenever the user navigates to a different page
    if st.session_state.get('last_counted_page') != page:
        PAGE_VIEWS.labels(page=page).inc()
        st.session_state.last_counted_page = page

    if page == 'home':
        quiz_creator_page()
    elif page == 'quiz':
        quiz_page()
    elif page == 'results':
        results_page()
    else:
        quiz_creator_page()

if __name__ == '__main__':
    main()
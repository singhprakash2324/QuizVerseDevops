import streamlit as st
import time
from services.gemini_service import GeminiService, HUDDLE_DEFINITIONS
from metrics import QUIZ_GENERATION_DURATION

FEATURED_TOPICS = [
    {"label": "🧮 Quantitative Aptitude", "topic": "Quantitative Aptitude"},
    {"label": "🧠 Logical Reasoning", "topic": "Logical Reasoning"},
    {"label": "💻 Python & Data Structures", "topic": "Python and Data Structures"},
    {"label": "🌐 Computer Networks & OS", "topic": "Computer Science Core"},
    {"label": "🗣️ Verbal Ability & Reading", "topic": "Verbal Ability & English"},
    {"label": "🔬 Physics & General Science", "topic": "Physics and Applied Science"},
    {"label": "🌎 History & Geography", "topic": "World History and Geography"},
    {"label": "🤖 Machine Learning & AI", "topic": "Machine Learning and AI"}
]

def quiz_creator_page():
    # Initialize session state stores if needed
    if 'unlocked_huddles' not in st.session_state:
        st.session_state.unlocked_huddles = {}
    if 'huddle_bests' not in st.session_state:
        st.session_state.huddle_bests = {}
    if 'seen_questions' not in st.session_state:
        st.session_state.seen_questions = {}

    st.title("⚡ QuizVerse — Exam-Calibrated Topic Huddles")

    # 1. Topic Selection
    with st.container():
        st.subheader("1. Select or Enter Your Topic")

        default_topic = st.session_state.get('active_topic', "Quantitative Aptitude")
        col_input, col_apply = st.columns([3, 1])
        with col_input:
            custom_topic = st.text_input(
                "Enter any subject or test domain:",
                value=default_topic,
                placeholder="e.g. Permutations & Combinations, Data Structures, Indian Polity..."
            )
        with col_apply:
            st.write("")
            st.write("")
            if st.button("Set Topic", use_container_width=True):
                st.session_state.active_topic = custom_topic.strip() or "Quantitative Aptitude"
                st.rerun()

        active_topic = st.session_state.get('active_topic', custom_topic.strip() or "Quantitative Aptitude")

        # Quick topic pills
        st.caption("Or choose a featured domain:")
        cols = st.columns(4)
        for i, qt in enumerate(FEATURED_TOPICS):
            with cols[i % 4]:
                if st.button(qt["label"], use_container_width=True, key=f"topic_pill_{i}"):
                    st.session_state.active_topic = qt["topic"]
                    st.rerun()

    st.markdown("---")

    # 2. Huddle Progression Ladder for this topic
    unlocked_tier = st.session_state.unlocked_huddles.get(active_topic, 1)
    seen_list = st.session_state.seen_questions.get(active_topic, [])

    col_h_title, col_h_stats = st.columns([2, 1])
    with col_h_title:
        st.subheader(f"2. Huddle Ladder: {active_topic}")
    with col_h_stats:
        st.info(f"🏆 Unlocked: **Tier {unlocked_tier}/5** | 👁️ AI Seen: **{len(seen_list)} unique questions**")

    # Render each huddle card
    for huddle in HUDDLE_DEFINITIONS:
        h_num = huddle["number"]
        is_unlocked = (h_num <= unlocked_tier)
        best_score_key = f"{active_topic}_huddle_{h_num}"
        best_score = st.session_state.huddle_bests.get(best_score_key)

        with st.container():
            col_info, col_action = st.columns([3, 1])
            
            with col_info:
                if is_unlocked:
                    st.markdown(f"### ✅ **HUDDLE {h_num:02d}: {huddle['name']}**")
                    st.markdown(f"`{huddle['badge']}` • **Benchmark:** {huddle['exam']}")
                    st.write(f"_{huddle['description']}_")
                    if best_score is not None:
                        st.caption(f"⭐ Personal Best: **{best_score['score']}/{best_score['total']}** ({best_score['accuracy']:.0f}%)")
                else:
                    st.markdown(f"### 🔒 **HUDDLE {h_num:02d}: {huddle['name']}**")
                    st.markdown(f"`{huddle['badge']}` • **Benchmark:** {huddle['exam']}")
                    st.caption(f"Score **70%+** on Huddle {h_num - 1} to unlock this tier.")

            with col_action:
                st.write("")
                st.write("")
                if is_unlocked:
                    btn_type = "primary" if h_num == unlocked_tier else "secondary"
                    if st.button(f"▶ Play Tier {h_num}", key=f"start_huddle_{h_num}", type=btn_type, use_container_width=True):
                        launch_huddle(active_topic, huddle)
                else:
                    st.button("🔒 Locked", key=f"locked_btn_{h_num}", disabled=True, use_container_width=True)

            st.markdown("---")

def launch_huddle(topic, huddle):
    """Generates unique questions live via AI and launches the quiz (No predefined fallback)."""
    gemini = GeminiService()

    if not gemini.is_configured:
        st.error("🔑 Please set your `GEMINI_API_KEY` in the `.env` file to generate live questions.")
        return

    previous_questions = st.session_state.seen_questions.get(topic, [])

    with st.spinner(f"🤖 generating 5 brand-new {huddle['exam']} questions for '{topic}' (guaranteeing zero repeats)..."):
        start_time = time.time()
        questions = gemini.generate_huddle_quiz(
            topic=topic,
            huddle_number=huddle['number'],
            num_questions=5,
            previous_questions=previous_questions
        )
        duration = time.time() - start_time
        QUIZ_GENERATION_DURATION.labels(topic=topic, huddle_tier=huddle['number']).observe(duration)

        if questions:
            # Register newly seen questions to guarantee zero repeats in future
            if topic not in st.session_state.seen_questions:
                st.session_state.seen_questions[topic] = []
            for q in questions:
                q_text = q.get('question', '').strip()
                if q_text and q_text not in st.session_state.seen_questions[topic]:
                    st.session_state.seen_questions[topic].append(q_text)

            st.session_state.quiz_topic = topic
            st.session_state.current_huddle_number = huddle['number']
            st.session_state.current_huddle_info = huddle
            st.session_state.quiz_questions = questions
            st.session_state.question_count = len(questions)
            st.session_state.current_question_index = 0
            st.session_state.score = 0
            st.session_state.answers_log = []
            st.session_state.answer_submitted = False
            st.session_state.quiz_start_time = time.time()
            st.session_state.pop('ai_performance_feedback', None)
            st.session_state.current_page = 'quiz'
            st.rerun()
        else:
            if GeminiService._auth_failed:
                st.error("❌ API authentication failed (401). Please check the API key in your `.env` file (ensure it is a valid Google AI Studio key).")
            else:
                st.error("⚠️ unable to generate questions for this topic right now. Please verify your internet connection or try again.")
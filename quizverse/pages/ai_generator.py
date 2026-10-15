import streamlit as st
from services.gemini_service import GeminiService
from database.db import get_db
from database.models import Category, Topic

def ai_generator_page():
    st.title("🤖 AI Quiz Generator")

    gemini_service = GeminiService()
    if not gemini_service.is_configured:
        st.warning("⚠️ **Gemini API Key Required**")
        st.info(
            "To generate dynamic, custom quizzes with Google Gemini, "
            "obtain an API key from Google AI Studio and set `GEMINI_API_KEY=your_key` in `quizverse/.env`."
        )
        st.caption("You can still play all standard Huddles and Quizzes using built-in questions without an API key!")
        return

    db = next(get_db())
    categories = db.query(Category).all()
    category_names = [c.name for c in categories]

    selected_category_name = st.selectbox("Category", category_names)
    selected_topic_name = "General"
    
    if selected_category_name:
        selected_category = db.query(Category).filter_by(name=selected_category_name).first()
        topics = db.query(Topic).filter_by(category_id=selected_category.id).all()
        topic_names = [t.name for t in topics] or ["General"]
        selected_topic_name = st.selectbox("Topic", topic_names)
    
    difficulty = st.slider("Difficulty", 1, 20, 5)
    num_questions = st.number_input("Number of Questions", 1, 20, 5)
    question_type = st.selectbox("Question Type", ["mcq"])

    if st.button("✨ Generate AI Quiz", type="primary"):
        if not selected_category_name:
            st.error("Please select a category.")
            return

        with st.spinner("Contacting to generate custom questions..."):
            questions = []
            for i in range(num_questions):
                question = gemini_service.generate_question(
                    category=selected_category_name,
                    topic=selected_topic_name,
                    difficulty=difficulty,
                    question_type=question_type,
                    previous_questions=[q["question"] for q in questions]
                )
                if question:
                    questions.append(question)
                else:
                    st.warning(f"Could only generate {len(questions)}/{num_questions} questions.")
                    break
        
        if questions:
            st.success(f"Generated {len(questions)} questions!")
            st.session_state.ai_quiz = questions
            st.session_state.selected_category = {
                'id': selected_category.id if selected_category else 'quant',
                'name': selected_category_name
            }
            st.session_state.current_page = 'ai_quiz_start'
            st.rerun()

def ai_quiz_start():
    st.title("🎯 AI Generated Quiz Ready")
    if 'ai_quiz' in st.session_state and st.session_state.ai_quiz:
        st.write(f"Your custom quiz has **{len(st.session_state.ai_quiz)} questions** ready.")
        if st.button("🚀 Start Quiz", type="primary", use_container_width=True):
            st.session_state.quiz_questions = list(st.session_state.ai_quiz)
            st.session_state.question_count = len(st.session_state.ai_quiz)
            st.session_state.current_question_index = 0
            st.session_state.score = 0
            st.session_state.streak = 0
            st.session_state.total_xp = 0
            st.session_state.quiz_started = True
            st.session_state.current_page = 'quiz'
            st.rerun()
    else:
        st.warning("No quiz generated yet.")
        if st.button("Go to AI Generator"):
            st.session_state.current_page = 'ai_generator'
            st.rerun()
import streamlit as st
import time
from services.gemini_service import GeminiService

import re

def clean_opt(val):
    s = str(val).strip().lower()
    # Strip common option prefixes: 'a) ', 'b. ', '(c) ', 'option a: '
    s = re.sub(r'^(option\s+)?[a-d1-4][\)\.\:\-]\s*', '', s)
    s = re.sub(r'^\([a-d1-4]\)\s*', '', s)
    s = s.strip().rstrip('.,;:!?')
    return s

def check_is_correct(selected, target):
    """Robust comparison between user's choice and the correct answer."""
    if selected is None or target is None:
        return False

    s_orig = str(selected).strip().lower()
    t_orig = str(target).strip().lower()

    if s_orig == t_orig:
        return True

    s = clean_opt(selected)
    t = clean_opt(target)

    if s == t:
        return True

    # Numeric comparison (handle '43,200' vs '43200', '24' vs '24.0')
    s_num_str = s.replace(',', '').replace(' ', '')
    t_num_str = t.replace(',', '').replace(' ', '')
    try:
        if float(s_num_str) == float(t_num_str):
            return True
    except ValueError:
        pass

    # Handle unit suffixes like '200 m' vs '200' or '12 cm²' vs '12'
    s_core = re.sub(r'[^\d\.\-]', '', s)
    t_core = re.sub(r'[^\d\.\-]', '', t)
    if s_core and t_core:
        try:
            if float(s_core) == float(t_core) and abs(float(s_core)) > 0:
                s_words = set(re.findall(r'[a-z]+', s))
                t_words = set(re.findall(r'[a-z]+', t))
                if not s_words or not t_words or s_words == t_words:
                    return True
        except ValueError:
            pass

    return False

def quiz_page():
    if 'quiz_questions' not in st.session_state or not st.session_state.quiz_questions:
        st.session_state.current_page = 'home'
        st.rerun()
        return

    # Check if all questions are finished
    if st.session_state.current_question_index >= len(st.session_state.quiz_questions):
        st.session_state.current_page = 'results'
        st.rerun()
        return

    topic = st.session_state.get('quiz_topic', 'Quiz')
    h_info = st.session_state.get('current_huddle_info', {})
    h_num = st.session_state.get('current_huddle_number', 1)
    h_badge = h_info.get('badge', f'Tier {h_num}')
    h_name = h_info.get('name', f'Huddle {h_num}')
    h_exam = h_info.get('exam', 'Exam Level')
    curr_idx = st.session_state.current_question_index
    total = len(st.session_state.quiz_questions)
    q_data = st.session_state.quiz_questions[curr_idx]

    # Header bar
    col_t, col_badge = st.columns([3, 1])
    with col_t:
        st.markdown(f"#### 📖 **{topic}** — {h_badge} {h_name}")
        st.caption(f"🎯 Target: **≥70% (4/5)** to unlock next tier • 🏛️ Benchmark: **{h_exam}**")
    with col_badge:
        st.markdown(f"**Level:** `{h_badge}`")

    # Progress bar
    progress_val = curr_idx / total
    st.progress(progress_val)
    st.caption(f"Question {curr_idx + 1} of {total} • Zero-repeat mode active")

    if st.session_state.get('answer_submitted'):
        display_feedback(curr_idx, total)
    else:
        display_question_card(curr_idx, q_data)

def display_question_card(curr_idx, q_data):
    st.markdown("---")
    st.markdown(f"### {q_data['question']}")

    # Hint button
    gemini = GeminiService()

    col_hint, col_space = st.columns([1, 4])
    with col_hint:
        if 'hint' not in st.session_state:
            if st.button("💡 Get Hint"):
                with st.spinner("Thinking..."):
                    hint_text = gemini.generate_hint(
                        q_data['question'],
                        q_data['options'],
                        q_data['correct_answer']
                    )
                    st.session_state.hint = hint_text
                st.rerun()

    if 'hint' in st.session_state:
        st.info(f"**Hint:** {st.session_state.hint}")

    options = [str(opt) for opt in q_data['options']]
    selected_option = st.radio(
        "Select your answer:",
        options,
        index=None,
        key=f"user_ans_{curr_idx}"
    )

    st.markdown("---")
    col_sub, col_abort = st.columns([2, 1])
    with col_sub:
        if st.button("Submit Answer", type="primary", use_container_width=True):
            if selected_option is None:
                st.warning("⚠️ Please select an answer before clicking Submit!")
            else:
                process_answer(selected_option, q_data)
    with col_abort:
        if st.button("Quit to Home", use_container_width=True):
            st.session_state.current_page = 'home'
            st.rerun()

def process_answer(selected_option, q_data):
    target = q_data['correct_answer']
    is_correct = check_is_correct(selected_option, target)

    if is_correct:
        st.session_state.score += 1

    # Record answer
    st.session_state.answers_log.append({
        'question': q_data['question'],
        'selected_answer': str(selected_option),
        'correct_answer': str(target),
        'correct': is_correct,
        'explanation': q_data.get('explanation', f"The correct answer is {target}.")
    })

    st.session_state.last_feedback = {
        'correct': is_correct,
        'selected': str(selected_option),
        'target': str(target),
        'explanation': q_data.get('explanation', f"The correct answer is {target}.")
    }
    st.session_state.answer_submitted = True
    st.rerun()

def display_feedback(curr_idx, total):
    fb = st.session_state.get('last_feedback', {})

    if fb.get('correct'):
        st.success("🎉 **Correct! Well done.**")
        st.balloons()
    else:
        st.error("❌ **Incorrect**")
        st.write(f"Your answer: **{fb.get('selected')}**")
        st.write(f"Correct answer: **{fb.get('target')}**")

    with st.expander("📖 Explanation", expanded=True):
        st.markdown(fb.get('explanation'))

    is_last = (curr_idx + 1 >= total)
    button_label = "🏁 View Performance & AI Feedback →" if is_last else "Next Question →"

    if st.button(button_label, type="primary", use_container_width=True):
        st.session_state.current_question_index += 1
        st.session_state.answer_submitted = False
        st.session_state.pop('hint', None)
        st.session_state.pop('last_feedback', None)

        if is_last:
            st.session_state.current_page = 'results'
        st.rerun()
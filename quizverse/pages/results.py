import streamlit as st
import time
from services.gemini_service import GeminiService, HUDDLE_DEFINITIONS
from pages.quiz_creator import launch_huddle
from metrics import QUIZZES_COMPLETED

def results_page():
    if 'answers_log' not in st.session_state or not st.session_state.answers_log:
        st.session_state.current_page = 'home'
        st.rerun()
        return

    # Prometheus: count each finished quiz exactly once (Streamlit reruns this page on every click)
    quiz_id = st.session_state.get('quiz_start_time')
    if quiz_id is not None and st.session_state.get('last_completed_quiz') != quiz_id:
        QUIZZES_COMPLETED.inc()
        st.session_state.last_completed_quiz = quiz_id

    topic = st.session_state.get('quiz_topic', 'Quiz')
    h_info = st.session_state.get('current_huddle_info', HUDDLE_DEFINITIONS[0])
    h_num = st.session_state.get('current_huddle_number', 1)
    answers = st.session_state.answers_log
    total = len(answers)
    score = st.session_state.get('score', sum(1 for a in answers if a.get('correct')))
    accuracy = (score / total * 100) if total > 0 else 0

    start_time = st.session_state.get('quiz_start_time', time.time() - 30)
    elapsed = max(5, int(time.time() - start_time))

    # Evaluate Huddle Progression
    is_cleared = (accuracy >= 70.0)
    
    # Update unlocked huddles in session state
    if 'unlocked_huddles' not in st.session_state:
        st.session_state.unlocked_huddles = {}
    current_unlocked = st.session_state.unlocked_huddles.get(topic, 1)
    if is_cleared and h_num >= current_unlocked and h_num < 5:
        st.session_state.unlocked_huddles[topic] = h_num + 1

    # Record / update personal best score
    if 'huddle_bests' not in st.session_state:
        st.session_state.huddle_bests = {}
    best_key = f"{topic}_huddle_{h_num}"
    existing_best = st.session_state.huddle_bests.get(best_key)
    if not existing_best or score > existing_best.get('score', 0):
        st.session_state.huddle_bests[best_key] = {
            'score': score,
            'total': total,
            'accuracy': accuracy
        }

    # Header
    st.title("🏆 Huddle Performance Analysis")
    st.markdown(f"#### **{topic}** — {h_info.get('badge', f'Tier {h_num}')} {h_info.get('name', '')}")
    st.caption(f"Benchmark Standard: **{h_info.get('exam', 'Competitive Exam')}** | Threshold to advance: **70%**")

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Final Score", f"{score} / {total}")
    with col2:
        st.metric("Accuracy", f"{accuracy:.1f}%")
    with col3:
        st.metric("Time Taken", f"{elapsed}s")
    with col4:
        avg_time = elapsed / max(1, total)
        st.metric("Avg / Question", f"{avg_time:.1f}s")

    # Outcome Banner
    if is_cleared:
        if h_num == 5:
            st.success("👑 **HALL OF FAME! You conquered Tier 5 Boss Level (CAT 99.9%ile / GATE AIR Top 100)!**")
            st.balloons()
        else:
            next_huddle = HUDDLE_DEFINITIONS[h_num]  # next index is h_num since definitions are 0-indexed
            st.success(f"🎉 **HUDDLE {h_num:02d} CLEARED!** You unlocked **Tier {h_num + 1}: {next_huddle['badge']} {next_huddle['name']}**!")
            st.balloons()
    else:
        st.warning(f"⚠️ **HUDDLE {h_num:02d} NOT CLEARED** (Scored {accuracy:.0f}%, needed 70% to unlock next tier). Review the analysis below and try again with brand-new, unrepeated questions!")

    st.markdown("---")

    # --- NEXT ACTION BUTTONS ---
    st.subheader("⚡ Next Action")
    if is_cleared and h_num < 5:
        next_huddle = HUDDLE_DEFINITIONS[h_num]
        col_next, col_retry, col_topic = st.columns([2, 1.5, 1.5])
        with col_next:
            if st.button(f"🚀 Advance to Tier {h_num + 1} ({next_huddle['badge']})", type="primary", use_container_width=True):
                launch_huddle(topic, next_huddle)
        with col_retry:
            if st.button(f"🔄 Replay Tier {h_num} (Fresh Qs)", use_container_width=True):
                launch_huddle(topic, h_info)
        with col_topic:
            if st.button("📚 Change Topic", use_container_width=True):
                clear_quiz_session()
                st.session_state.current_page = 'home'
                st.rerun()
    elif is_cleared and h_num == 5:
        col_boss, col_topic = st.columns(2)
        with col_boss:
            if st.button("🔄 Re-challenge Boss Level (Fresh Qs)", type="primary", use_container_width=True):
                launch_huddle(topic, h_info)
        with col_topic:
            if st.button("📚 Choose Another Topic", use_container_width=True):
                clear_quiz_session()
                st.session_state.current_page = 'home'
                st.rerun()
    else:
        col_retry, col_topic = st.columns(2)
        with col_retry:
            if st.button(f"🔄 Retry Huddle {h_num:02d} with Fresh Questions", type="primary", use_container_width=True):
                launch_huddle(topic, h_info)
        with col_topic:
            if st.button("📚 Switch Topic", use_container_width=True):
                clear_quiz_session()
                st.session_state.current_page = 'home'
                st.rerun()

    st.markdown("---")

    # --- AI PERFORMANCE COACH REPORT ---
    st.subheader("🤖 Gemini AI Performance Coach")
    
    if 'ai_performance_feedback' not in st.session_state:
        with st.spinner("Analyzing your responses against competitive exam standards..."):
            gemini = GeminiService()
            feedback = gemini.generate_performance_feedback(
                topic=topic,
                huddle_info=h_info,
                total_questions=total,
                correct_count=score,
                time_taken=elapsed,
                answers_summary=answers
            )
            st.session_state.ai_performance_feedback = feedback

    with st.container():
        st.markdown(st.session_state.ai_performance_feedback)

    st.markdown("---")

    # --- DETAILED QUESTION-BY-QUESTION REVIEW ---
    with st.expander("📝 Detailed Question Review & Solutions", expanded=True):
        for idx, item in enumerate(answers):
            status = "✅ Correct" if item.get('correct') else "❌ Incorrect"
            st.markdown(f"**Q{idx + 1}: {item['question']}** ({status})")
            st.write(f"- **Your Answer:** `{item['selected_answer']}`")
            st.write(f"- **Correct Answer:** `{item['correct_answer']}`")
            st.info(f"**Explanation:** {item.get('explanation', 'N/A')}")
            st.markdown("---")

def clear_quiz_session():
    for key in [
        'quiz_topic', 'quiz_questions', 'question_count',
        'current_question_index', 'score', 'answers_log',
        'answer_submitted', 'hint', 'last_feedback',
        'ai_performance_feedback', 'quiz_start_time',
        'current_huddle_number', 'current_huddle_info'
    ]:
        st.session_state.pop(key, None)
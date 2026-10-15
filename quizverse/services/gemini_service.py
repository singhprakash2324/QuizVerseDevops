import random
import os
import json
import logging
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HUDDLE_DEFINITIONS = [
    {
        "number": 1,
        "name": "Foundations & Fundamentals",
        "badge": "🌱 Tier 1: Foundations",
        "exam": "Concept & Fundamentals",
        "pass_target": 70,
        "description": "Essential formulas, core definitions, and direct calculation checks.",
        "difficulty_prompt": "Foundational & clear. Test core definitions, basic formulas, and direct problem solving with zero ambiguity."
    },
    {
        "number": 2,
        "name": "SSC CGL & Banking PO Level",
        "badge": "⚡ Tier 2: SSC / Bank PO",
        "exam": "SSC CGL Tier-1 / IBPS PO",
        "pass_target": 70,
        "description": "Standard competitive exam questions with speed traps and elimination patterns.",
        "difficulty_prompt": "Calibrated directly to SSC CGL Tier-1, IBPS Bank PO, and campus aptitude levels. Include realistic distractors, standard calculation traps, and speed-optimized problem structures."
    },
    {
        "number": 3,
        "name": "GATE & UPSC CSAT Level",
        "badge": "🔬 Tier 3: GATE / CSAT",
        "exam": "GATE General / CSAT",
        "pass_target": 70,
        "description": "Rigorous conceptual questions, edge-cases, and 2-3 step analytical deductions.",
        "difficulty_prompt": "Calibrated directly to GATE (Graduate Aptitude Test in Engineering) General Aptitude/CS and UPSC CSAT. Problems must require 2-3 logical steps, deep conceptual rigor, boundary constraints, and precise mathematical/logical deduction."
    },
    {
        "number": 4,
        "name": "CAT Exam Level (QA / DILR / VARC)",
        "badge": "🔥 Tier 4: CAT Exam Level",
        "exam": "CAT (IIM Entrance)",
        "pass_target": 70,
        "description": "High-order reasoning, subtle distractors, multi-concept synthesis.",
        "difficulty_prompt": "Calibrated directly to CAT (Common Admission Test for IIMs) Quantitative Aptitude, DILR, or VARC. Questions must feature subtle trap options, non-trivial mathematical deduction, multi-variable logic, and test creative problem-solving rather than rote formula application."
    },
    {
        "number": 5,
        "name": "👑 Boss Huddle: CAT 99.9%ile & GATE Top Ranker",
        "badge": "👑 Tier 5: CAT 99th %ile",
        "exam": "CAT 99.9%ile / GATE AIR Top 100",
        "pass_target": 70,
        "description": "Extreme synthesis of multiple concepts, high-order thinking, and novel problem scenarios.",
        "difficulty_prompt": "Extreme master level equivalent to CAT 99.9th percentile and GATE Top Ranker benchmark. Questions must require synthesizing 2 or more distinct mathematical/logical concepts, with intricate constraints, novel problem formulations, and highly sophisticated distractors designed to catch common cognitive biases."
    }
]

class GeminiService:
    _auth_failed = False

    def __init__(self, override_key=None):
        # Load from current dir or parent dir .env
        load_dotenv()
        try:
            from pathlib import Path
            base = Path(__file__).resolve().parent.parent
            load_dotenv(base / '.env')
            load_dotenv(base.parent / '.env')
        except Exception:
            pass

        self.api_key = (
            override_key
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
            or ""
        ).strip()

        is_invalid = (
            not self.api_key
            or self.api_key == "your_api_key_here"
        )

        if is_invalid:
            self.is_configured = False
            self.model = None
            return

        self.is_configured = True
        self.model = None
        try:
            genai.configure(api_key=self.api_key)
            for m_candidate in ['gemini-2.5-flash', 'gemini-flash-latest', 'gemini-1.5-flash']:
                try:
                    self.model = genai.GenerativeModel(m_candidate)
                    break
                except Exception:
                    continue
            if not self.model:
                self.model = genai.GenerativeModel('gemini-2.5-flash')
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini model: {e}")
            self.is_configured = False

    def generate_huddle_quiz(self, topic, huddle_number=1, num_questions=5, previous_questions=None):
        """
        Generates exam-calibrated questions for a specific topic and huddle level.
        Enforces strict zero-repetition against previous_questions.
        """
        if previous_questions is None:
            previous_questions = []

        huddle = next((h for h in HUDDLE_DEFINITIONS if h["number"] == huddle_number), HUDDLE_DEFINITIONS[0])

        if not self.is_configured or not self.model or GeminiService._auth_failed:
            return None

        # Build avoidance snippet for prompt
        avoid_snippet = ""
        if previous_questions:
            # Provide up to last 20 question texts to avoid bloating prompt
            recent_avoid = previous_questions[-20:]
            avoid_snippet = f"""
        **CRITICAL ZERO-REPETITION CONSTRAINT:**
        The user has ALREADY answered the following questions on this topic. You MUST NOT repeat, duplicate, or rephrase any of these:
        {json.dumps(recent_avoid, indent=2)}
        Ensure every question generated is 100% fresh, novel, and unique!
        """

        prompt = f"""
        You are a premier test designer for top competitive examinations (CAT, GATE, SSC CGL).
        Generate an elite quiz for the following topic and difficulty tier.

        **Topic:** {topic}
        **Huddle Level:** Huddle {huddle['number']} - {huddle['name']}
        **Exam Target Benchmark:** {huddle['exam']}
        **Difficulty Calibration:** {huddle['difficulty_prompt']}
        **Number of Questions:** {num_questions}
        {avoid_snippet}

        **Instructions:**
        1. Create exactly {num_questions} multiple-choice questions calibrated strictly to the benchmark examination standard.
        2. For CAT/GATE tiers (Huddles 3, 4, 5): craft sophisticated, realistic problem statements with realistic distractors (options designed around common calculation mistakes or misread constraints).
        3. Each question must have exactly 4 distinct options.
        4. Exactly ONE option must be strictly correct.
        5. Provide a detailed, step-by-step educational explanation for the solution.
        6. Respond ONLY with a valid JSON array matching the schema below. No markdown fences, no conversational text.

        **JSON Schema:**
        [
          {{
            "question": "Problem statement text here...",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": "Option A",
            "explanation": "Detailed step-by-step solution and reasoning."
          }}
        ]
        """

        for attempt in range(2):
            try:
                response = self.model.generate_content(prompt)
                cleaned = response.text.strip().replace("```json", "").replace("```", "").strip()
                start = cleaned.find('[')
                end = cleaned.rfind(']')
                if start != -1 and end != -1:
                    cleaned = cleaned[start:end+1]
                data = json.loads(cleaned)

                if isinstance(data, list) and len(data) > 0:
                    validated = []
                    seen_lower = {q.strip().lower() for q in previous_questions}

                    for item in data:
                        q_text = item.get("question", "").strip()
                        if (
                            q_text
                            and q_text.lower() not in seen_lower
                            and "options" in item
                            and isinstance(item["options"], list)
                            and len(item["options"]) >= 2
                            and "correct_answer" in item
                        ):
                            if item["correct_answer"] not in item["options"]:
                                item["options"].append(item["correct_answer"])
                            validated.append(item)
                            seen_lower.add(q_text.lower())

                    if validated and len(validated) >= 1:
                        return validated[:num_questions]
            except Exception as e:
                err_str = str(e)
                if any(k in err_str for k in ["401", "Unauthenticated", "ACCESS_TOKEN_TYPE_UNSUPPORTED"]):
                    GeminiService._auth_failed = True
                    self.is_configured = False
                    logger.warning(f"Gemini authentication error: {e}")
                    return None
                logger.warning(f"Gemini huddle quiz generation attempt {attempt + 1} error: {e}")

        return None

    def generate_hint(self, question, options, correct_answer):
        """Generates a subtle, educational hint."""
        if not self.is_configured or not self.model or GeminiService._auth_failed:
            return "Tip: Eliminate options that conflict with foundational constraints and check intermediate calculation steps."

        prompt = f"""
        Provide a subtle 1-2 sentence hint for this question that guides the student's problem-solving approach WITHOUT revealing the answer.
        Question: {question}
        Options: {json.dumps(options)}
        Correct Answer: {correct_answer}
        Respond ONLY with the hint text.
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception:
            return "Tip: Eliminate options that conflict with foundational constraints and check intermediate calculation steps."

    def generate_performance_feedback(self, topic, huddle_info, total_questions, correct_count, time_taken, answers_summary):
        """
        Analyzes the user's test performance against the exam benchmark and generates actionable feedback.
        """
        accuracy = (correct_count / total_questions * 100) if total_questions > 0 else 0
        h_name = huddle_info.get("name", "Quiz")
        h_exam = huddle_info.get("exam", "Competitive Exam")

        if not self.is_configured or not self.model or GeminiService._auth_failed:
            status = "CLEARED! 🎉" if accuracy >= 70 else "NOT YET CLEARED (Need 70%+ to unlock next level)"
            feedback = f"""
### 📊 Performance Summary
- **Result:** {status}
- **Score:** **{correct_count}/{total_questions}** ({accuracy:.1f}%)
- **Huddle Tier:** {h_name} ({h_exam} Standard)
- **Time Elapsed:** {int(time_taken)} seconds (avg {time_taken / max(1, total_questions):.1f}s / question)

#### 🌟 Demonstrated Strengths
- Good foundational command on concepts answered correctly.
- Maintained a steady pace throughout the challenge.

#### 🎯 Exam Analysis & Traps
- For **{h_exam}** style questions, carefully analyze the boundary conditions and option distractors.
- Review any incorrect answers in the detailed breakdown below.
"""
            return feedback

        prompt = f"""
        You are an expert exam strategist and faculty coach for competitive exams ({h_exam}, CAT, GATE, SSC).
        A student has just completed:
        - Topic: {topic}
        - Huddle: {h_name} ({h_exam} Level)
        - Score: {correct_count} / {total_questions} ({accuracy:.1f}% accuracy)
        - Pass Benchmark: 70%
        - Time: {int(time_taken)}s
        - Detailed Questions & Responses:
        {json.dumps(answers_summary, indent=2)}

        Write a sharp, motivating, and highly insightful exam evaluation with clear Markdown sections:
        1. **Huddle Verdict**: Did they meet the {h_exam} passing standard (≥70%)? Briefly evaluate their exam readiness.
        2. **Mastery Highlights**: Specific concepts/techniques they demonstrated strong competence in.
        3. **Exam Trap & Gap Analysis**: Deep dive into the questions they missed. What was the trap distractor, and what conceptual gap or calculation pitfall caught them?
        4. **Targeted Strategy for Next Tier**: 2-3 specific exam techniques or revision formulas to master before attempting the next level.
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.warning(f"Gemini feedback generation error: {e}")
            return f"""
### 📊 Performance Summary
You scored **{correct_count}/{total_questions}** ({accuracy:.1f}%) on **{topic} - {h_name}**.
Review the questions and step-by-step solutions below to reinforce your exam readiness!
"""
# QuizVerse AI — Pure Gemini-Powered Real-Time Exam Huddles

**Learn. Challenge. Level Up.**

QuizVerse AI is a friction-free, real-time quiz application powered 100% by Google Gemini AI. It generates on-demand questions, hints, and exam-calibrated performance reviews with **zero predefined questions** and **zero repeated questions**.

---

## ⚡ Core Architecture

- **100% Google Gemini AI Engine**: All questions, options, hints, explanations, and coaching evaluations are generated live via Gemini 1.5 Flash. Predefined questions have been completely removed.
- **Zero Authentication / Zero Database**: No login, sign-up, or persistent database required. Progression, personal bests, and question histories run dynamically in memory (`st.session_state`).
- **5 Competitive Exam-Calibrated Tiers**:
  1. **Tier 1: Foundations** (`Concept & Fundamentals`)
  2. **Tier 2: SSC / Bank PO** (`SSC CGL Tier-1 / IBPS PO Speed & Calculation Traps`)
  3. **Tier 3: GATE / CSAT** (`GATE General Aptitude / UPSC CSAT 2-3 Step Analytical Deduction`)
  4. **Tier 4: CAT Exam Level** (`CAT IIM Entrance QA / DILR / VARC Trap Distractors & Multi-Variable Logic`)
  5. **Tier 5: 👑 Boss Level** (`CAT 99.9th Percentile / GATE AIR Top 100 Multi-Concept Synthesis`)
- **Strict Zero-Repetition Guarantee**: Previously seen questions for any topic are tracked in memory and strictly prohibited in subsequent Gemini prompts.
- **70% Advance Threshold**: Scoring $\ge 70\%$ unlocks the next exam tier.

---

## 📂 Project Structure

```
quizverse/
├── README.md                 # Project documentation
├── requirements.txt          # Python dependencies (Streamlit, python-dotenv, google-generativeai)
├── app.py                    # Application entry point & sidebar API key management
├── config/
│   └── settings.py           # Environment settings loader
├── pages/
│   ├── quiz_creator.py       # Topic launcher, API key prompt, and 5-tier Huddle progression ladder
│   ├── quiz.py               # Active quiz interface, live AI hints, answer verification
│   └── results.py            # AI Performance Coach review, tier unlock advancement
├── services/
│   └── gemini_service.py     # Gemini 1.5 Flash question generation & coaching engine
└── static/
    └── style.css             # UI styling
```

---

## 🚀 How to Run

1. **Activate Environment**:
   ```bash
   source venv/bin/activate
   ```

2. **Configure Gemini API Key** (optional via `.env`):
   ```bash
   # In .env:
   GEMINI_API_KEY=AIzaSy...
   ```
   *(You can also paste your API key directly in the web UI when prompted)*

3. **Start the App**:
   ```bash
   streamlit run quizverse/app.py
   ```

4. Open your browser at **`http://localhost:8501`**.
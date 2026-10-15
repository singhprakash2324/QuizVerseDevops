"""Centralized Prometheus metrics for QuizVerse.

Import the metric objects wherever they are needed:

    from metrics import PAGE_VIEWS, QUIZ_GENERATION_DURATION, QUIZZES_COMPLETED

Call start_metrics_server() once (from app.py) to expose them at
http://<host>:8001/metrics, which is the endpoint Prometheus scrapes.
"""
import threading

from prometheus_client import Counter, Histogram, start_http_server

METRICS_PORT = 8001

# Exposed as page_views_total{page="..."}
PAGE_VIEWS = Counter(
    "page_views",
    "Number of times each page of the quiz application was viewed",
    ["page"],
)

# Exposed as quiz_generation_duration_seconds_bucket / _sum / _count
QUIZ_GENERATION_DURATION = Histogram(
    "quiz_generation_duration_seconds",
    "Time taken to generate a quiz with the Gemini API",
    ["topic", "huddle_tier"],
    buckets=(0.5, 1, 2, 3, 5, 8, 13, 20, 30, 60),
)

# Exposed as quizzes_completed_total
QUIZZES_COMPLETED = Counter(
    "quizzes_completed",
    "Number of quizzes completed by users",
)

_server_started = False
_lock = threading.Lock()


def start_metrics_server(port: int = METRICS_PORT) -> None:
    """Start the Prometheus HTTP server once per process.

    Streamlit re-runs the script on every interaction, so this is guarded
    to avoid 'Address already in use' errors.
    """
    global _server_started
    with _lock:
        if _server_started:
            return
        try:
            start_http_server(port)
        except OSError:
            # Port already bound (e.g. server started by an earlier run)
            pass
        _server_started = True
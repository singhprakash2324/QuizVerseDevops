import sys
from metrics import start_metrics_server
start_metrics_server()
from streamlit.web import cli as stcli
sys.argv = ["streamlit", "run", "app.py", "--server.port=8501",
            "--server.address=0.0.0.0", "--server.headless=true",
            "--server.fileWatcherType=none"]
stcli.main()

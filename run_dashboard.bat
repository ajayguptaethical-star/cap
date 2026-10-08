@echo off
REM ==============================================================================
REM Launch FeedbackIQ Streamlit Interactive Dashboard on Windows
REM Forces UTF-8 encoding to prevent Windows cp1252 charmap encoding errors
REM ==============================================================================
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo Starting FeedbackIQ Streamlit Dashboard on http://localhost:8501...
python -m streamlit run src/dashboard/app.py --server.port 8501
pause

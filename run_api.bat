@echo off
REM ==============================================================================
REM Launch FeedbackIQ FastAPI REST Service on Windows
REM Forces UTF-8 encoding
REM ==============================================================================
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo Starting FeedbackIQ FastAPI Backend on http://localhost:8000...
echo Swagger UI will be available at http://localhost:8000/docs
uvicorn src.api.app:app --port 8000 --reload
pause

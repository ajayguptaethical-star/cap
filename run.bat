@echo off
REM ==============================================================================
REM Launch FeedbackIQ Project (API and Dashboard)
REM ==============================================================================

echo Activating virtual environment...
if exist ".\.venv\Scripts\activate.bat" (
    call .\.venv\Scripts\activate.bat
) else (
    echo Warning: .venv not found. Relying on global Python environment.
)

set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo Starting FastAPI Backend...
start "FeedbackIQ API" cmd /k "uvicorn src.api.app:app --port 8000 --reload"

echo Starting Streamlit Dashboard...
start "FeedbackIQ Dashboard" cmd /k "python -m streamlit run src/dashboard/app.py --server.port 8501"

echo Waiting for services to start...
timeout /t 5 /nobreak >nul

echo Opening in Google Chrome...
start chrome http://localhost:8501
start chrome http://localhost:8000/docs

echo.
echo Both services are starting up in separate windows!
echo API Swagger UI: http://localhost:8000/docs
echo Dashboard:      http://localhost:8501
echo.
pause

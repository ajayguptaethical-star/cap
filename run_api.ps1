# ==============================================================================
# Launch FeedbackIQ FastAPI REST Service (PowerShell)
# ==============================================================================
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

Write-Host "Starting FeedbackIQ FastAPI Backend on http://localhost:8000..." -ForegroundColor Cyan
Write-Host "Swagger UI: http://localhost:8000/docs" -ForegroundColor Green
uvicorn src.api.app:app --port 8000 --reload

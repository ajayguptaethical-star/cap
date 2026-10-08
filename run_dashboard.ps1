# ==============================================================================
# Launch FeedbackIQ Streamlit Interactive Dashboard (PowerShell)
# Forces UTF-8 encoding to prevent Windows cp1252 charmap encoding errors
# ==============================================================================
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

Write-Host "Starting FeedbackIQ Streamlit Dashboard on http://localhost:8501..." -ForegroundColor Cyan
python -m streamlit run src/dashboard/app.py --server.port 8501

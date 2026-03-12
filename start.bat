@echo off
echo =======================================================
echo   Starting Credpanion - Agentic Credit Intelligence
echo =======================================================

echo.
echo [1/2] Starting FastAPI Backend on port 8000...
start "Credpanion Backend" cmd /k "uvicorn backend.main:app --reload --port 8000"

echo [2/2] Starting Next.js Frontend on port 3000...
start "Credpanion Frontend" cmd /k "cd frontend-next && npm run dev"

echo.
echo All services started!
echo Next.js Dashboard: http://localhost:3000
echo FastAPI Docs:      http://localhost:8000/docs
echo.
echo Close the terminal windows to stop the servers.
pause

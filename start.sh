#!/bin/bash
echo "======================================================="
echo "  Starting Credpanion - Agentic Credit Intelligence"
echo "======================================================="
echo

# Kill existing processes on ports 3000 and 8000
echo "Scanning for processes on ports 8000 and 3000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null

echo "[1/2] Starting FastAPI Backend on port 8000..."
uvicorn backend.main:app --reload --port 8000 &
BACKEND_PID=$!

echo "[2/2] Starting Next.js Frontend on port 3000..."
cd frontend-next && npm run dev &
FRONTEND_PID=$!

echo
echo "All services started!"
echo "Next.js Dashboard: http://localhost:3000"
echo "FastAPI Docs:      http://localhost:8000/docs"
echo
echo "Press Ctrl+C to stop servers."

# Wait for Ctrl+C
trap "echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT SIGTERM
wait

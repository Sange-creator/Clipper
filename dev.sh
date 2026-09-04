#!/usr/bin/env bash
# AI Video Clipper Pro - Unified Local Dev Server Runner
# Starts both FastAPI backend (port 8000) and Next.js frontend (port 3000) concurrently.

set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

# Clean shutdown of child processes on Ctrl+C or script termination
cleanup() {
  echo ""
  echo "🛑 Shutting down AI Video Clipper Pro services..."
  kill $(jobs -p) 2>/dev/null || true
  wait 2>/dev/null || true
  echo "👋 All services stopped."
}
trap cleanup EXIT INT TERM

echo "=========================================================="
echo "🎬 AI Video Clipper Pro — Starting Local Dev Environment"
echo "=========================================================="

# Check Python environment
if [ -f "$BACKEND_DIR/.venv/bin/uvicorn" ]; then
  UVICORN_CMD="$BACKEND_DIR/.venv/bin/uvicorn"
elif command -v uvicorn >/dev/null 2>&1; then
  UVICORN_CMD="uvicorn"
else
  echo "❌ Error: uvicorn not found in backend/.venv or system PATH."
  echo "Please set up the backend environment: cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -e ."
  exit 1
fi

# 1. Start FastAPI backend
echo "⚡ [1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ..."
(
  cd "$BACKEND_DIR"
  "$UVICORN_CMD" app.main:app --host 0.0.0.0 --port 8000 --reload
) &
BACKEND_PID=$!

# Wait briefly for backend to initialize
sleep 2

# 2. Start Next.js frontend
echo "✨ [2/2] Starting Next.js Frontend on http://localhost:3000 ..."
(
  cd "$FRONTEND_DIR"
  npm run dev
) &
FRONTEND_PID=$!

echo ""
echo "✅ Both services running:"
echo "   - Web App:   http://localhost:3000"
echo "   - API Docs:  http://127.0.0.1:8000/docs"
echo "   - Health:    http://127.0.0.1:8000/api/health"
echo "Press Ctrl+C at any time to stop both servers."
echo "=========================================================="

# Wait for both processes
wait

@echo off
REM Development startup script for Windows

echo Starting SHL Assessment Recommender...

REM Install dependencies
echo [1] Installing dependencies...
pip install -q -r requirements.txt

REM Build FAISS index if needed
if not exist "vectorstore\shl_index.faiss" (
    echo [2] Building FAISS index...
    python scripts/build_faiss_index.py
)

REM Start server
echo [3] Starting FastAPI server...
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

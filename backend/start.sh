#!/bin/bash
# Development startup script

echo "Starting SHL Assessment Recommender..."

# Install dependencies
echo "[1] Installing dependencies..."
pip install -q -r requirements.txt

# Load environment
if [ -f .env ]; then
    echo "[2] Loading .env file"
    export $(cat .env | xargs)
fi

# Build FAISS index if needed
if [ ! -f "vectorstore/shl_index.faiss" ]; then
    echo "[3] Building FAISS index..."
    python scripts/build_faiss_index.py || echo "Warning: FAISS index build failed"
fi

# Start server
echo "[4] Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

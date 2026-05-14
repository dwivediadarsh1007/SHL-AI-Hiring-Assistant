# SHL Assessment Recommender

A production-grade, AI-powered system that helps recruiters and hiring managers discover appropriate SHL assessments through natural conversation.

## 🏗️ Architecture

This project is divided into two separate applications to follow clean architecture principles:

1. **`/backend`**: A FastAPI application that handles vector search (FAISS), embeddings (sentence-transformers), prompt orchestration, guardrails, and Gemini LLM generation.
2. **`/frontend`**: A Next.js (React 18) frontend built with App Router, Tailwind CSS, and Lucide icons that provides a modern ChatGPT-style chat interface for recruiters.

## 🚀 Getting Started

### 1. Start the Backend

The backend needs to be running for the frontend to communicate with it.

```bash
cd backend
python -m venv venv
source venv/bin/activate  # (or venv\Scripts\activate on Windows)
pip install -r requirements.txt
```

Ensure your `.env` file is properly configured inside the `backend` folder:
```env
GEMINI_API_KEY=your_google_ai_studio_key
GEMINI_MODEL=gemini-2.5-flash
```

Run the FastAPI server:
```bash
python -m uvicorn app.main:app --reload
```
The backend will run on `http://localhost:8000`.

### 2. Start the Frontend

Open a **new terminal window** and navigate to the frontend directory:

```bash
cd frontend
npm install
```

Ensure you are using Node.js v20.9.0 or higher.
Start the Next.js development server:
```bash
npm run dev
```

Visit `http://localhost:3000` in your web browser to use the AI Hiring Assistant!

## ✨ Features

- **Conversational Assessment Recommendation**: Ask vague or specific hiring questions.
- **Intent Routing**: The agent automatically detects if you want to clarify, recommend, refine, compare, or refuse.
- **Guardrails**: Responses are 100% grounded in the real SHL catalog. Hallucinated URLs and assessments are strictly blocked.
- **Modern UI**: Clean, responsive Dashboard, Chat Interface, and Settings views built with Tailwind CSS.

## 📝 Deployment

- **Backend**: Can be easily deployed to Render or Railway using the included `render.yaml` or `Dockerfile`.
- **Frontend**: Best deployed to Vercel. Simply connect your GitHub repository and Vercel will auto-detect the Next.js framework. Make sure to set the `NEXT_PUBLIC_API_URL` environment variable to your deployed backend URL.

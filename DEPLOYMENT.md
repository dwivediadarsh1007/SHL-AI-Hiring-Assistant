# SHL Assessment Recommender - Deployment Guide

This guide covers deploying to Render and Railway platforms.

## Prerequisites

- GitHub repository with the code
- Gemini API key for LLM functionality

## Local Development

### Setup

```bash
# Clone repository
git clone <repo_url>
cd shl-recommender

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env .env.local
# Edit .env.local and add GEMINI_API_KEY
```

### Running Locally

**Option 1: Direct start**
```bash
./start.sh  # On Windows: start.bat
```

**Option 2: Manual**
```bash
# Build FAISS index (if not already built)
python scripts/build_faiss_index.py

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Option 3: Docker**
```bash
docker build -t shl-recommender .
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key shl-recommender
```

The API will be available at `http://localhost:8000`

## Render Deployment

### 1. Connect Repository

1. Go to [render.com](https://render.com)
2. Sign in with GitHub
3. Click "New +" → "Web Service"
4. Connect your GitHub repository

### 2. Configure Service

- **Name**: `shl-recommender`
- **Runtime**: `Python 3.11`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 3. Set Environment Variables

In the Render dashboard, add:
- `GEMINI_API_KEY`: Your Gemini API key

### 4. Deploy

Click "Deploy" and wait for the build to complete.

Your API will be available at: `https://shl-recommender.onrender.com`

### 5. Test Deployment

```bash
curl https://shl-recommender.onrender.com/health
```

Expected response:
```json
{"status": "ok"}
```

## Railway Deployment

### 1. Connect Repository

1. Go to [railway.app](https://railway.app)
2. Sign in with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository

### 2. Configure Environment Variables

In the Railway dashboard, add:
- `GEMINI_API_KEY`: Your Gemini API key
- `PYTHON_VERSION`: `3.11` (optional, inferred)

### 3. Deploy

Railway automatically detects `railway.toml` and deploys.

Your API will be available at the generated Railway domain.

### 4. Test Deployment

```bash
curl https://<your-railway-domain>/health
```

## Environment Variables

All configurations use environment variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | None | Google Gemini API key |
| `API_HOST` | No | `0.0.0.0` | API bind address |
| `API_PORT` | No | `8000` | API port |
| `RETRIEVAL_TOP_K` | No | `10` | Top-K retrieval results |
| `RETRIEVAL_RERANK_TOP_K` | No | `5` | Reranking results |
| `ENABLE_HYBRID_RETRIEVAL` | No | `true` | Use semantic + lexical search |
| `ENABLE_RERANKING` | No | `true` | Rerank results |
| `ENABLE_HALLUCINATION_GUARDS` | No | `true` | Validate against catalog |

## Testing the Deployment

### Health Check

```bash
curl https://<your-domain>/health
```

### Chat Endpoint

```bash
curl -X POST https://<your-domain>/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "I need to hire a backend developer"
      }
    ]
  }'
```

Expected response:
```json
{
  "reply": "Based on your requirements...",
  "recommendations": [
    {
      "name": "Assessment Name",
      "url": "https://www.shl.com/...",
      "test_type": "cognitive"
    }
  ],
  "end_of_conversation": false
}
```

## Monitoring

### Logs

**Render**: View in Render dashboard → Logs
**Railway**: View in Railway dashboard → Deployments → Logs

### Common Issues

1. **Service not starting**: Check `GEMINI_API_KEY` is set
2. **FAISS index errors**: Will fall back to in-memory search
3. **Timeout errors**: Increase timeout in deployment settings

## Scaling

### Render
- Change plan from "Free" to "Paid" for better performance
- Enable auto-scaling if needed

### Railway
- Increase instance size in Railway dashboard
- Deploy new instances for horizontal scaling

## Troubleshooting

### API returns 503 Service Unavailable

**Cause**: Dialog manager failed to initialize

**Solution**:
- Check `GEMINI_API_KEY` is set
- Check logs for initialization errors
- Redeploy

### No recommendations returned

**Cause**: FAISS index not built or retrieval failed

**Solution**:
- Index is built on first request (may take ~30s)
- Wait a moment and retry
- Check logs for retrieval errors

### Very slow responses

**Cause**: Model loading or FAISS search overhead

**Solution**:
- First request is slower (model loading)
- Subsequent requests are cached
- Consider upgrading to paid tier for better CPU

## Rolling Back

**Render**:
1. Go to Deployments
2. Select previous deployment
3. Click "Redeploy"

**Railway**:
1. Go to Deployments
2. Select previous deployment
3. Click "Rollback"

## Security Best Practices

1. **API Keys**: Keep `GEMINI_API_KEY` secret (use platform secrets, never commit)
2. **HTTPS**: Both Render and Railway enforce HTTPS
3. **Rate Limiting**: Implement rate limiting in production
4. **CORS**: Configure if using from frontend

## Cost Estimation

- **Render Free Tier**: Perfect for development/testing
- **Render Paid Tier**: ~$7/month for basic instance
- **Railway**: Pay-as-you-go (~$5-20/month depending on usage)

## Further Reading

- [Render Docs](https://render.com/docs)
- [Railway Docs](https://docs.railway.app)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

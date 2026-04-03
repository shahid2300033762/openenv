---
title: OpenEnv Workflow Evaluation Environment
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
tags:
  - openenv
  - reinforcement-learning
  - evaluation
  - agent-evaluation
  - workflow-automation
---

# OpenEnv Workflow Evaluation Environment

Production-grade AI evaluation framework for testing agents on real-world professional workflows.

## 🚀 Quick Start - Try It Now!

**👉 [Open Interactive API Documentation](/docs)** 👈

Click the link above to access the **Swagger UI** where you can:
- ✅ Test all API endpoints interactively
- ✅ See real-time responses
- ✅ Try different tasks (Email Triage, Data Cleaning, Code Review, Incident Response)
- ✅ Execute actions and see rewards

### Direct Links:
- **Interactive API Docs**: [/docs](/docs)
- **Alternative API Docs**: [/redoc](/redoc)
- **Health Check**: [/health](/health)

## Features

- 4 realistic tasks: Email Triage, Data Cleaning, Code Review, Incident Response
- 52 comprehensive tests with 85%+ coverage
- Full OpenEnv specification compliance
- Deterministic grading with semantic evaluation
- Chain-of-thought reasoning rewards
- Docker containerized for easy deployment

## API Endpoints

- `POST /reset` - Start a new environment session
- `POST /step` - Execute an action
- `GET /state/{session_id}` - Get current state
- `GET /health` - Health check

## Quick Test Example

1. Go to [/docs](/docs)
2. Click on **POST /reset**
3. Click "Try it out"
4. Use this JSON:
```json
{
  "task_name": "email_triage",
  "index": 0
}
```
5. Click "Execute" and see the response!

## Usage

See the [GitHub repository](https://github.com/shahid2300033762/openenv) for complete documentation.

## Environment Variables

For LLM-based inference (optional):
- `API_BASE_URL` - API endpoint for LLM
- `MODEL_NAME` - Model identifier
- `HF_TOKEN` - API key

## Deployment

This Space runs the FastAPI server defined in `server/app.py`.

To test locally:
```bash
docker build -t openenv-workflow .
docker run -p 7860:7860 openenv-workflow
```

Then visit: http://localhost:7860/health

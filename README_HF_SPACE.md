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

## Usage

See the [GitHub repository](https://github.com/yourusername/openenv-workflow-eval) for complete documentation.

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

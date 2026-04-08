"""
FastAPI server for the OpenEnv evaluation environment.

Exposes the environment via HTTP/WebSocket for remote access.
"""

from typing import Any, Dict, Optional

import json
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from pydantic import BaseModel as PydanticBaseModel, Field

from models import Action, Observation, Reward, State, StepResult
from tasks.email_triage.environment import EmailTriageEnvironment
from tasks.data_cleaning.environment import DataCleaningEnvironment
from tasks.code_review.environment import CodeReviewEnvironment
from tasks.incident_response.environment import IncidentResponseEnvironment


# In-memory session store
_sessions: dict = {}


class StepRequest(PydanticBaseModel):
    session_id: str
    action: Action


def _create_env(task_name: str, index: int = 0):
    if task_name == "email_triage":
        return EmailTriageEnvironment(email_index=index)
    elif task_name == "data_cleaning":
        return DataCleaningEnvironment()
    elif task_name == "code_review":
        return CodeReviewEnvironment(snippet_index=index)
    elif task_name == "incident_response":
        return IncidentResponseEnvironment(incident_index=index)
    raise ValueError(f"Unknown task: {task_name}")


# Create FastAPI app with OpenAPI docs enabled
app = FastAPI(
    title="OpenEnv Workflow Evaluation Environment",
    version="1.0.0",
    description="Production-grade AI evaluation for professional workflows",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to interactive API documentation."""
    return RedirectResponse(url="/docs")


@app.post("/reset")
async def reset(request: Request):
    """Reset the environment and create a new session.

    Accepts POST with no body, empty body, or JSON body with optional
    task_name and index fields.
    """
    task_name = "email_triage"
    index = 0

    # Try to parse JSON body — be maximally lenient
    try:
        body_bytes = await request.body()
        if body_bytes and body_bytes.strip():
            data = json.loads(body_bytes)
            if isinstance(data, dict):
                task_name = data.get("task_name", task_name)
                index = data.get("index", index)
    except Exception:
        # Any parse failure → use defaults, never error
        pass

    session_id = str(uuid.uuid4())
    env = _create_env(task_name, index)
    obs = env.reset()
    _sessions[session_id] = env

    return {
        "session_id": session_id,
        "observation": obs.model_dump(),
    }


@app.get("/state/{session_id}")
async def state(session_id: str):
    """Get current session state."""
    env = _sessions.get(session_id)
    if not env:
        raise HTTPException(404, "Session not found")
    return env.state().model_dump()


def _clamp_scores(obj, eps=0.001):
    """Recursively clamp all float values in a dict/list to strict (0, 1).
    
    This is the final safety net: no score field should ever be exactly 0.0 or 1.0
    in the API response, per competition rules.
    """
    if isinstance(obj, dict):
        return {k: _clamp_scores(v, eps) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_clamp_scores(item, eps) for item in obj]
    elif isinstance(obj, float):
        if obj <= 0.0:
            return eps
        if obj >= 1.0:
            return 1.0 - eps
        return obj
    return obj


@app.post("/step")
async def step(req: StepRequest):
    """Execute an action in the environment."""
    env = _sessions.get(req.session_id)
    if not env:
        raise HTTPException(404, "Session not found")
    result = env.step(req.action)
    response = result.model_dump()
    # Final safety: clamp all float values to strict (0, 1)
    response = _clamp_scores(response)
    return response


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}


def main():
    """Entry point for the server."""
    import uvicorn
    uvicorn.run(
        "server.app:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 7860)),
        reload=False,
    )


if __name__ == "__main__":
    main()

"""
FastAPI server for the OpenEnv evaluation environment.

Exposes the environment via HTTP/WebSocket for remote access.
"""

from __future__ import annotations

import json
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel as PydanticBaseModel

from models import Action, Observation, Reward, State, StepResult
from tasks.email_triage.environment import EmailTriageEnvironment
from tasks.data_cleaning.environment import DataCleaningEnvironment
from tasks.code_review.environment import CodeReviewEnvironment
from tasks.incident_response.environment import IncidentResponseEnvironment


app = FastAPI(
    title="OpenEnv Workflow Evaluation Environment",
    version="1.0.0",
    description="Production-grade AI evaluation for professional workflows",
)

# Enable CORS for all origins (required for validator)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
async def root():
    """Redirect to documentation."""
    return RedirectResponse(url="/docs")


# In-memory session store
_sessions: dict = {}


class CreateSessionRequest(PydanticBaseModel):
    task_name: str
    index: int = 0


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


@app.post("/reset", response_model=dict)
async def reset(
    task_name: str = "email_triage",
    index: int = 0,
    body: dict = Body(default=None, embed=False),
):
    """Create a new session and reset the environment.
    
    Accepts task_name and index either via:
    - JSON body: {"task_name": "email_triage", "index": 0}
    - Query parameters: ?task_name=email_triage&index=0
    - Defaults to email_triage
    """
    # Support both body (JSON) and query parameters
    if body and isinstance(body, dict) and "task_name" in body:
        task_name = body.get("task_name")
        index = body.get("index", index)
    
    if not task_name:
        task_name = "email_triage"
    
    session_id = str(uuid.uuid4())
    env = _create_env(task_name, index)
    obs = env.reset()
    _sessions[session_id] = env
    return {"session_id": session_id, "observation": obs.model_dump()}


@app.post("/step", response_model=dict)
async def step(req: StepRequest):
    """Execute an action in the environment."""
    env = _sessions.get(req.session_id)
    if not env:
        raise HTTPException(404, "Session not found")
    result = env.step(req.action)
    return result.model_dump()


@app.get("/state/{session_id}", response_model=dict)
async def state(session_id: str):
    """Get current session state."""
    env = _sessions.get(session_id)
    if not env:
        raise HTTPException(404, "Session not found")
    return env.state().model_dump()


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}

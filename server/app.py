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

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel as PydanticBaseModel, Field

from models import Action, Observation, Reward, State, StepResult
from tasks.email_triage.environment import EmailTriageEnvironment
from tasks.data_cleaning.environment import DataCleaningEnvironment
from tasks.code_review.environment import CodeReviewEnvironment
from tasks.incident_response.environment import IncidentResponseEnvironment


# In-memory session store
_sessions: dict = {}


class CreateSessionRequest(PydanticBaseModel):
    task_name: str = Field(default="email_triage")
    index: int = Field(default=0)


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


async def _reset_impl(request: Request):
    """Implementation of reset without FastAPI validation."""
    task_name = "email_triage"
    index = 0
    
    # Try to parse JSON body if Content-Type says JSON
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            # Read raw body to check if it exists
            body_bytes = await request.body()
            if body_bytes:
                body = json.loads(body_bytes)
                # body could be dict, None, or empty dict—all valid
                if isinstance(body, dict):
                    task_name = body.get("task_name", task_name)
                    index = body.get("index", index)
        except Exception:
            # Empty body, malformed JSON, or other error—use defaults
            pass
    
    # Create session
    session_id = str(uuid.uuid4())
    env = _create_env(task_name, index)
    obs = env.reset()
    _sessions[session_id] = env
    
    return {
        "session_id": session_id,
        "observation": obs.model_dump()
    }


# Create FastAPI app (WITHOUT CORS - we'll add it at wrapper level)
_fastapi_app = FastAPI(
    title="OpenEnv Workflow Evaluation Environment",
    version="1.0.0",
    description="Production-grade AI evaluation for professional workflows",
)


@_fastapi_app.get("/", include_in_schema=False)
async def root():
    """Redirect to documentation."""
    return RedirectResponse(url="/docs")


@_fastapi_app.get("/state/{session_id}", response_model=dict)
async def state(session_id: str):
    """Get current session state."""
    env = _sessions.get(session_id)
    if not env:
        raise HTTPException(404, "Session not found")
    return env.state().model_dump()


@_fastapi_app.post("/step", response_model=dict)
async def step(req: StepRequest):
    """Execute an action in the environment."""
    env = _sessions.get(req.session_id)
    if not env:
        raise HTTPException(404, "Session not found")
    result = env.step(req.action)
    return result.model_dump()


@_fastapi_app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


# Wrap FastAPI app with custom ASGI handler for /reset
class ResetHandlerASGI:
    def __init__(self, fastapi_app):
        self.fastapi_app = fastapi_app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["path"] == "/reset" and scope["method"] == "POST":
            # Handle /reset with custom logic, bypassing FastAPI validation
            request = Request(scope, receive)
            try:
                result = await _reset_impl(request)
                response = JSONResponse(result)
            except Exception as e:
                response = JSONResponse({"error": str(e)}, status_code=500)
            
            # Send response with CORS headers
            await send({
                "type": "http.response.start",
                "status": response.status_code,
                "headers": [
                    *response.headers.raw,
                    (b"access-control-allow-origin", b"*"),
                    (b"access-control-allow-methods", b"*"),
                    (b"access-control-allow-headers", b"*"),
                    (b"access-control-allow-credentials", b"true"),
                ],
            })
            await send({
                "type": "http.response.body",
                "body": response.body,
            })
        else:
            # All other routes go through FastAPI with CORS
            cors_app = CORSMiddleware(
                self.fastapi_app,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
            await cors_app(scope, receive, send)


# Replace with wrapped app
app = ResetHandlerASGI(_fastapi_app)

"""
FastAPI server for the OpenEnv evaluation environment.

Exposes the environment via HTTP/WebSocket for remote access.
"""

from typing import Optional

import json
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse as StarletteJSONResponse
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

# Add exception handler for validation errors on /reset
@_fastapi_app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors - return default session for /reset."""
    if request.url.path == "/reset":
        # Return default session instead of error
        session_id = str(uuid.uuid4())
        env = _create_env("email_triage", 0)
        obs = env.reset()
        _sessions[session_id] = env
        return JSONResponse({
            "session_id": session_id,
            "observation": obs.model_dump()
        })
    # For other endpoints, return the validation error
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


# Custom middleware to handle /reset validation errors
class ResetErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path == "/reset" and request.method == "POST":
            try:
                response = await call_next(request)
                # If it's a 422 error on /reset, convert to 200 with default
                if response.status_code == 422:
                    session_id = str(uuid.uuid4())
                    env = _create_env("email_triage", 0)
                    obs = env.reset()
                    _sessions[session_id] = env
                    return StarletteJSONResponse({
                        "session_id": session_id,
                        "observation": obs.model_dump()
                    })
                return response
            except Exception:
                # If there's any error, return default session
                session_id = str(uuid.uuid4())
                env = _create_env("email_triage", 0)
                obs = env.reset()
                _sessions[session_id] = env
                return StarletteJSONResponse({
                    "session_id": session_id,
                    "observation": obs.model_dump()
                })
        return await call_next(request)

_fastapi_app.add_middleware(ResetErrorHandlerMiddleware)

# Enable CORS for all origins (required for validator)
_fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


@_fastapi_app.post("/reset", include_in_schema=True)
async def reset_endpoint_sync(request: Request):
    """Create a new session and reset the environment.
    
    Accepts optional JSON body with task_name and index fields.
    Uses defaults: task_name="email_triage", index=0
    """
    task_name = "email_triage"
    index = 0
    
    # Try to read body if present
    try:
        body = await request.json()
        if isinstance(body, dict):
            task_name = body.get("task_name", task_name)
            index = body.get("index", index)
    except Exception:
        # No body or invalid JSON, use defaults
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


# Replace with wrapped app
app = _fastapi_app

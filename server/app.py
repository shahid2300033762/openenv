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
from starlette.routing import Route
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


# Create FastAPI app WITHOUT OpenAPI docs (remove validation hooks)
_fastapi_app = FastAPI(
    title="OpenEnv Workflow Evaluation Environment",
    version="1.0.0",
    description="Production-grade AI evaluation for professional workflows",
    openapi_url=None,  # Disable OpenAPI schema generation
    docs_url=None,  # Disable Swagger docs
    redoc_url=None,  # Disable ReDoc
)

# Don't add middleware for /reset - ASGI interceptor handles it directly
# Just enable CORS for other endpoints
_fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@_fastapi_app.get("/", include_in_schema=False)
async def root():
    """Root endpoint - API is ready."""
    return {"status": "ok", "version": "1.0.0"}


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


# ASGI wrapper that intercepts /reset BEFORE FastAPI validation
class ResetInterceptorASGI:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        # Only intercept POST /reset requests
        if scope["type"] == "http" and scope["path"] == "/reset" and scope["method"] == "POST":
            # Handle the request directly without going through FastAPI
            # Read the entire body first
            body_parts = []
            while True:
                message = await receive()
                body_parts.append(message.get("body", b""))
                if not message.get("more_body", False):
                    break
            
            body = b"".join(body_parts)
            task_name = "email_triage"
            index = 0
            
            # Try to parse JSON body (be very lenient)
            if body:
                try:
                    data = json.loads(body)
                    if isinstance(data, dict):
                        task_name = data.get("task_name", task_name)
                        index = data.get("index", index)
                except Exception as e:
                    # Silently ignore parse errors, use defaults
                    pass
            
            # Create session
            try:
                session_id = str(uuid.uuid4())
                env = _create_env(task_name, index)
                obs = env.reset()
                _sessions[session_id] = env
                
                # Send successful response
                response_body = json.dumps({
                    "session_id": session_id,
                    "observation": obs.model_dump()
                }).encode('utf-8')
                
                await send({
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"access-control-allow-origin", b"*"),
                        (b"access-control-allow-credentials", b"true"),
                        (b"content-length", str(len(response_body)).encode()),
                    ],
                })
                await send({
                    "type": "http.response.body",
                    "body": response_body,
                    "more_body": False,
                })
                return
            except Exception as e:
                # Even if something fails, try to send a 500 error response
                error_response = json.dumps({"error": str(e)}).encode('utf-8')
                await send({
                    "type": "http.response.start",
                    "status": 500,
                    "headers": [(b"content-type", b"application/json")],
                })
                await send({
                    "type": "http.response.body",
                    "body": error_response,
                })
                return
        
        # For all other requests, pass through to FastAPI
        await self.app(scope, receive, send)


@_fastapi_app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


# Wrap FastAPI app with ASGI interceptor for /reset endpoint
app = ResetInterceptorASGI(_fastapi_app)

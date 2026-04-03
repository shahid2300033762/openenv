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
from fastapi.responses import JSONResponse, HTMLResponse
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
    version="1.0.1",
    description="Production-grade AI evaluation for professional workflows",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - Welcome page with links to API docs."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>OpenEnv Workflow Evaluation Environment</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, sans-serif;
                max-width: 900px;
                margin: 50px auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                background: rgba(255, 255, 255, 0.95);
                padding: 40px;
                border-radius: 15px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                color: #333;
            }
            h1 {
                color: #667eea;
                margin-top: 0;
            }
            .hero {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 10px;
                margin-bottom: 30px;
                text-align: center;
            }
            .cta-button {
                display: inline-block;
                background: #4CAF50;
                color: white;
                padding: 15px 40px;
                text-decoration: none;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
                margin: 10px;
                transition: all 0.3s;
            }
            .cta-button:hover {
                background: #45a049;
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            }
            .secondary-button {
                background: #2196F3;
            }
            .secondary-button:hover {
                background: #0b7dda;
            }
            .features {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin: 30px 0;
            }
            .feature {
                background: #f5f5f5;
                padding: 20px;
                border-radius: 8px;
                border-left: 4px solid #667eea;
            }
            .feature h3 {
                margin-top: 0;
                color: #667eea;
            }
            .endpoint {
                background: #f9f9f9;
                border: 1px solid #ddd;
                padding: 10px 15px;
                margin: 10px 0;
                border-radius: 5px;
                font-family: monospace;
            }
            .badge {
                display: inline-block;
                background: #4CAF50;
                color: white;
                padding: 3px 10px;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
                margin-right: 10px;
            }
            .post { background: #2196F3; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="hero">
                <h1>🤖 OpenEnv Workflow Evaluation Environment</h1>
                <p style="font-size: 18px;">Production-grade AI evaluation for real-world professional workflows</p>
                <div style="margin-top: 30px;">
                    <a href="/docs" class="cta-button">📚 Interactive API Documentation</a>
                    <a href="/redoc" class="cta-button secondary-button">📖 Alternative Docs</a>
                </div>
            </div>
            
            <h2>🚀 Quick Start</h2>
            <p><strong>Click the "Interactive API Documentation" button above</strong> to access the Swagger UI where you can:</p>
            <ul>
                <li>✅ Test all endpoints interactively</li>
                <li>✅ See request/response examples</li>
                <li>✅ Try different tasks and actions</li>
                <li>✅ View reward scores in real-time</li>
            </ul>

            <h2>📋 Available Endpoints</h2>
            <div class="endpoint">
                <span class="badge post">POST</span> <strong>/reset</strong> - Create a new evaluation session
            </div>
            <div class="endpoint">
                <span class="badge post">POST</span> <strong>/step</strong> - Execute an action and get rewards
            </div>
            <div class="endpoint">
                <span class="badge">GET</span> <strong>/state/{session_id}</strong> - Get current session state
            </div>
            <div class="endpoint">
                <span class="badge">GET</span> <strong>/health</strong> - Health check
            </div>

            <div class="features">
                <div class="feature">
                    <h3>📧 Email Triage</h3>
                    <p>Customer support email processing with classification, prioritization, and response generation.</p>
                </div>
                <div class="feature">
                    <h3>🧹 Data Cleaning</h3>
                    <p>Tabular data quality improvement with error detection and correction.</p>
                </div>
                <div class="feature">
                    <h3>🔍 Code Review</h3>
                    <p>Pull request review with bug detection, fix suggestions, and optimization.</p>
                </div>
                <div class="feature">
                    <h3>🛡️ Incident Response</h3>
                    <p>Cybersecurity incident response with threat detection and remediation.</p>
                </div>
            </div>

            <h2>💡 Example Usage</h2>
            <ol>
                <li>Visit <a href="/docs" style="color: #667eea; font-weight: bold;">/docs</a></li>
                <li>Click on <strong>POST /reset</strong></li>
                <li>Click "Try it out"</li>
                <li>Enter: <code>{"task_name": "email_triage"}</code></li>
                <li>Click "Execute" and copy the session_id</li>
                <li>Use that session_id in <strong>POST /step</strong> to execute actions</li>
            </ol>

            <p style="text-align: center; margin-top: 40px;">
                <a href="https://github.com/shahid2300033762/openenv" style="color: #667eea;">
                    View on GitHub
                </a> | 
                <a href="/docs" style="color: #667eea;">API Docs</a> |
                <a href="/health" style="color: #667eea;">Health Check</a>
            </p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


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


@app.post("/step")
async def step(req: StepRequest):
    """Execute an action in the environment."""
    env = _sessions.get(req.session_id)
    if not env:
        raise HTTPException(404, "Session not found")
    result = env.step(req.action)
    return result.model_dump()


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

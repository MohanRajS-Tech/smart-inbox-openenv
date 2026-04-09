import os

from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from server.environment import SmartInboxEnv
from models import EmailAction, EmailObservation, EmailState

# Initialize the state-holding environment
env = SmartInboxEnv()

# MANDATORY: List of tasks for the OpenEnv validator to enumerate
TASKS = [
    {
        "id": "easy",
        "description": "Archive the 2 promotional emails (Pizza and Shoes) to declutter the inbox.",
        "difficulty": "easy"
    },
    {
        "id": "medium",
        "description": "Flag the 2 urgent alerts (Security and HR) while archiving the 2 newsletters.",
        "difficulty": "medium"
    },
    {
        "id": "hard",
        "description": "Flag 2 high-priority alerts AND move 2 project-related emails to the 'Work' folder.",
        "difficulty": "hard"
    }
]

app = FastAPI(
    title="Smart Inbox Lite Service",
    version="1.0.0",
    description="Professional OpenEnv-compliant Email Triage environment."
)

class ResetRequest(BaseModel):
    task_id: str = "easy"
    seed: Optional[int] = None  # Set for reproducible episodes

@app.get("/", include_in_schema=False)
async def root():
    """Redirect web visitors directly to the Swagger UI."""
    return RedirectResponse(url="/docs")

@app.post("/reset", response_model=EmailObservation)
async def reset(req: Optional[ResetRequest] = None):
    task_id = req.task_id if req else "easy"
    seed = req.seed if req else None
    try:
        obs = env.reset(task_id, seed=seed)
        return obs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/step")
async def step(action: EmailAction):
    try:
        obs, reward, done, info = env.step(action)
        return {
            "observation": obs,
            "reward": reward,
            "done": done,
            "info": info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/state", response_model=EmailState)
async def state():
    try:
        return env.state()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy", "env": "smart_inbox_lite"}

@app.get("/tasks")
async def list_tasks():
    """Mandatory: Returns the list of tasks for the remote validator."""
    return TASKS

@app.get("/metadata")
async def get_metadata():
    """Mandatory: Returns the environment metadata for the validator."""
    return {
        "name": "smart_inbox_lite",
        "version": "1.0.0",
        "description": "A 3-task professional email triage environment with temporal step penalties.",
        "author": "Smart Inbox Team",
        "standard_version": "1.0.0",
        "tasks": TASKS
    }

@app.get("/schema")
async def get_schema():
    """Mandatory: Returns the Pydantic JSON schemas for all models."""
    return {
        "action": EmailAction.model_json_schema(),
        "observation": EmailObservation.model_json_schema(),
        "state": EmailState.model_json_schema()
    }

@app.post("/mcp")
async def mcp_bridge(payload: Dict[str, Any]):
    """Mandatory: JSON-RPC 2.0 bridge for the Model Context Protocol."""
    method = payload.get("method")
    params = payload.get("params", {})
    request_id = payload.get("id")

    try:
        if method == "reset":
            obs = env.reset(params.get("task_id", "easy"), seed=params.get("seed"))
            result = obs.model_dump()
        elif method == "step":
            action = EmailAction(**params.get("action", {}))
            obs, reward, done, info = env.step(action)
            result = {
                "observation": obs.model_dump(),
                "reward": reward,
                "done": done,
                "info": info
            }
        else:
            result = {"error": f"Method {method} not supported"}

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32000, "message": str(e)}
        }

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()

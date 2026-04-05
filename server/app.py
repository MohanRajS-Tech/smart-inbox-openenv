import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from environment import SmartInboxEnv
from models import EmailAction, EmailObservation, EmailState

# Initialize the state-holding environment
env = SmartInboxEnv()

app = FastAPI(title="Smart Inbox Lite Service")

class ResetRequest(BaseModel):
    task_id: str = "easy"

@app.post("/reset", response_model=EmailObservation)
async def reset(req: Optional[ResetRequest] = None):
    task_id = req.task_id if req else "easy"
    try:
        obs = env.reset(task_id)
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
    return {"status": "ok", "env": "smart_inbox_lite"}

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()

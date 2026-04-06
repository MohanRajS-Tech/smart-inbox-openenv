import os
import json
import time
import httpx
import sys
from openai import OpenAI
from dotenv import load_dotenv

# Load API keys from .env
load_dotenv()

# Ensure absolute paths to the project root and server directory are added
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, "server"))

from server.environment import SmartInboxEnv
from models import EmailAction

# MANDATORY STDOUT LOGGING
def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: str = "null") -> None:
    done_val = str(done).lower()
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: list[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

# --------------------------------------------------------------------------
# CONFIGURATION (Strict Compliance)
# --------------------------------------------------------------------------
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.groq.com/openai/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.1-8b-instant")
HF_TOKEN = os.getenv("HF_TOKEN")
BENCHMARK_NAME = os.getenv("SMART_INBOX_BENCHMARK", "smart_inbox_lite")
TASK_NAME = os.getenv("SMART_INBOX_TASK", "easy")
# --------------------------------------------------------------------------

def format_inbox(emails):
    """Converts the list of Email objects into a readable string for the LLM."""
    if not emails:
        return "INBOX IS EMPTY"
    lines = []
    for e in emails:
        flag_status = "[🚩] " if e.is_flagged else ""
        lines.append(f"{flag_status}[{e.id}] FROM: {e.sender} | SUBJECT: {e.subject} | SNIPPET: {e.snippet}")
    return "\n".join(lines)

def get_llm_action(client, obs, task_description, history=""):
    """The brain of the agent using the MANDATORY OpenAI Client with Memory."""
    
    inbox_text = format_inbox(obs.emails)
    
    prompt = f"""
    You are a Professional Smart Inbox Assistant. 
    CURRENT TASK: {task_description}
    PROGRESS: {obs.goal_progress * 100}% Complete.
    
    ⚠️ TIME IS LIMITED: Every action you take reduces your final reward by 1% (0.01 points).
    Minimize turns to maximize your score!

    Recent History:
    {history if history else "Start of task."}

    Visible Inbox Contents (ONLY USE THESE IDs):
    {inbox_text}
    
    Available Actions:
    - 'archive': For spam, social, or newsletters.
    - 'flag': For urgent security, boss, or HR alerts.
    - 'move_to_folder': Use folder_name="Work" for project-related emails.
    
    Reply in JSON format:
    {{
        "thinking": "Analyze why the previous action worked or failed, then plan the next step from the VISIBLE IDs.",
        "action_type": "archive/flag/move_to_folder",
        "email_id": "ONE specific numeric ID from the list above",
        "folder_name": "Folder name if moving (otherwise null)"
    }}
    """
    
    try:
        # [DEBUG] logs help the user but are ignored by the grader
        # print(f"[DEBUG] Calling AI Brain ({MODEL_NAME})...")
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={ "type": "json_object" },
            timeout=30.0 # Standard safety timeout
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        
        # Robust handling for lists
        if isinstance(data, list): data = data[0] if len(data) > 0 else {}
        
        return (
            data.get("thinking", "No reasoning provided"), 
            str(data.get("action_type") or "none").lower(), 
            str(data.get("email_id") or "none"), 
            data.get("folder_name")
        )
            
    except Exception as e:
        return f"Brain Error: {str(e)}", "none", "none", None

def run_pro_agent(task_id="easy"):
    # 1. Setup (Using mandatory OpenAI client)
    if not HF_TOKEN:
        print("❌ ERROR: HF_TOKEN not found in environment.")
        return 0.0

    http_client = httpx.Client(trust_env=False)
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN, http_client=http_client)
    
    env = SmartInboxEnv()
    obs = env.reset(task_id)
    task_desc = env.all_tasks.get(task_id, {}).get("description", "Clean the inbox")
    
    log_start(task=task_id, env=BENCHMARK_NAME, model=MODEL_NAME)
    
    total_turns = 0
    rewards = []
    success = False
    
    # 2. Episode Loop
    history = []
    try:
        while not obs.done:
            if not obs.emails or total_turns > 15:
                break
                
            total_turns += 1
            
            # 3. Brain Call
            history_str = "\n".join(history[-3:]) 
            thinking, a_type, eid, folder = get_llm_action(client, obs, task_desc, history_str)
            
            # 4. Step execution
            action_desc = f"{a_type}({eid})" if folder is None else f"move({eid},{folder})"
            action = EmailAction(action_type=a_type, email_id=eid, folder_name=folder)
            obs, reward, done, info = env.step(action)
            
            # 5. MANDATORY LOGGING
            log_step(step=total_turns, action=action_desc, reward=reward, done=done)
            
            # Keep history for agent memory
            rewards.append(reward)
            history.append(f"Turn {total_turns}: {a_type}({eid}) -> Reward {reward:+.2f}")
            
    finally:
        # Final Score Calculation (Must be normalized score in [0, 1])
        final_score = obs.goal_progress
        success = final_score >= 1.0
        log_end(success=success, steps=total_turns, score=final_score, rewards=rewards)
    
    return final_score

def main():
    # Only run the mandatory task defined by environment variables (Standard for Autograder)
    run_pro_agent(TASK_NAME)

if __name__ == "__main__":
    main()

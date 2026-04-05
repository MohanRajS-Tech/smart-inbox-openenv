import os
import json
import time
from dotenv import load_dotenv
from openai import OpenAI
import httpx

# Load API keys from .env
load_dotenv()

# Configuration (Required environment variables)
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.groq.com/openai/v1")

# Smart API Key Selection: Prioritize the key that matches the URL
if "groq" in API_BASE_URL.lower():
    API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("HF_TOKEN")
else:
    API_KEY = os.getenv("HF_TOKEN") or os.getenv("GROQ_API_KEY")

MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.1-8b-instant")

import sys
# Ensure absolute paths to the project root and server directory are added
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, "server"))

from server.environment import SmartInboxEnv
from models import EmailAction

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
        print(f"📡 Calling AI Brain ({MODEL_NAME})...")
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={ "type": "json_object" },
            timeout=30.0 # Standard safety timeout
        )
        print("✅ Brain Responded.")
        
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

def run_pro_agent(task_id="hard"):
    # 1. Setup (Using mandatory OpenAI client)
    if not API_KEY:
        print("❌ ERROR: API Key (HF_TOKEN or GROQ_API_KEY) not found.")
        return

    # Fix for the networking hang: Create a custom client that doesn't trust system proxies
    # and has specific connection limits.
    http_client = httpx.Client(trust_env=False)
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY, http_client=http_client)
    
    env = SmartInboxEnv()
    
    # Get task description for the agent
    task_desc = env.all_tasks.get(task_id, {}).get("description", "Clean the inbox")
    
    # Reset now returns ONLY obs (Strict Spec)
    obs = env.reset(task_id)
    
    print("=" * 60)
    print(f"🚀 STARTING PRO TASK: {task_id.upper()}")
    print(f"GOAL: {task_desc}")
    print("=" * 60)
    
    total_turns = 0
    trajectory = []
    
    # 2. Episode Loop
    history = []
    while not obs.done:
        if not obs.emails:
            print("\n📭 Inbox is empty. Task likely complete.")
            break
            
        total_turns += 1
        print(f"\n[TURN {total_turns}]")
        print(format_inbox(obs.emails))
        
        # 3. Brain Call with History
        history_str = "\n".join(history[-3:]) # Keep last 3 turns
        thinking, a_type, eid, folder = get_llm_action(client, obs, task_desc, history_str)
        
        print(f"🤔 THINKING: {thinking}")
        print(f"👉 ACTION: {a_type} on ID {eid} (Folder: {folder})")
        
        # 4. Step execution (Returns exactly 4 values: obs, reward, done, info)
        action = EmailAction(action_type=a_type, email_id=eid, folder_name=folder)
        obs, reward, done, info = env.step(action)
        
        # Update history
        result_desc = f"Success (+{reward})" if reward > 0 else f"Failed/Redundant ({reward})"
        history.append(f"Turn {total_turns}: {a_type} on ID {eid} -> {result_desc}")

        # 5. Log Trajectory
        trajectory.append({
            "turn": total_turns,
            "agent_thinking": thinking,
            "action": action.model_dump(),
            "reward": reward,
            "goal_progress": obs.goal_progress,
            "done": done
        })
        
        # RESULT
        print(f"STATUS: {obs.last_action_status}")
        # Note: reward = (Progress Gain) - (Temporal Pressure Penalty)
        print(f"PROGRESS: {obs.goal_progress * 100:.1f}% | REWARD: {obs.reward:+.2f} (Includes Time Penalty)")
        
        time.sleep(1)
        if total_turns > 15: break

    # 6. Save Trajectory (Optional but Pro)
    timestamp = int(time.time())
    traj_dir = "smart_inbox_lite/trajectories"
    os.makedirs(traj_dir, exist_ok=True)
    file_path = f"{traj_dir}/task_{task_id}_{timestamp}.json"
    with open(file_path, "w") as f:
        json.dump(trajectory, f, indent=2)
    print(f"\n✅ Trajectory saved to: {file_path}")

    print("\n" + "🏁" * 30)
    print(f"FINAL COMPLETION SCORE: {obs.goal_progress * 100:.1f}%")
    print(f"TURNS TAKEN: {total_turns}")
    print("🏁" * 30)

def main():
    # Choose your task: 'easy', 'medium', or 'hard'
    run_pro_agent("hard")

if __name__ == "__main__":
    main()

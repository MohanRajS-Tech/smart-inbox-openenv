import os
import json
import time

# Ensure imports work
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.environment import SmartInboxEnv
from models import EmailAction

def generate_golden_trajectory(task_id: str, seed: int):
    env = SmartInboxEnv()
    obs = env.reset(task_id, seed=seed)
    
    trajectory = []
    turn = 1
    
    gt = env.current_gt
    actions_to_take = []
    
    for eid in gt.get("archived_ids", []):
        actions_to_take.append(EmailAction(action_type="archive", email_id=eid))
    for eid in gt.get("flagged_ids", []):
        actions_to_take.append(EmailAction(action_type="flag", email_id=eid))
    for eid in gt.get("work_folder_ids", []):
        actions_to_take.append(EmailAction(action_type="move_to_folder", email_id=eid, folder_name="Work"))
        
    for action in actions_to_take:
        if obs.done:
            break
            
        thinking = f"Taking golden action {action.action_type} on email {action.email_id}"
        
        obs, reward, done, info = env.step(action)
        
        step_record = {
            "turn": turn,
            "agent_thinking": thinking,
            "action": {
                "action_type": action.action_type,
                "email_id": action.email_id,
                "folder_name": action.folder_name
            },
            "reward": reward,
            "goal_progress": obs.goal_progress,
            "done": obs.done
        }
        trajectory.append(step_record)
        turn += 1
        
    timestamp = int(time.time())
    filepath = os.path.join(os.path.dirname(__file__), "trajectories", f"task_{task_id}_{timestamp}.json")
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(trajectory, f, indent=2)
        
    print(f"✅ Generated golden trajectory for {task_id} -> {filepath}")
    print(f"   Score: {obs.goal_progress}, Turns: {turn-1}")

if __name__ == "__main__":
    generate_golden_trajectory("medium", seed=101)
    generate_golden_trajectory("hard", seed=102)

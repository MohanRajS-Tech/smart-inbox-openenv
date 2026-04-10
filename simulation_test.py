import os
import sys
import random

# Add parent directory to path to allow importing from 'server' and 'tasks'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server.environment import SmartInboxEnv
from models import EmailAction
from tasks.definitions import TASKS

class SmartInboxOracle:
    """
    The Oracle has 'perfect' knowledge of which email belongs to which category
    and what the rules are for the current task. It mimics a perfectly trained agent.
    """
    def __init__(self):
        self.tasks_data = TASKS

    def get_action(self, task_id, emails):
        if not emails:
            return None

        rules = self.tasks_data[task_id]["rules"]
        pool = self.tasks_data[task_id]["email_pool"]

        # 1. Identify categories for visible emails
        for email in emails:
            # Match by sender and subject (template matching)
            match = next((t for t in pool if t["sender"] == email.sender and t["subject"] == email.subject), None)
            if not match:
                continue
            
            category = match["category"]
            rule = rules.get(category)
            
            if not rule:
                continue

            if rule == "archive":
                return EmailAction(action_type="archive", email_id=email.id)
            elif rule == "flag":
                return EmailAction(action_type="flag", email_id=email.id)
            elif rule.startswith("move_to_folder"):
                folder = rule.split("|")[1]
                return EmailAction(action_type="move_to_folder", email_id=email.id, folder_name=folder)
        
        return None

def run_simulation():
    print("=" * 60)
    print("SMART INBOX LITE - ORACLE SIMULATION TEST")
    print("=" * 60)

    env = SmartInboxEnv()
    oracle = SmartInboxOracle()
    overall_success = True

    for task_id in ["easy", "medium", "hard"]:
        print(f"\n[SIMULATING TASK: {task_id.upper()}]")
        obs = env.reset(task_id)
        
        steps = 0
        total_reward = 0.0
        
        while not obs.done:
            steps += 1
            action = oracle.get_action(task_id, obs.emails)
            
            if not action:
                # Oracle says no more actions needed (e.g. only spam left)
                # But the environment says we are not done? 
                # This could happen if the goal_progress isn't 1.0 yet.
                print(f"  [!] Oracle found no actions but goal_progress={obs.goal_progress:.2f}")
                break

            obs, reward, done, info = env.step(action)
            total_reward += reward
            
            spawn_str = f" [+SPAWN: {info['spawned_email_id']}]" if info.get('spawned_email_id') else ""
            print(f"  Step {steps:02d}: {action.action_type}({action.email_id}) -> Reward: {reward:+.2f} | Score: {obs.score:.2f}{spawn_str}")

            if steps > 20: # Safety break
                print("  [!] Safety timeout reached.")
                break

        print(f"--- Result: {task_id.upper()} ---")
        print(f"Steps: {steps} | Cumulative Reward: {total_reward:.2f} | Final Score: {obs.score:.2f}")
        
        if obs.score < 0.99:
            print(f"  [X] FAILED: Final score {obs.score:.2f} < 0.99")
            overall_success = False
        else:
            print(f"  [OK] PASSED: Task solved (Score: {obs.score:.2f})")

    print("\n" + "=" * 60)
    if overall_success:
        print("OVERALL SIMULATION: PASSED [Environment Is Mathematically Solvable]")
    else:
        print("OVERALL SIMULATION: FAILED [Logical Gaps Detected]")
    print("=" * 60)

if __name__ == "__main__":
    run_simulation()

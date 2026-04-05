import json
import os
from typing import List, Dict, Any
from models import Email, EmailAction, EmailObservation, EmailState
from grader import SmartInboxGrader

class SmartInboxEnv:
    def __init__(self):
        # Load tasks from tasks.json
        tasks_path = os.path.join(os.path.dirname(__file__), "tasks.json")
        try:
            with open(tasks_path, "r") as f:
                self.all_tasks = json.load(f)
        except Exception as e:
            print(f"Error loading tasks.json: {e}")
            self.all_tasks = {}

        self._state = EmailState(episode_id="initial", task_id="easy")
        self.emails = [] # Internal storage of all emails for the current task
        self.current_gt = {} # Ground truth for the active task
        self.STEP_PENALTY = 0.01 # The "Cost of Time"

    def reset(self, task_id: str = "easy"):
        """Resets the environment and returns the initial observation."""
        self._state = EmailState(episode_id=f"ep_{task_id}", task_id=task_id)
        
        task_data = self.all_tasks.get(task_id, {})
        if not task_data:
            print(f"Warning: Task {task_id} not found in tasks.json")
            self.emails = []
            self.current_gt = {}
        else:
            # Load emails as models
            self.emails = [Email(**e) for e in task_data.get("emails", [])]
            self.current_gt = task_data.get("ground_truth", {})
            
        self._state.total_emails = len(self.emails)
        # Return ONLY the observation (OpenEnv Spec)
        return self._get_obs("Inbox Reset", 0.0)

    def state(self) -> EmailState:
        """Mandatory: Returns the current full internal state."""
        return self._state

    def _calculate_score(self):
        """Uses the external SmartInboxGrader to calculate the current score."""
        return SmartInboxGrader.calculate_score(self._state, self.current_gt)

    def _get_obs(self, status: str, reward: float):
        """Provides the current view to the agent."""
        # Filter: Hide emails already processed (Archived, Moved to Work, or Flagged)
        done_ids = self._state.archived_ids + self._state.work_folder_ids + self._state.flagged_ids
        visible = [e for e in self.emails if e.id not in done_ids]
        
        # Determine if task is completed
        current_score = self._calculate_score()
        done = (current_score == 1.0) or (self._state.step_count >= self._state.max_steps)
        
        return EmailObservation(
            emails=visible,
            last_action_status=status,
            goal_progress=current_score,
            reward=reward,
            done=done
        )

    def step(self, action: EmailAction):
        """The core logic for 'Pro' actions."""
        self._state.step_count += 1
        old_score = self._calculate_score()
        
        status = f"Action: {action.action_type}"
        
        # Find the target email object
        target = next((e for e in self.emails if e.id == action.email_id), None)
        if not target:
            obs = self._get_obs(f"Email ID {action.email_id} not found", -self.STEP_PENALTY)
            return obs, -self.STEP_PENALTY, obs.done, {}
        
        # 1. Process the Action
        if action.action_type == "archive":
            if action.email_id not in self._state.archived_ids:
                self._state.archived_ids.append(action.email_id)
        
        elif action.action_type == "flag":
            if action.email_id not in self._state.flagged_ids:
                self._state.flagged_ids.append(action.email_id)
                target.is_flagged = True
                
        elif action.action_type == "move_to_folder":
            if action.folder_name == "Work":
                if action.email_id not in self._state.work_folder_ids:
                    self._state.work_folder_ids.append(action.email_id)
        
        # 2. Calculate Reward
        new_score = self._calculate_score()
        # Reward = (Progress Gain) - (Temporal Pressure Penalty)
        reward = round((new_score - old_score) - self.STEP_PENALTY, 2)
        self._state.score = new_score
        
        # 3. Return results
        obs = self._get_obs(status, reward)
        return obs, reward, obs.done, {}

if __name__ == "__main__":
    # Internal test
    env = SmartInboxEnv()
    obs = env.reset("easy")
    print(f"Task: {env._state.task_id} | Visible: {len(obs.emails)}")
    
    # Simulate a correct move
    action = EmailAction(action_type="archive", email_id="1")
    obs, reward, done, info = env.step(action)
    print(f"Goal Progress: {obs.goal_progress} | Reward: {reward}")


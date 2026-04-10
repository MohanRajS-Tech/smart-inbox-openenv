import json
import os
import random
from typing import List, Dict, Any, Optional
from models import Email, EmailAction, EmailObservation, EmailState
from tasks.definitions import TASKS
from tasks.graders import grade_task

class SmartInboxEnv:
    def __init__(self):
        # Load tasks from the new root-level definitions
        self.all_tasks = TASKS

        self._state = EmailState(episode_id="initial", task_id="easy")
        self.emails = []       # Internal storage of all emails for the current episode
        self.current_gt = {}   # Ground truth, built dynamically each reset
        self.STEP_PENALTY = 0.01  # The "Cost of Time"

    def reset(self, task_id: str = "easy", seed: Optional[int] = None):
        """
        Resets the environment with a procedurally generated inbox.

        Randomly draws emails from the task's email_pool using the 'select'
        counts per category. Ground truth is built dynamically from 'rules',
        so the grader always reflects exactly which emails were drawn.

        Args:
            task_id: One of 'easy', 'medium', 'hard'.
            seed: Optional integer seed. Set for reproducible episodes
                  (e.g. for automated validation). Leave None for true randomness.
        """
        # Apply seed BEFORE any random operations
        if seed is not None:
            random.seed(seed)

        self._state = EmailState(episode_id=f"ep_{task_id}", task_id=task_id)

        task_data = self.all_tasks.get(task_id, {})
        if not task_data:
            print(f"Warning: Task '{task_id}' not found in tasks definitions")
            self.emails = []
            self.current_gt = {}
        else:
            self._build_episode_from_pool(task_data)

        self._state.total_emails = len(self.emails)
        # Return ONLY the observation (OpenEnv Spec)
        return self._get_obs("Inbox Reset", 0.0)

    def _build_episode_from_pool(self, task_data: Dict[str, Any]):
        """
        Draws emails from the pool and constructs a fresh, randomized episode.
        Ground truth is computed dynamically based on drawn emails + task rules.
        """
        pool: List[Dict]          = task_data.get("email_pool", [])
        select: Dict[str, int]    = task_data.get("select", {})
        rules: Dict[str, str]     = task_data.get("rules", {})
        
        # Save pools for mid-episode dynamic spawning
        self._spawn_pool = pool
        self._spawn_rules = rules

        # --- Step 1: Group the pool by category ---
        by_category: Dict[str, List[Dict]] = {}
        for email_template in pool:
            cat = email_template.get("category", "other")
            by_category.setdefault(cat, []).append(email_template)

        # --- Step 2: Randomly sample required count per category ---
        sampled_emails: List[Dict] = []
        for category, count in select.items():
            available = by_category.get(category, [])
            if len(available) < count:
                print(f"Warning: Pool has only {len(available)} '{category}' emails, needed {count}.")
            drawn = random.sample(available, min(count, len(available)))
            for template in drawn:
                sampled_emails.append({**template, "category": category})

        # --- Step 3: Shuffle to remove category-ordering bias ---
        random.shuffle(sampled_emails)

        # --- Step 4: Assign fresh sequential IDs + build Email models ---
        self.emails = []
        self.current_gt = {"archived_ids": [], "flagged_ids": [], "work_folder_ids": []}

        for i, template in enumerate(sampled_emails):
            email_id = str(i + 1)
            category = template["category"]

            self.emails.append(Email(
                id=email_id,
                sender=template["sender"],
                subject=template["subject"],
                snippet=template.get("snippet", ""),
                is_urgent=(category == "urgent"),
            ))

            # --- Step 5: Build ground truth from rules ---
            rule = rules.get(category)  # e.g. "archive", "flag", "move_to_folder|Work"
            if rule == "archive":
                self.current_gt["archived_ids"].append(email_id)
            elif rule == "flag":
                self.current_gt["flagged_ids"].append(email_id)
            elif rule and rule.startswith("move_to_folder"):
                self.current_gt["work_folder_ids"].append(email_id)
            # No rule (e.g. "spam") = intentionally ignored, not in ground truth

    def state(self) -> EmailState:
        """Mandatory: Returns the current full internal state."""
        return self._state

    def _calculate_score(self):
        """Uses the standardized grader to calculate the current score."""
        return grade_task(self._state, self.current_gt)

    def _get_obs(self, status: str, reward: float):
        """Provides the current view to the agent."""
        # Filter: Hide emails already processed (Archived, Moved to Work, or Flagged)
        done_ids = self._state.archived_ids + self._state.work_folder_ids + self._state.flagged_ids
        visible = [e for e in self.emails if e.id not in done_ids]

        # Determine if task is completed
        current_score = self._calculate_score()
        done = (current_score == 1.0) or (self._state.step_count >= self._state.max_steps)
        steps_remaining = max(0, self._state.max_steps - self._state.step_count)

        return EmailObservation(
            emails=visible,
            last_action_status=status,
            goal_progress=current_score,
            score=current_score, # Alias for validator compliance
            reward=reward,
            done=done,
            steps_remaining=steps_remaining
        )


    def step(self, action: EmailAction):
        """The core logic for 'Pro' actions."""
        self._state.step_count += 1
        old_score = self._calculate_score()

        status = f"Action: {action.action_type}"

        # Find the target email object
        target = next((e for e in self.emails if e.id == action.email_id), None)
        if not target:
            obs = self._get_obs(f"Email ID {action.email_id} not found", -0.15)
            return obs, -0.15, obs.done, {}

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
        new_score_before_spawn = self._calculate_score()
        progress_gain = new_score_before_spawn - old_score
        
        wrong_action_penalty = 0.0
        # If the action produced no progress, it was either incorrect, repeated, or unnecessary.
        if progress_gain == 0.0:
            wrong_action_penalty = 0.15
            status += " (Incorrect/Ineffective)"
            
        # Reward = (Progress Gain) - (Temporal Pressure Penalty) - (Wrong Action Penalty)
        reward = round(progress_gain - self.STEP_PENALTY - wrong_action_penalty, 2)
        
        # 3. Dynamic Spawn Mechanic: Inject a new email every 3 steps (max 12 to fit in Gym)
        spawn_message = ""
        if self._state.step_count % 3 == 0 and len(self.emails) < 12:
            if hasattr(self, '_spawn_pool') and self._spawn_pool:
                template = random.choice(self._spawn_pool)
                new_id = str(len(self.emails) + 1)
                category = template.get("category", "other")
                
                self.emails.append(Email(
                    id=new_id,
                    sender=template["sender"],
                    subject=template["subject"],
                    snippet=template.get("snippet", ""),
                    is_urgent=(category == "urgent")
                ))
                
                # Expand ground truth so the grader knows about this new objective
                rule = getattr(self, '_spawn_rules', {}).get(category)
                if rule == "archive":
                    self.current_gt["archived_ids"].append(new_id)
                elif rule == "flag":
                    self.current_gt["flagged_ids"].append(new_id)
                elif rule and rule.startswith("move_to_folder"):
                    self.current_gt["work_folder_ids"].append(new_id)
                    
                spawn_message = " [*NEW MAIL*]"

        # 4. Update the final world state score and return
        self._state.score = self._calculate_score()
        obs = self._get_obs(status + spawn_message, reward)
        return obs, reward, obs.done, {}


if __name__ == "__main__":
    # Quick internal test: run 3 resets to prove randomization works
    env = SmartInboxEnv()
    for task in ["easy", "medium", "hard"]:
        obs = env.reset(task)
        print(f"\nTask: {task} | Visible: {len(obs.emails)} emails")
        for e in obs.emails:
            print(f"  [{e.id}] {e.sender} — {e.subject}")
        print(f"  Ground truth: {env.current_gt}")

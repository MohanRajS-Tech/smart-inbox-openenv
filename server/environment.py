import json
import os
import random
from typing import List, Dict, Any, Optional
from models import Email, EmailAction, EmailObservation, EmailState
from tasks.definitions import TASKS
from tasks.graders import grade_task, compute_step_reward
from tasks.generator import TaskGenerator

class SmartInboxEnv:
    def __init__(self):
        self.all_tasks = TASKS
        self._state = EmailState(episode_id="initial", task_id="easy-triage")
        self.emails = []
        self.current_gt = {}
        self.STEP_PENALTY = 0.01

        # Load policies
        policy_path = os.path.join(os.path.dirname(__file__), "..", "tasks", "company_policies.json")
        try:
            with open(policy_path, "r") as f:
                self.policies = json.load(f)
        except Exception:
            self.policies = {}

        # Load user context
        context_path = os.path.join(os.path.dirname(__file__), "..", "tasks", "user_context.json")
        try:
            with open(context_path, "r") as f:
                self.user_context_data = json.load(f)
        except Exception:
            self.user_context_data = {"summary": "Standard Profile", "history": []}

    def reset(self, task_id: str = "easy-triage", seed: Optional[int] = None):
        """Standardized OpenEnv Reset."""
        if seed is not None:
            random.seed(seed)
        
        generator = TaskGenerator(seed=seed)
        task_data = self.all_tasks.get(task_id, {})
        
        email_count = task_data.get("email_count", 5)
        self.emails = generator.generate_episode(task_id, email_count)
        
        tools_state = generator.generate_tools_state()
        
        self._state = EmailState(
            episode_id=f"ep_{task_id}_{seed or 'rand'}",
            task_id=task_id,
            total_emails=len(self.emails),
            calendar_entries=tools_state["calendar"],
            crm_records=tools_state["crm"],
            employee_directory=tools_state["directory"]
        )

        # Build Ground Truth
        self.current_gt = {
            "archived_ids": [], "flagged_ids": [], "work_folder_ids": [],
            "redacted_ids": [], "phishing_ids": [], "crm_search_ids": [],
            "calendar_update_ids": [], "verification_ids": []
        }
        
        rules = task_data.get("rules", {})
        for email in self.emails:
            rule = rules.get(email.category)
            
            if email.has_pii:
                self.current_gt["redacted_ids"].append(email.id)
            
            if rule == "archive":
                self.current_gt["archived_ids"].append(email.id)
            elif rule == "flag":
                self.current_gt["flagged_ids"].append(email.id)
            elif rule and rule.startswith("move_to_folder"):
                self.current_gt["work_folder_ids"].append(email.id)
            elif rule == "report_as_phishing":
                self.current_gt["phishing_ids"].append(email.id)
            elif rule == "verify_identity":
                self.current_gt["verification_ids"].append(email.id)
            elif rule == "search_crm":
                self.current_gt["crm_search_ids"].append(email.id)

        self._state.score = self._calculate_score()
        return self._get_obs("Inbox Reset", 0.01)

    def _calculate_score(self):
        return grade_task(self._state, self.current_gt)

    def _get_obs(self, status: str, reward: float):
        done_ids = (
            self._state.archived_ids + self._state.work_folder_ids + 
            self._state.flagged_ids + self._state.redacted_ids + 
            self._state.phishing_reported_ids
        )
        visible = [e for e in self.emails if e.id not in done_ids]
        current_score = self._calculate_score()
        done = (current_score >= 0.99) or (self._state.step_count >= self._state.max_steps)
        
        return EmailObservation(
            emails=visible,
            last_action_status=status,
            goal_progress=current_score,
            score=current_score,
            reward=reward,
            done=done,
            steps_remaining=max(0, self._state.max_steps - self._state.step_count)
        )

    def step(self, action: EmailAction):
        self._state.step_count += 1
        old_score = self._calculate_score()
        info = {"action_result": "no_change", "security_breach": False}
        status = f"Result of {action.action_type}"

        target = next((e for e in self.emails if e.id == action.email_id), None)
        if not target:
            obs = self._get_obs("Email ID not found", -0.1)
            return obs, -0.1, obs.done, info

        # --- Action Logic ---
        if action.action_type == "archive":
            if target.has_pii and action.email_id not in self._state.redacted_ids:
                self._state.security_breach = True
                info["security_breach"] = True
            self._state.archived_ids.append(action.email_id)
            info["action_result"] = "success"

        elif action.action_type == "flag":
            if target.has_pii and action.email_id not in self._state.redacted_ids:
                self._state.security_breach = True
                info["security_breach"] = True
            self._state.flagged_ids.append(action.email_id)
            info["action_result"] = "success"

        elif action.action_type == "redact":
            self._state.redacted_ids.append(action.email_id)
            info["action_result"] = "success"

        elif action.action_type == "report_as_phishing":
            if target.category in ["phishing", "spoofed_internal"]:
                self._state.phishing_reported_ids.append(action.email_id)
                info["action_result"] = "success"
            else:
                info["action_result"] = "fail"

        elif action.action_type == "verify_identity":
            official_email = self._state.employee_directory.get(target.sender)
            if official_email and official_email == target.sender_email:
                self._state.verified_ids.append(action.email_id)
                info["action_result"] = "success"
            else:
                info["action_result"] = "fail"

        # --- Post-Action Security Checks ---
        if action.action_type in ["archive", "flag"] and target.category in ["phishing", "spoofed_internal"]:
            self._state.security_breach = True
            info["security_breach"] = True

        new_score = self._calculate_score()
        reward = compute_step_reward(old_score, new_score, info)
        
        self._state.score = new_score
        obs = self._get_obs(status, reward)
        return obs, reward, obs.done, info

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

        # Load policies for the Check Policy action
        policy_path = os.path.join(os.path.dirname(__file__), "..", "tasks", "company_policies.json")
        try:
            with open(policy_path, "r") as f:
                self.policies = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load company_policies.json: {e}")
            self.policies = {}

        # Load user context for the Personal Assistant
        context_path = os.path.join(os.path.dirname(__file__), "..", "tasks", "user_context.json")
        try:
            with open(context_path, "r") as f:
                self.user_context_data = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load user_context.json: {e}")
            self.user_context_data = {"summary": "Standard Profile", "history": []}

        # [NEW] Static Mock Tools Infrastructure
        self.MOCK_CRM = {
            "Acme Corp": {"id": "C-001", "tier": "Gold", "contact": "Alice", "notes": "Active Project"},
            "Globex": {"id": "C-002", "tier": "Silver", "contact": "Hank", "notes": "Pending Quote"},
            "Hooli": {"id": "C-003", "tier": "Bronze", "contact": "Gavin", "notes": "Idle"}
        }
        self.INITIAL_CALENDAR = [
            {"event": "Team Sync", "time": "10:00 AM"},
            {"event": "Partner Review", "time": "02:00 PM"}
        ]
        self.MOCK_DIRECTORY = {
            "CEO": "ceo@company.com",
            "HR Manager": "hr@company.com",
            "IT Support": "support@company.com",
            "Finance Lead": "finance@company.com"
        }

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

        # [NEW] Initialize tool states in the model
        self._state.calendar_entries = list(self.INITIAL_CALENDAR)
        self._state.crm_records = dict(self.MOCK_CRM)
        self._state.employee_directory = dict(self.MOCK_DIRECTORY)
        self._state.operations_log = []
        self._state.verified_ids = []

        self._state.total_emails = len(self.emails)
        self._state.score = self._calculate_score() # Ensure state score is updated
        # Return ONLY the observation (OpenEnv Spec)
        return self._get_obs("Inbox Reset", 0.01)

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
        self.current_gt = {
            "archived_ids": [], 
            "flagged_ids": [], 
            "work_folder_ids": [],
            "redacted_ids": [], # Ground truth: emails that MUST be redacted
            "phishing_ids": [], # Ground truth: emails that MUST be reported
            "crm_search_ids": [], # New tool-use GT
            "calendar_update_ids": [],
            "task_creation_ids": [],
            "verification_ids": [] # IDs requiring identity verify first
        }

        for i, template in enumerate(sampled_emails):
            email_id = str(i + 1)
            category = template["category"]
            has_pii = template.get("has_pii", False)

            self.emails.append(Email(
                id=email_id,
                sender=template["sender"],
                sender_email=template.get("sender_email", f"{template['sender'].lower().replace(' ', '.')}@company.com"),
                subject=template["subject"],
                snippet=template.get("snippet", ""),
                is_urgent=(category == "urgent"),
                has_pii=has_pii,
                category=category,
                policy_required=template.get("policy_required", False),
                thread_id=template.get("thread_id")
            ))

            # --- Step 5: Build ground truth from rules ---
            rule = rules.get(category)  # e.g. "archive", "flag", "move_to_folder|Work", "redact"
            
            if has_pii:
                # If it has PII, it MUST be redacted first (Gold Standard)
                self.current_gt["redacted_ids"].append(email_id)
            
            if template.get("policy_required", False):
                self._state.policy_required_ids.append(email_id)
            
            if category == "history_needed":
                self._state.memory_required_ids.append(email_id)
            
            if rule == "archive":
                self.current_gt["archived_ids"].append(email_id)
            elif rule == "flag":
                self.current_gt["flagged_ids"].append(email_id)
            elif rule and rule.startswith("move_to_folder"):
                self.current_gt["work_folder_ids"].append(email_id)
            elif rule == "redact":
                # Special case where redaction IS the primary goal
                if email_id not in self.current_gt["redacted_ids"]:
                    self.current_gt["redacted_ids"].append(email_id)
            elif rule == "report_as_phishing":
                self.current_gt["phishing_ids"].append(email_id)
            elif rule == "policy_dependent":
                # Determine correct action based on specific template properties
                if category == "finance":
                    amount = template.get("amount", 0)
                    if amount > 100:
                        self.current_gt["flagged_ids"].append(email_id)
                    else:
                        self.current_gt["archived_ids"].append(email_id)
                elif category == "it_request":
                    item_type = template.get("item_type", "software")
                    if item_type == "hardware":
                        self.current_gt["work_folder_ids"].append(email_id)
                    else:
                        self.current_gt["flagged_ids"].append(email_id)
            elif rule == "search_crm":
                self.current_gt["crm_search_ids"].append(email_id)
            elif rule == "update_calendar":
                self.current_gt["calendar_update_ids"].append(email_id)
            elif rule == "create_task":
                self.current_gt["task_creation_ids"].append(email_id)
            elif rule == "verify_identity":
                self.current_gt["verification_ids"].append(email_id)
            # No rule (e.g. "spam") = intentionally ignored, not in ground truth

    def state(self) -> EmailState:
        """Mandatory: Returns the current full internal state."""
        return self._state

    def _calculate_score(self):
        """Uses the standardized grader to calculate the current score."""
        raw_score = grade_task(self._state, self.current_gt)
        # Ensure the score is NATURALLY returned within the (0.01, 0.99) range
        clamped = max(0.01, min(0.99, raw_score))
        return round(clamped, 2)

    def _get_obs(self, status: str, reward: float):
        """Provides the current view to the agent."""
        # Filter: Hide emails already processed (Archived, Moved to Work, Flagged, or Redacted)
        done_ids = (
            self._state.archived_ids + 
            self._state.work_folder_ids + 
            self._state.flagged_ids +
            self._state.redacted_ids +
            self._state.phishing_reported_ids
        )
        visible = [e for e in self.emails if e.id not in done_ids]

        # Determine if task is completed
        current_score = self._calculate_score()
        done = (current_score >= 0.99) or (self._state.step_count >= self._state.max_steps)
        steps_remaining = max(0, self._state.max_steps - self._state.step_count)

        return EmailObservation(
            emails=visible,
            last_action_status=status,
            tool_output=self._state.operations_log[-1] if self._state.operations_log else None,
            goal_progress=current_score,
            score=current_score, # Alias for validator compliance
            user_context=self.user_context_data.get("summary", ""),
            reward=reward,
            done=done,
            steps_remaining=steps_remaining
        )


    def step(self, action: EmailAction):
        """The core logic for 'Pro' actions with improved robustness and metadata."""
        self._state.step_count += 1
        old_score = self._calculate_score()
        
        info = {
            "action_result": "no_change",
            "spawned_email_id": None,
            "gt_size": sum(len(ids) for ids in self.current_gt.values())
        }

        status = f"Action: {action.action_type}"

        # Find the target email object
        target = next((e for e in self.emails if e.id == action.email_id), None)
        if not target:
            obs = self._get_obs(f"Email ID {action.email_id} not found", -0.15)
            info["action_result"] = "fail"
            return obs, -0.15, obs.done, info

        # 1. Process the Action
        if action.action_type == "archive":
            if target.has_pii and action.email_id not in self._state.redacted_ids:
                self._state.security_breach = True
                status += " [SECURITY BREACH: Archived PII without redaction]"
            
            if action.email_id not in self._state.archived_ids:
                self._state.archived_ids.append(action.email_id)
                info["action_result"] = "success"

        elif action.action_type == "flag":
            if target.has_pii and action.email_id not in self._state.redacted_ids:
                self._state.security_breach = True
                status += " [SECURITY BREACH: Flagged PII without redaction]"

            if action.email_id not in self._state.flagged_ids:
                self._state.flagged_ids.append(action.email_id)
                target.is_flagged = True
                info["action_result"] = "success"

        elif action.action_type == "move_to_folder":
            if target.has_pii and action.email_id not in self._state.redacted_ids:
                self._state.security_breach = True
                status += " [SECURITY BREACH: Moved PII without redaction]"

            if action.folder_name == "Work":
                if action.email_id not in self._state.work_folder_ids:
                    self._state.work_folder_ids.append(action.email_id)
                    info["action_result"] = "success"

        elif action.action_type == "redact":
            if action.email_id not in self._state.redacted_ids:
                self._state.redacted_ids.append(action.email_id)
                info["action_result"] = "success"
                status += " (PII Safely Redacted)"

        elif action.action_type == "report_as_phishing":
            if target.category == "phishing":
                if action.email_id not in self._state.phishing_reported_ids:
                    self._state.phishing_reported_ids.append(action.email_id)
                    info["action_result"] = "success"
                    status += " (Threat Neutralized)"
            else:
                # Penalty for reporting a legitimate email as phishing
                wrong_action_penalty = 0.2
                status += " (FALSE POSITIVE: Reported non-phishing email)"
                info["action_result"] = "fail"

        elif action.action_type == "check_policy":
            if action.email_id not in self._state.policy_checked_ids:
                self._state.policy_checked_ids.append(action.email_id)
            
            policy_text = self.policies.get(target.category, "General Policy: Handle with standard care.")
            status = f"Policy [KB]: {policy_text}"
            info["action_result"] = "success"

        elif action.action_type == "search_memory":
            if action.email_id not in self._state.memory_searched_ids:
                self._state.memory_searched_ids.append(action.email_id)
            
            query = (action.query or "").lower()
            history = self.user_context_data.get("history", [])
            # Keyword matching against query field or text field
            matches = [h["text"] for h in history if query and (query in h.get("query", "").lower() or query in h["text"].lower())]
            
            if matches:
                status = f"Memory Retrieval: {matches[0]}"
                info["action_result"] = "success"
            else:
                status = f"Memory: No results for '{query}'"
                info["action_result"] = "fail"

        elif action.action_type == "update_calendar":
            details = action.calendar_details or {}
            event_name = details.get("event", "Untitled Event")
            event_time = details.get("time", "TBD")
            
            # Conflict Detection
            conflict = next((e for e in self._state.calendar_entries if e["time"] == event_time), None)
            if conflict:
                status = f"CALENDAR CONFLICT: {event_time} is occupied by '{conflict['event']}'"
                info["action_result"] = "fail"
                self._state.operations_log.append(status)
            else:
                new_entry = {"event": event_name, "time": event_time}
                self._state.calendar_entries.append(new_entry)
                if action.email_id not in self._state.calendar_updated_ids:
                    self._state.calendar_updated_ids.append(action.email_id)
                status = f"CALENDAR SUCCESS: Booked '{event_name}' at {event_time}"
                info["action_result"] = "success"
                self._state.operations_log.append(status)

        elif action.action_type == "search_crm":
            query = action.query or ""
            # Simple substring match on keys
            results = {k: v for k, v in self._state.crm_records.items() if query.lower() in k.lower()}
            if results:
                if action.email_id not in self._state.crm_searched_ids:
                    self._state.crm_searched_ids.append(action.email_id)
                status = f"CRM RESULTS: Found {len(results)} matches for '{query}'"
                info["action_result"] = "success"
                # Store serialized results in operations log for agent observation
                self._state.operations_log.append(json.dumps(results))
            else:
                status = f"CRM: No matches found for '{query}'"
                info["action_result"] = "fail"
                self._state.operations_log.append(status)

        elif action.action_type == "create_task":
            if action.email_id not in self._state.task_created_ids:
                self._state.task_created_ids.append(action.email_id)
            task_desc = action.task_details or "New Task"
            status = f"TASK CREATED: {task_desc}"
            info["action_result"] = "success"
            self._state.operations_log.append(status)

        elif action.action_type == "verify_identity":
            sender_name = target.sender
            email_addr = target.sender_email if hasattr(target, "sender_email") else ""
            # Some emails might not have sender_email attribute if they are old templates
            # Let's assume the template has it, or we extract it from snippet for simulation
            
            official_email = self._state.employee_directory.get(sender_name)
            if official_email and official_email == email_addr:
                status = f"IDENTITY VERIFIED: {sender_name} is authenticated."
                info["action_result"] = "success"
                if action.email_id not in self._state.verified_ids:
                    self._state.verified_ids.append(action.email_id)
            else:
                status = f"IDENTITY FAILED: {sender_name} ({email_addr}) is NOT matching directory."
                info["action_result"] = "fail"
                # If they tried to verify a spoofed email, we don't breach yet, but they know it's bad
            self._state.operations_log.append(status)

        # --- Advanced Security Trap & Negligence Logic ---
        high_stakes = ["account_change", "spoofed_internal", "access_request", "knowledge_request", "account_link"]
        is_sensitive = target.category in high_stakes
        
        # 1. Phishing Trap
        if action.action_type in ["archive", "flag", "move_to_folder", "redact"] and target.category == "phishing":
            self._state.security_breach = True
            status += f" [SECURITY BREACH: Fell for Phishing - {action.action_type.upper()}]"
            info["action_result"] = "fail"

        # 2. Social Engineering / Spoofing Trap
        elif action.action_type in ["archive", "flag", "move_to_folder"] and target.category == "spoofed_internal":
            if action.email_id not in self._state.verified_ids:
                self._state.security_breach = True
                status += f" [SECURITY BREACH: Acted on unverified SPOOFED INTERNAL request]"
                info["action_result"] = "fail"

        # 3. Negligence Penalty (Skipped Verification on Legit High-Stakes)
        elif action.action_type in ["archive", "flag", "move_to_folder"] and is_sensitive:
            if action.email_id not in self._state.verified_ids:
                status += " [NEGLIGENCE: Skipped mandatory Identity Verification]"
                info["negligence"] = True # Handled in grader

        # 2. Calculate Reward
        new_score_before_spawn = self._calculate_score()
        progress_gain = new_score_before_spawn - old_score
        
        wrong_action_penalty = 0.0
        # If the action produced no progress, it was either incorrect, repeated, or unnecessary.
        if progress_gain == 0.0 and info["action_result"] != "success":
            wrong_action_penalty = 0.15
            status += " (Incorrect/Ineffective)"
            info["action_result"] = "fail"
            
        # Reward = (Progress Gain) - (Temporal Pressure Penalty) - (Wrong Action Penalty)
        reward = round(progress_gain - self.STEP_PENALTY - wrong_action_penalty, 2)
        # Ensure reward is never exactly 0.0 (Hard Clamping)
        if reward >= 0:
            reward = max(0.01, reward)
        else:
            reward = min(-0.01, reward)
        
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
                
                # CRITICAL Fix: Keep total_emails consistent for progress metrics
                self._state.total_emails = len(self.emails)
                info["spawned_email_id"] = new_id
                
                # Expand ground truth so the grader knows about this new objective
                rule = getattr(self, '_spawn_rules', {}).get(category)
                new_has_pii = template.get("has_pii", False)
                if new_has_pii:
                    self.current_gt["redacted_ids"].append(new_id)

                if rule == "archive":
                    self.current_gt["archived_ids"].append(new_id)
                elif rule == "flag":
                    self.current_gt["flagged_ids"].append(new_id)
                elif rule and rule.startswith("move_to_folder"):
                    self.current_gt["work_folder_ids"].append(new_id)
                elif rule == "redact":
                    if new_id not in self.current_gt["redacted_ids"]:
                        self.current_gt["redacted_ids"].append(new_id)
                elif rule == "report_as_phishing":
                    self.current_gt["phishing_ids"].append(new_id)
                    
                spawn_message = " [*NEW MAIL*]"
                info["gt_size"] = sum(len(ids) for ids in self.current_gt.values())

        # 4. Update the final world state score and return
        self._state.score = self._calculate_score()
        obs = self._get_obs(status + spawn_message, reward)
        return obs, reward, obs.done, info


if __name__ == "__main__":
    # Quick internal test: run 3 resets to prove randomization works
    env = SmartInboxEnv()
    for task in ["easy", "medium", "hard"]:
        obs = env.reset(task)
        print(f"\nTask: {task} | Visible: {len(obs.emails)} emails")
        for e in obs.emails:
            print(f"  [{e.id}] {e.sender} — {e.subject}")
        print(f"  Ground truth: {env.current_gt}")

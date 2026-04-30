from typing import Dict, List, Any
from models import EmailState

def clip_score(score: float) -> float:
    """Clips the score to be strictly between 0.01 and 0.99."""
    return round(max(0.01, min(0.99, score)), 4)

def grade_step(action_result: str, info: Dict[str, Any]) -> float:
    """
    Computes a reward for a single step based on the outcome.
    Providing a dense reward signal helps RL agents learn faster.
    """
    reward = 0.0
    
    if action_result == "success":
        reward += 0.20 # Base success
        
        # Bonus for security compliance
        if info.get("redacted"):
            reward += 0.05
        if info.get("verified"):
            reward += 0.05
            
    elif action_result == "fail":
        reward -= 0.15 # Broad failure penalty
        
        if info.get("security_breach"):
            reward -= 0.50 # Heavy security penalty
            
    elif action_result == "no_change":
        reward -= 0.05 # Penalty for ineffective actions (prevent loops)

    return reward

def grade_task(state: Any, ground_truth: Dict[str, Any]) -> float:
    """
    Calculates the cumulative task progress (0.01 - 0.99).
    This is used for the 'goal_progress' metric.
    """
    def get_val(obj, attr, default):
        if hasattr(obj, attr):
            return getattr(obj, attr)
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return default

    correct = 0
    total_required = sum(len(ids) for ids in ground_truth.values())
    
    if total_required == 0:
        return 0.99

    # Score based on standard categories
    check_lists = [
        ("archived_ids", "archived_ids"),
        ("flagged_ids", "flagged_ids"),
        ("work_folder_ids", "work_folder_ids"),
        ("redacted_ids", "redacted_ids"),
        ("phishing_ids", "phishing_reported_ids")
    ]
    
    for gt_key, state_key in check_lists:
        gt_list = ground_truth.get(gt_key, [])
        state_list = get_val(state, state_key, [])
        for eid in gt_list:
            if eid in state_list:
                correct += 1
                
    # Tool usage GT
    tool_checks = [
        ("crm_search_ids", "crm_searched_ids"),
        ("calendar_update_ids", "calendar_updated_ids"),
        ("verification_ids", "verified_ids")
    ]
    for gt_key, state_key in tool_checks:
        gt_list = ground_truth.get(gt_key, [])
        state_list = get_val(state, state_key, [])
        for eid in gt_list:
            if eid in state_list:
                correct += 1

    progress = correct / total_required
    
    # Critical Security Failures override progress
    if get_val(state, "security_breach", False):
        return 0.01

    return clip_score(progress)

def compute_step_reward(old_score: float, new_score: float, info: Dict[str, Any]) -> float:
    """
    Calculates the reward for the transition between two states.
    Uses progress gain + outcome-based logic.
    """
    progress_gain = new_score - old_score
    
    # Base reward is the progress boost
    reward = progress_gain
    
    # Add nuance from the action result
    if info.get("action_result") == "fail":
        reward -= 0.1
    
    # Specific security penalties
    if info.get("security_breach"):
        reward -= 0.5
        
    return round(reward, 3)

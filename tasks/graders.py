from typing import Dict, List, Any
# Note: In a real OpenEnv V4 environment, the judge might not have access to your local models.py
# If the judge fails to import EmailState, we use a dictionary-based approach.

def grade_task(state: Any, ground_truth: Dict[str, Any]) -> float:
    """Standardized grading function for OpenEnv V4.
    
    Args:
        state: The current state object (or dictionary) of the environment.
        ground_truth: The task's ground truth dictionary.
    """
    correct = 0
    total_required = 0

    # Ensure state is handled whether it's an object or a dict
    def get_val(obj, attr, default):
        if hasattr(obj, attr):
            return getattr(obj, attr)
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return default

    archived_ids = get_val(state, "archived_ids", [])
    flagged_ids = get_val(state, "flagged_ids", [])
    work_folder_ids = get_val(state, "work_folder_ids", [])

    # 1. Evaluate Archived Emails
    gt_archived = ground_truth.get("archived_ids", [])
    total_required += len(gt_archived)
    for eid in gt_archived:
        if eid in archived_ids:
            correct += 1

    # 2. Evaluate Flagged Emails
    gt_flagged = ground_truth.get("flagged_ids", [])
    total_required += len(gt_flagged)
    for eid in gt_flagged:
        if eid in flagged_ids:
            correct += 1

    # 3. Evaluate Folders (e.g., Work)
    gt_work = ground_truth.get("work_folder_ids", [])
    total_required += len(gt_work)
    for eid in gt_work:
        if eid in work_folder_ids:
            correct += 1

    # Normalized Score (Avoid division by zero)
    if total_required == 0:
        return 0.99
        
    raw_score = correct / total_required
    clamped_score = max(0.01, min(0.99, raw_score))
    return round(clamped_score, 2)

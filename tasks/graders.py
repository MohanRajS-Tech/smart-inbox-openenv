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
    redacted_ids = get_val(state, "redacted_ids", [])
    phishing_reported_ids = get_val(state, "phishing_reported_ids", [])
    security_breach = get_val(state, "security_breach", False)

    # 0. CRITICAL: Security Breach Penalty
    # If PII was mishandled or phishing trap triggered, the score is fixed at the minimum possible.
    if security_breach:
        return 0.01

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

    # 4. Evaluate Redacted Emails (Security Compliance)
    gt_redacted = ground_truth.get("redacted_ids", [])
    total_required += len(gt_redacted)
    for eid in gt_redacted:
        if eid in redacted_ids:
            correct += 1

    gt_phishing = ground_truth.get("phishing_ids", [])
    total_required += len(gt_phishing)
    for eid in gt_phishing:
        if eid in phishing_reported_ids:
            correct += 1

    # 6. Policy Compliance Check (Executive Reasoning)
    # A small 'Negligence Penalty' for skipped policy checks on required emails.
    negligence_penalty = 0.0
    policy_required_ids = get_val(state, "policy_required_ids", [])
    policy_checked_ids = get_val(state, "policy_checked_ids", [])
    
    for eid in policy_required_ids:
        # If the email was processed (it's in any of the 'done' lists) but NOT checked in policy
        processed = (eid in archived_ids or eid in flagged_ids or 
                     eid in work_folder_ids or eid in redacted_ids or 
                     eid in phishing_reported_ids)
        if processed and eid not in policy_checked_ids:
            negligence_penalty += 0.15 # 15% penalty per neglected professional step

    # 7. Contextual Awareness Check (Personal Assistant)
    # Penalty for skipping memory searches on history-dependent emails.
    memory_required_ids = get_val(state, "memory_required_ids", [])
    memory_searched_ids = get_val(state, "memory_searched_ids", [])
    
    for eid in memory_required_ids:
        processed = (eid in archived_ids or eid in flagged_ids or 
                     eid in work_folder_ids or eid in redacted_ids or 
                     eid in phishing_reported_ids)
        if processed and eid not in memory_searched_ids:
            negligence_penalty += 0.15 # 15% penalty for ignoring user history

    # Normalized Score (Avoid division by zero)
    if total_required == 0:
        return 0.99
        
    raw_score = (correct / total_required) - negligence_penalty
    clamped_score = max(0.01, min(0.99, raw_score))
    return round(clamped_score, 2)

from typing import Dict, List, Any
from models import EmailState

class SmartInboxGrader:
    """Standalone grader for the Smart Inbox environment.
    
    This class evaluates the agent's progress by comparing the current state 
    to the 'ground_truth' defined for each task.
    """

    @staticmethod
    def calculate_score(state: EmailState, ground_truth: Dict[str, Any]) -> float:
        """Calculates a normalized score (0.0 to 1.0) based on task completion.
        
        Args:
            state: The current EmailState of the environment.
            ground_truth: The task's ground truth dictionary from tasks.json.
        """
        correct = 0
        total_required = 0

        # 1. Evaluate Archived Emails
        gt_archived = ground_truth.get("archived_ids", [])
        total_required += len(gt_archived)
        for eid in gt_archived:
            if eid in state.archived_ids:
                correct += 1

        # 2. Evaluate Flagged Emails
        gt_flagged = ground_truth.get("flagged_ids", [])
        total_required += len(gt_flagged)
        for eid in gt_flagged:
            if eid in state.flagged_ids:
                correct += 1

        # 3. Evaluate Folders (e.g., Work)
        gt_work = ground_truth.get("work_folder_ids", [])
        total_required += len(gt_work)
        for eid in gt_work:
            if eid in state.work_folder_ids:
                correct += 1

        # Normalized Score (Avoid division by zero)
        if total_required == 0:
            return 0.99
            
        raw_score = correct / total_required
        clamped_score = max(0.01, min(0.99, raw_score))
        return round(clamped_score, 2)

if __name__ == "__main__":
    # Internal test
    test_state = EmailState(episode_id="test", task_id="easy", archived_ids=["1"])
    test_gt = {"archived_ids": ["1", "2"], "flagged_ids": [], "work_folder_ids": []}
    
    score = SmartInboxGrader.calculate_score(test_state, test_gt)
    print(f"Test Score (Expected 0.5): {score}")

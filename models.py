from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Email(BaseModel):
    """Represents a single email in the inbox."""
    id: str
    sender: str
    subject: str
    snippet: str = ""
    is_read: bool = False
    is_flagged: bool = False
    folder: str = "Inbox"
    is_urgent: bool = False # Internal hidden property for the reward logic
    has_pii: bool = False # Whether the email contains sensitive data (PII)
    category: str = "other" # Internal category for rule matching
    policy_required: bool = False # Whether this email requires a policy check
    thread_id: Optional[str] = None # For linking related emails

class EmailObservation(BaseModel):
    """What the agent sees at each step. This is the SPEC-COMPLIANT view."""
    emails: List[Email]
    current_folder: str = "Inbox"
    last_action_status: Optional[str] = None
    goal_progress: float = 0.01 # From 0.0 to 1.0 (Progress toward the task)
    score: float = 0.01 # Standard OpenEnv field for grader verification
    user_context: str = "" # [NEW] Situational Awareness (e.g. OOO status)
    tool_output: Optional[str] = None # Output from the last tool call (e.g. CRM search results)
    steps_remaining: int = 15 # Temporal pressure signal
    reward: float = 0.01 # Points earned in the last step
    done: bool = False

class EmailAction(BaseModel):
    """The move an agent can make. This is the SPEC-COMPLIANT action."""
    action_type: str = Field(..., description="Action: 'archive', 'flag', 'move_to_folder', 'redact', 'report_as_phishing', 'check_policy', 'search_memory', 'update_calendar', 'search_crm', 'create_task'")
    email_id: str = Field(..., description="The ID of the target email")
    query: Optional[str] = Field(None, description="Search term (for 'search_memory' or 'search_crm')")
    folder_name: Optional[str] = Field(None, description="Target folder name (if 'move_to_folder')")
    calendar_details: Optional[Dict[str, str]] = Field(None, description="Details like {'event': 'Meeting', 'time': '2 PM'} (for 'update_calendar')")
    task_details: Optional[str] = Field(None, description="Task description (for 'create_task')")

class EmailState(BaseModel):
    """The full internal state of the environment."""
    episode_id: str
    step_count: int = 0
    max_steps: int = 15
    total_emails: int = 0
    archived_ids: List[str] = []
    flagged_ids: List[str] = []
    work_folder_ids: List[str] = []
    redacted_ids: List[str] = [] # IDs of emails that have been safely redacted
    phishing_reported_ids: List[str] = [] # IDs of emails reported as phishing
    policy_checked_ids: List[str] = [] # IDs of emails where policy was consulted
    policy_required_ids: List[str] = [] # IDs of emails that REQUIRED a policy check
    memory_searched_ids: List[str] = [] # [NEW] IDs of emails where memory search was performed
    memory_required_ids: List[str] = [] # [NEW] IDs of emails that REQUIRED a memory lookup
    security_breach: bool = False # Flags if PII was mishandled or social engineering clicked
    task_id: str = "easy" # 'easy', 'medium', 'hard', 'expert', 'insane'
    score: float = 0.01 # Normalized 0.01 to 0.99
    
    # [TOOL STATE]
    calendar_entries: List[Dict[str, str]] = [] # [{ "event": "...", "time": "..." }]
    crm_records: Dict[str, Dict[str, Any]] = {} # Mock DB of client info
    operations_log: List[str] = [] # Audit log of tool uses for grading
    crm_searched_ids: List[str] = []
    calendar_updated_ids: List[str] = []
    task_created_ids: List[str] = []

class StepResponse(BaseModel):
    """Mandatory: Standard OpenEnv 1.0 step response schema."""
    observation: EmailObservation
    reward: float
    done: bool
    info: Dict[str, Any] = {}

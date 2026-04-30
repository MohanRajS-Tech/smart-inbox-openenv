# Task Metadata for Smart Inbox Pro
# Consolidated into 3 rigorous levels for Phase 1 Parity

TASKS = {
    "easy-triage": {
        "description": "Baseline Inbox Management: Identify promotional emails and archive them. Leave project-related work alone.",
        "difficulty": "easy",
        "email_count": 5,
        "rules": {
            "spam": "archive",
            "work": "ignore" # Don't act on these
        }
    },
    "medium-triage": {
        "description": "Enterprise Coordination: Manage urgent alerts, archive promotions, and redact sensitive PII leaks.",
        "difficulty": "medium",
        "email_count": 10,
        "rules": {
            "urgent": "flag",
            "work": "ignore",
            "spam": "archive",
            "security": "redact"
        }
    },
    "hard-triage": {
        "description": "Security Architect Challenge: Detect sophisticated phishing traps, verify spoofed internal requests, and ensure total data compliance.",
        "difficulty": "hard",
        "email_count": 15,
        "rules": {
            "urgent": "flag",
            "work": "move_to_folder|Work",
            "security": "redact",
            "phishing": "report_as_phishing",
            "spoofed_internal": "verify_identity"
        }
    }
}

AVAILABLE_TASKS = list(TASKS.keys())

TASKS = {
  "easy": {
    "description": "Your inbox has promotional emails mixed with important ones. Archive ALL promotional emails to declutter your inbox. Leave urgent or important emails alone.",
    "select": {"promo": 2, "urgent": 1},
    "rules": {"promo": "archive"},
    "email_pool": [
      {"sender": "Pizza Place",   "subject": "BOGO Deal!",                   "snippet": "Buy one, get one free on all pizzas today.",         "category": "promo"},
      {"sender": "Shoe Store",    "subject": "Weekend Sneaker Sale",          "snippet": "50% off all shoes. This weekend only.",              "category": "promo"},
      {"sender": "Netflix",       "subject": "New shows added this week",     "snippet": "Check out the latest releases on your watchlist.",   "category": "promo"},
      {"sender": "Amazon Deals",  "subject": "Flash Sale: 60% off Today",     "snippet": "Deals expire in 4 hours.",                          "category": "promo"},
      {"sender": "LinkedIn",      "subject": "3 people viewed your profile",  "snippet": "See who's looking at your profile.",                 "category": "promo"},
      {"sender": "Spotify",       "subject": "Your weekly playlist is ready", "snippet": "Discover new music picked for you.",                 "category": "promo"},
      {"sender": "Boss",          "subject": "Meeting at 5pm",                "snippet": "Please confirm your attendance.",                    "category": "urgent"},
      {"sender": "CEO",           "subject": "Q4 Review - Your Input Needed", "snippet": "Required before end of day.",                       "category": "urgent"},
      {"sender": "HR Manager",    "subject": "Team Lunch RSVP by Noon",       "snippet": "Please confirm by 12pm today.",                     "category": "urgent"},
      {"sender": "Director",      "subject": "1-on-1 Rescheduled to 3pm",    "snippet": "Please update your calendar.",                      "category": "urgent"}
    ]
  },
  "medium": {
    "description": "Your inbox has a mix of urgent alerts and newsletters. FLAG all urgent security or HR alerts. ARCHIVE all newsletters and promotional digests. Urgent emails have keywords like ALERT, Policy, Expires, or Emergency.",
    "select": {"urgent": 2, "promo": 2},
    "rules": {"urgent": "flag", "promo": "archive"},
    "email_pool": [
      {"sender": "Security System",  "subject": "LOGIN ALERT: Unusual Activity",  "snippet": "A login was detected from an unknown device.",       "category": "urgent"},
      {"sender": "HR Department",    "subject": "Policy Update — Action Required", "snippet": "You must acknowledge by this Friday.",               "category": "urgent"},
      {"sender": "IT Team",          "subject": "Your Password Expires Today",     "snippet": "Reset immediately to avoid lockout.",                "category": "urgent"},
      {"sender": "Finance",          "subject": "Expense Report Due — EOD",        "snippet": "Submit your report before end of business day.",     "category": "urgent"},
      {"sender": "Boss",             "subject": "EMERGENCY: Join meeting now",     "snippet": "Drop everything. Conference room B.",                "category": "urgent"},
      {"sender": "Newsletter Co",    "subject": "Monday Morning Tips",             "snippet": "5 productivity hacks for the week ahead.",           "category": "promo"},
      {"sender": "Sales Digest",     "subject": "Q4 Industry Report is Out",      "snippet": "Read the full industry analysis.",                   "category": "promo"},
      {"sender": "Tech Trends",      "subject": "AI News You Missed This Week",    "snippet": "Top 10 stories in artificial intelligence.",         "category": "promo"},
      {"sender": "Marketing Dept",   "subject": "Campaign Performance Results",    "snippet": "Click to see this month's metrics.",                 "category": "promo"},
      {"sender": "Blog Digest",      "subject": "5 Articles Curated for You",     "snippet": "Catch up on what you missed.",                      "category": "promo"}
    ]
  },
  "hard": {
    "description": "Critical mixed inbox. FLAG all high-priority alerts (system failures, client escalations). MOVE project emails to the Work folder. WARNING: Some emails contain PII (passwords/keys) — these MUST be REDACTED before any other action.",
    "select": {"urgent": 1, "work": 1, "security": 1, "spam": 1},
    "rules": {"urgent": "flag", "work": "move_to_folder|Work", "security": "redact"},
    "email_pool": [
      {"sender": "IT Ops",       "subject": "SYSTEM DOWN — Production Outage",  "snippet": "All services offline. Immediate response required.",    "category": "urgent"},
      {"sender": "Client A",     "subject": "Project Budget: Needs Approval",   "snippet": "Client is waiting. Escalated to priority.",             "category": "urgent"},
      {"sender": "PM Lead",      "subject": "Task: Update Project Docs",       "snippet": "Please move to work tracker and complete by Friday.",   "category": "work"},
      {"sender": "Eng Lead",     "subject": "Bug: Fix Login Flow — Assigned",  "snippet": "Ticket #442. Belongs in your work queue.",             "category": "work"},
      {"sender": "IT Admin",     "subject": "Temporary VPN Password",          "snippet": "Your new password is: Hunter2! Please redact this.",   "category": "security", "has_pii": True},
      {"sender": "Finance",      "subject": "Draft Payroll Sheet",             "snippet": "Contains salary data for all dept heads.",            "category": "security", "has_pii": True},
      {"sender": "Spam Bot",     "subject": "CLICK ME! Win a FREE Prize!",     "snippet": "You have been selected. Claim now.",                    "category": "spam"}
    ]
  },
  "expert": {
    "description": "Enterprise Triage. Flag Urgent, Move Work, Redact Security, and Archive Promos. Be extremely careful with Security emails; mishandling PII will fail the task.",
    "select": {"urgent": 2, "work": 2, "security": 2, "promo": 2},
    "rules": {"urgent": "flag", "work": "move_to_folder|Work", "security": "redact", "promo": "archive"},
    "email_pool": [
      {"sender": "Boss",         "subject": "ASAP: Review Slide Deck",         "category": "urgent"},
      {"sender": "Alerts",       "subject": "[CRITICAL] DB Overload",          "category": "urgent"},
      {"sender": "Project Mgr",  "subject": "Work: Sprint 5 Planning",         "category": "work"},
      {"sender": "Dev Ops",      "subject": "Work: Review PR #123",            "category": "work"},
      {"sender": "Security",     "subject": "Leak Detected: Internal Keys",    "category": "security", "has_pii": True},
      {"sender": "Audit",        "subject": "Confidential: User List Export",  "category": "security", "has_pii": True},
      {"sender": "Marketing",    "subject": "Lunch Menu for Today",            "category": "promo"},
      {"sender": "News",         "subject": "Daily Tech Digest",               "category": "promo"}
    ]
  },
  "insane": {
    "description": "Chaos Mode. Manage a high-volume inbox with constant dynamic spawns. You must redact, flag, and archive according to corporate policy. Speed and safety are equally vital.",
    "select": {"urgent": 3, "work": 3, "security": 3, "promo": 3},
    "rules": {"urgent": "flag", "work": "move_to_folder|Work", "security": "redact", "promo": "archive"},
    "email_pool": [
       {"sender": "IT Ops",       "subject": "SYSTEM DOWN", "category": "urgent"},
       {"sender": "Client B",     "subject": "Refund Request Escalation", "category": "urgent"},
       {"sender": "System",       "subject": "Memory usage at 99%", "category": "urgent"},
       {"sender": "Team",         "subject": "Work: Standup meeting notes", "category": "work"},
       {"sender": "Manager",      "subject": "Work: Performance reviews", "category": "work"},
       {"sender": "Admin",        "subject": "Work: Budget forecast", "category": "work"},
       {"sender": "HR",           "subject": "Sensitive: Employee SSN list", "category": "security", "has_pii": True},
       {"sender": "Dev",          "subject": "SSH Private Key for Server-1", "category": "security", "has_pii": True},
       {"sender": "GCP",          "subject": "Billing Alert: Over Budget", "category": "security", "has_pii": True},
       {"sender": "Subway",       "subject": "Lunch deals", "category": "promo"},
       {"sender": "AI News",      "subject": "Newsletter", "category": "promo"},
       {"sender": "Flyer",        "subject": "Weekly coupons", "category": "promo"}
    ]
  }
}

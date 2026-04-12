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
    "description": "Critical mixed inbox. FLAG all high-priority alerts (system failures, client escalations). MOVE project emails to the Work folder. WARNING: Some emails contain PII (passwords/keys) — these MUST be REDACTED. Also, WATCH OUT for phishing attempts — REPORT them immediately.",
    "select": {"urgent": 1, "work": 1, "security": 1, "phishing": 1},
    "rules": {"urgent": "flag", "work": "move_to_folder|Work", "security": "redact", "phishing": "report_as_phishing"},
    "email_pool": [
      {"sender": "IT Ops",       "subject": "SYSTEM DOWN — Production Outage",  "snippet": "All services offline. Immediate response required.",    "category": "urgent"},
      {"sender": "Client A",     "subject": "Project Budget: Needs Approval",   "snippet": "Client is waiting. Escalated to priority.",             "category": "urgent"},
      {"sender": "PM Lead",      "subject": "Task: Update Project Docs",       "snippet": "Please move to work tracker and complete by Friday.",   "category": "work"},
      {"sender": "Eng Lead",     "subject": "Bug: Fix Login Flow — Assigned",  "snippet": "Ticket #442. Belongs in your work queue.",             "category": "work"},
      {"sender": "IT Admin",     "subject": "Temporary VPN Password",          "snippet": "Your new password is: Hunter2! Please redact this.",   "category": "security", "has_pii": True},
      {"sender": "Finance",      "subject": "Draft Payroll Sheet",             "snippet": "Contains salary data for all dept heads.",            "category": "security", "has_pii": True},
      {"sender": "IT Helpdesk",  "subject": "URGENT: Password Reset Required", "snippet": "We detected unauthorized access. Click here to reset: http://secure-login.co/reset", "category": "phishing"},
      {"sender": "Spam Bot",     "subject": "CLICK ME! Win a FREE Prize!",     "snippet": "You have been selected. Claim now.",                    "category": "spam"}
    ]
  },
  "expert": {
    "description": "Enterprise Triage: Operational Efficiency. You must redact PII, report phishing, and use TOOLS (Calendar/CRM) to resolve requests. Tasks include checking client tiers in CRM and booking meeting rooms.",
    "select": {"urgent": 1, "work": 1, "security": 1, "phishing": 1, "finance": 1, "client_query": 1, "meeting_request": 1, "administrative": 1},
    "rules": {
        "urgent": "flag", 
        "work": "move_to_folder|Work", 
        "security": "redact", 
        "phishing": "report_as_phishing", 
        "finance": "policy_dependent",
        "client_query": "search_crm",
        "meeting_request": "update_calendar",
        "administrative": "create_task"
    },
    "email_pool": [
      {"sender": "Salesforce Lead", "subject": "New Inquiry: Acme Corp", "snippet": "Need to check client tier before responding.", "category": "client_query"},
      {"sender": "Project Mgr",  "subject": "Schedule Sync: 3 PM", "snippet": "Book a room for 3 PM today.", "category": "meeting_request", "time": "3:00 PM"},
      {"sender": "Office Manager", "subject": "Supplies low", "snippet": "Create a task to order coffee beans.", "category": "administrative"},
      {"sender": "CEO @ Company", "subject": "Quick Favor",  "snippet": "I need some gift cards. Reply with codes.", "category": "phishing"},
      {"sender": "Boss",         "subject": "ASAP: Review Slide Deck",         "category": "urgent"},
      {"sender": "Staff Eng",    "subject": "Internal Key Leak", "category": "security", "has_pii": True},
      {"sender": "Finance Team", "subject": "Quarterly Report Draft", "snippet": "Draft of the Q3 results.", "category": "finance", "amount": 500, "policy_required": True},
      {"sender": "Engineering",  "subject": "Work: Feature Specs", "snippet": "Move to work folder.", "category": "work"}
    ]
  },
  "insane": {
    "description": "Chaos Mode: Multi-channel operations. Redact, Report, and solve Operational Conflicts. Includes heavy tool usage and scheduling challenges.",
    "select": {"urgent": 1, "work": 1, "security": 1, "phishing": 1, "finance": 1, "client_query": 2, "meeting_request": 2, "administrative": 1},
    "rules": {
      "urgent": "flag", 
      "work": "move_to_folder|Work", 
      "security": "redact", 
      "phishing": "report_as_phishing", 
      "finance": "policy_dependent",
      "client_query": "search_crm",
      "meeting_request": "update_calendar",
      "administrative": "create_task"
    },
    "email_pool": [
       {"sender": "VP Sales", "subject": "Client Check: Globex", "snippet": "What is the status of Globex?", "category": "client_query"},
       {"sender": "Marketing", "subject": "Brand Review: Acme Corp", "snippet": "Verify tier for Acme Corp.", "category": "client_query"},
       {"sender": "Director", "subject": "Morning Sync: 10 AM", "snippet": "Schedule a sync for 10 AM.", "category": "meeting_request", "time": "10:00 AM"}, # Conflict
       {"sender": "Team Lead", "subject": "Evening Debrief: 5 PM", "snippet": "Book a room for 5 PM.", "category": "meeting_request", "time": "5:00 PM"}, # No Conflict
       {"sender": "Facility", "subject": "Visitor Access", "snippet": "Create a task to register visitors.", "category": "administrative"},
       {"sender": "IT Support", "subject": "Password reset needed", "category": "security", "has_pii": True},
       {"sender": "Security", "subject": "URGENT ACTION NEEDED", "category": "phishing"},
       {"sender": "Accounts", "subject": "High-Value Invoice", "snippet": "Amount: $2,500.00", "category": "finance", "amount": 2500, "policy_required": True},
       {"sender": "Project Mgr", "subject": "Work: Task List", "category": "work"},
       {"sender": "IT Ops", "subject": "SYSTEM DOWN", "category": "urgent"}
    ]
  }
}

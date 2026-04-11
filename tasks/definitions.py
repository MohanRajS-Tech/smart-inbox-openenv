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
    "description": "Enterprise Triage: High-stakes operations. You must redact PII, report phishing, and CONSULT COMPANY POLICY for finance and IT requests. Neglecting policy checks on sensitive emails will result in penalties.",
    "select": {"urgent": 1, "work": 1, "security": 1, "phishing": 1, "finance": 2, "it_request": 2},
    "rules": {"urgent": "flag", "work": "move_to_folder|Work", "security": "redact", "phishing": "report_as_phishing", "finance": "policy_dependent", "it_request": "policy_dependent"},
    "email_pool": [
      {"sender": "Finance Dept", "subject": "Refund Request (ID 442)", "snippet": "Amount: $150.00. Please process.", "category": "finance", "amount": 150, "policy_required": True},
      {"sender": "Finance Dept", "subject": "Reimbursement (ID 121)", "snippet": "Amount: $45.00. Small mileage claim.", "category": "finance", "amount": 45, "policy_required": True},
      {"sender": "IT Support",  "subject": "Hardware Request: New Laptop", "snippet": "Need a Macbook Pro for the new dev.", "category": "it_request", "item_type": "hardware", "policy_required": True},
      {"sender": "IT Support",  "subject": "Software: Adobe Access", "snippet": "License request for Creative Cloud.", "category": "it_request", "item_type": "software", "policy_required": True},
      {"sender": "Security",     "subject": "Leak Detected: Internal Keys",    "category": "security", "has_pii": True},
      {"sender": "CEO @ Company", "subject": "Quick Favor",  "snippet": "I need some gift cards. Reply with codes.", "category": "phishing"},
      {"sender": "Boss",         "subject": "ASAP: Review Slide Deck",         "category": "urgent"},
      {"sender": "Project Mgr",  "subject": "Work: Sprint 5 Planning",         "category": "work"}
    ]
  },
  "insane": {
    "description": "Chaos Mode: Multi-channel triage. Redact, Report, and Follow Policies. Dynamic spawning will test your consistency under pressure.",
    "select": {"urgent": 2, "work": 2, "security": 2, "phishing": 2, "finance": 2, "it_request": 2},
    "rules": {"urgent": "flag", "work": "move_to_folder|Work", "security": "redact", "phishing": "report_as_phishing", "finance": "policy_dependent", "it_request": "policy_dependent"},
    "email_pool": [
       {"sender": "IT Help",      "subject": "New Monitor Request", "category": "it_request", "item_type": "hardware", "policy_required": True},
       {"sender": "IT Help",      "subject": "VPN Access - Remote Work", "category": "it_request", "item_type": "software", "policy_required": True},
       {"sender": "Accounts",     "subject": "Invoice #992 - High Amount", "snippet": "Total: $1,200.00", "category": "finance", "amount": 1200, "policy_required": True},
       {"sender": "Accounts",     "subject": "Office Supplies Refund", "snippet": "Total: $12.50", "category": "finance", "amount": 12.5, "policy_required": True},
       {"sender": "HR",           "subject": "Sensitive: Employee SSN list", "category": "security", "has_pii": True},
       {"sender": "Dev",          "subject": "SSH Private Key for Server-1", "category": "security", "has_pii": True},
       {"sender": "IT Security",  "subject": "Suspicious Login Attempt", "category": "phishing"},
       {"sender": "Police",       "subject": "TICKET: Unpaid Fine", "category": "phishing"},
       {"sender": "IT Ops",       "subject": "SYSTEM DOWN", "category": "urgent"},
       {"sender": "Client B",     "subject": "Refund Request Escalation", "category": "urgent"},
       {"sender": "Team",         "subject": "Work: Standup meeting notes", "category": "work"},
       {"sender": "Manager",      "subject": "Work: Performance reviews", "category": "work"}
    ]
  }
}

import random
from typing import List, Dict, Any, Optional
from models import Email

class TaskGenerator:
    """Generative engine for creating unique but reproducible email triage scenarios."""

    # --- Templates: People & Entities ---
    NAMES = ["Alex Kim", "Jordan Lee", "Taylor Chen", "Morgan Patel", "Casey Wong", "Riley Johnson", "Sam Rivera", "Jamie Smith"]
    COMPANY_DOMAINS = ["company.com", "corporate.net", "enterprise.org"]
    SPOOF_DOMAINS = ["c0mpany.com", "company-security.net", "admin-verify.biz", "secure-login.co"]
    
    COMPANIES = ["Acme Corp", "Globex", "Hooli", "Soylent Corp", "Initech", "Umbrella Corp", "Wayne Ent", "Stark Ind"]
    PROJECTS = ["Atlas", "Phoenix", "Neptune", "Horizon", "Catalyst", "Aurora", "Sentinel"]

    # --- Templates: Email Content ---
    URGENT_SUBJECTS = [
        "URGENT: {system} Outage - Immediate Response Required",
        "CRITICAL: Security Breach Detected in {system}",
        "EMERGENCY: {project} Deadline Moved to TODAY",
        "ALERT: {system} Stability Issues Affecting Clients",
        "ACTION REQUIRED: Mandatory Policy Update for {project}"
    ]
    
    NORMAL_SUBJECTS = [
        "Q{quarter} {project} Sync - Action Items",
        "Re: {project} Design Documentation Feedback",
        "Weekly Update: {project} Milestone {sprint}",
        "Invitation: {project} Retrospective Meeting",
        "FYI: New Guidelines for {project} Workflow"
    ]
    
    SPAM_SUBJECTS = [
        "You've been selected for a FREE {item}!!!",
        "URGENT: Your {service} account will be suspended",
        "Claim your {item} before it's too late!!!",
        "Re: Re: Fw: Guaranteed {amount}/month with AI",
        "FINAL NOTICE: {service} invoice overdue"
    ]

    PHISHING_SUBJECTS = [
        "Security Alert: Unusual login detected",
        "Mandatory Password Reset: HR Directive",
        "IT Dept: Action required for account verification",
        "Important notification regarding your benefits"
    ]

    ITEMS = ["iPhone 16 Pro", "MacBook Pro", "Tesla Model 3", "$5,000 Gift Card", "Rolex Watch"]
    SERVICES = ["Microsoft 365", "Google Workspace", "Dropbox", "Slack", "Adobe Creative Cloud"]
    SYSTEMS = ["Main API", "Payment Gateway", "Auth Service", "DB Cluster", "Load Balancer"]

    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)
        self.company_domain = self.rng.choice(self.COMPANY_DOMAINS)
        
        # Build a consistent mock directory for this seed
        self.directory = {}
        for name in self.NAMES:
            email = f"{name.lower().replace(' ', '.')}@{self.company_domain}"
            self.directory[name] = email

    def generate_email(self, email_id: str, category: str, difficulty: str = "easy") -> Email:
        """Generates a single email based on the category and difficulty."""
        
        is_phishing = False
        has_pii = False
        is_urgent = False
        sender_name = self.rng.choice(self.NAMES)
        sender_email = self.directory.get(sender_name, "misc@external.com")
        
        if category == "urgent":
            is_urgent = True
            system = self.rng.choice(self.SYSTEMS)
            project = self.rng.choice(self.PROJECTS)
            subject = self.rng.choice(self.URGENT_SUBJECTS).format(system=system, project=project)
            snippet = f"We are seeing critical failures in {system}. All hands on deck for {project} sync."
            
        elif category == "work":
            project = self.rng.choice(self.PROJECTS)
            quarter = self.rng.randint(1, 4)
            sprint = self.rng.randint(1, 12)
            subject = self.rng.choice(self.NORMAL_SUBJECTS).format(project=project, quarter=quarter, sprint=sprint)
            snippet = f"Please review the latest updates for {project}. We need to finalize Sprint {sprint} goals."
            
        elif category == "security":
            has_pii = True
            subject = "New Temporary Credentials"
            password = "".join(self.rng.choices("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*", k=12))
            snippet = f"Your temp password for the internal portal is: {password}. Please redact this immediately."
            
        elif category == "phishing":
            is_phishing = True
            sender_name = "IT Support"
            sender_email = f"support@{self.rng.choice(self.SPOOF_DOMAINS)}" # Spoof domain
            subject = self.rng.choice(self.PHISHING_SUBJECTS)
            snippet = "A login attempt was flagged. Click here to verify: http://verify-company-login.co/reset"

        elif category == "spoofed_internal":
            # Sophisticated CEO Fraud
            is_phishing = True
            sender_name = "CEO"
            sender_email = f"ceo@{self.rng.choice(self.SPOOF_DOMAINS)}" # Subtle spoof
            subject = "Confidential: Quick Task"
            snippet = "I'm in a meeting. Can you send me the latest salary sheet or wire $2,000 to this vendor?"

        else: # promo / spam
            item = self.rng.choice(self.ITEMS)
            service = self.rng.choice(self.SERVICES)
            amount = self.rng.randint(1000, 10000)
            subject = self.rng.choice(self.SPAM_SUBJECTS).format(item=item, service=service, amount=amount)
            snippet = f"Congratulations! You won a {item}. Claim now at http://win-big.biz."
            sender_name = "Marketing Deals"
            sender_email = "deals@spam-bot.xyz"

        return Email(
            id=email_id,
            sender=sender_name,
            sender_email=sender_email,
            subject=subject,
            snippet=snippet,
            is_urgent=is_urgent,
            has_pii=has_pii,
            category=category
        )

    def generate_episode(self, task_id: str, count: int) -> List[Email]:
        """Generates a list of emails for an episode."""
        emails = []
        
        # Difficulty-based distribution
        if task_id == "easy-triage":
            distributions = ["work"] * (count // 2) + ["spam"] * (count - (count // 2))
        elif task_id == "medium-triage":
            distributions = ["urgent"] * 2 + ["work"] * 3 + ["spam"] * 3 + ["security"] * 2
        else: # hard-triage
            distributions = ["urgent"] * 3 + ["work"] * 4 + ["security"] * 4 + ["phishing"] * 4 + ["spoofed_internal"] * 5

        # Pad or trim
        while len(distributions) < count:
            distributions.append(self.rng.choice(["work", "spam", "urgent"]))
        distributions = distributions[:count]
        self.rng.shuffle(distributions)

        for i, cat in enumerate(distributions):
            emails.append(self.generate_email(str(i+1), cat, task_id))
            
        return emails

    def generate_tools_state(self) -> Dict[str, Any]:
        """Generates mock CRM and Calendar data."""
        crm = {}
        for company in self.COMPANIES:
            crm[company] = {
                "id": f"C-{self.rng.randint(100, 999)}",
                "tier": self.rng.choice(["Gold", "Silver", "Bronze"]),
                "contact": self.rng.choice(self.NAMES),
                "notes": "Generated for scenario."
            }
            
        calendar = []
        times = ["09:00 AM", "10:00 AM", "11:00 AM", "01:00 PM", "02:00 PM", "03:00 PM", "04:00 PM"]
        self.rng.shuffle(times)
        for i in range(3): # 3 baseline meetings
            calendar.append({
                "event": f"{self.rng.choice(self.PROJECTS)} Review",
                "time": times[i]
            })
            
        return {
            "crm": crm,
            "calendar": calendar,
            "directory": self.directory
        }

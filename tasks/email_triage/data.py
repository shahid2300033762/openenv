"""
Realistic email dataset for the Email Triage task.

20+ emails spanning billing complaints, refund requests, service failures,
promotional spam, and general queries.  Each has ground-truth labels.
All data is fixed / deterministic — no randomisation.
"""

from __future__ import annotations

from typing import Dict, List


# Ground-truth structure per email
# {
#   "id": str,
#   "subject": str,
#   "sender": str,
#   "body": str,
#   "ground_truth": {
#       "classification": str,   # complaint | refund | failure | promotion | query
#       "priority": str,         # critical | high | medium | low
#       "response_keywords": [str],  # keywords a good reply should contain
#   }
# }

EMAILS: List[Dict] = [
    # --- COMPLAINTS (billing) ---
    {
        "id": "email_001",
        "subject": "Charged twice for my subscription",
        "sender": "maria.gonzalez@example.com",
        "body": (
            "Hi, I just noticed that my credit card was charged $49.99 twice "
            "this month for the same subscription plan. I've been a loyal "
            "customer for 2 years and this is really frustrating. Can you "
            "please look into this and refund the duplicate charge? I've "
            "attached my bank statement showing both transactions."
        ),
        "ground_truth": {
            "classification": "complaint",
            "priority": "high",
            "response_keywords": [
                "apologize", "sorry", "investigate", "refund",
                "duplicate", "charge", "review", "account",
            ],
        },
    },
    {
        "id": "email_002",
        "subject": "Your service is terrible",
        "sender": "angry_customer_42@example.com",
        "body": (
            "I've been trying to reach someone for THREE DAYS about my "
            "billing issue. Nobody responds to my tickets. I was charged "
            "$199 for a plan I never signed up for. If this isn't resolved "
            "by end of week, I'm disputing with my bank and leaving a review "
            "on every platform I can find."
        ),
        "ground_truth": {
            "classification": "complaint",
            "priority": "critical",
            "response_keywords": [
                "apologize", "sorry", "escalate", "urgent",
                "resolve", "immediately", "billing", "review",
            ],
        },
    },
    {
        "id": "email_003",
        "subject": "Incorrect amount on invoice #4521",
        "sender": "accounting@bigcorp.example.com",
        "body": (
            "Good afternoon, our accounts payable team flagged invoice #4521 "
            "dated March 15. The total shows $12,500 but our contract rate "
            "is $10,000/month. Could you please issue a corrected invoice? "
            "We need this resolved before our month-end close on the 28th."
        ),
        "ground_truth": {
            "classification": "complaint",
            "priority": "high",
            "response_keywords": [
                "invoice", "correct", "review", "contract",
                "updated", "apologize", "process",
            ],
        },
    },
    # --- REFUND REQUESTS ---
    {
        "id": "email_004",
        "subject": "Requesting refund for unused portion",
        "sender": "james.chen@example.com",
        "body": (
            "Hello, I purchased the annual Pro plan last month but I realize "
            "it doesn't have the API access I need for my project. I've "
            "barely used the service (logged in twice). Could I get a "
            "prorated refund for the remaining 11 months? I'd consider "
            "upgrading to Enterprise in the future if API access improves."
        ),
        "ground_truth": {
            "classification": "refund",
            "priority": "medium",
            "response_keywords": [
                "refund", "prorated", "policy", "process",
                "account", "enterprise", "upgrade",
            ],
        },
    },
    {
        "id": "email_005",
        "subject": "Product not as described — want my money back",
        "sender": "disappointed_buyer@example.com",
        "body": (
            "The marketing page said 'unlimited storage' but I hit a 50GB "
            "cap on day one. This is false advertising. I want a full refund "
            "of $299. I've already exported all my data."
        ),
        "ground_truth": {
            "classification": "refund",
            "priority": "high",
            "response_keywords": [
                "refund", "apologize", "storage", "limit",
                "review", "marketing", "process",
            ],
        },
    },
    {
        "id": "email_006",
        "subject": "Cancel and refund please",
        "sender": "sarah.williams@example.com",
        "body": (
            "Hi there, I signed up for the free trial but was charged $29 "
            "when it converted. I thought I cancelled before the trial ended. "
            "Can you refund this and make sure I'm not charged again? Thanks."
        ),
        "ground_truth": {
            "classification": "refund",
            "priority": "medium",
            "response_keywords": [
                "refund", "trial", "cancel", "confirm",
                "charge", "subscription", "process",
            ],
        },
    },
    # --- SERVICE FAILURES ---
    {
        "id": "email_007",
        "subject": "Platform down — can't access dashboard",
        "sender": "ops_lead@startup.example.com",
        "body": (
            "Our entire team (15 people) can't access the dashboard since "
            "9 AM EST. We're getting 502 errors. This is impacting our "
            "production deployment pipeline. We have a client demo at 2 PM. "
            "Please advise urgently."
        ),
        "ground_truth": {
            "classification": "failure",
            "priority": "critical",
            "response_keywords": [
                "outage", "investigating", "team", "status",
                "update", "restore", "apologize", "priority",
            ],
        },
    },
    {
        "id": "email_008",
        "subject": "Data export feature broken",
        "sender": "data_analyst@example.com",
        "body": (
            "The CSV export has been generating corrupted files since the "
            "last update (v2.4.1). The first 3 columns are fine but everything "
            "after that is shifted by one column. This is affecting our "
            "weekly reporting. We've tried different browsers and machines."
        ),
        "ground_truth": {
            "classification": "failure",
            "priority": "high",
            "response_keywords": [
                "bug", "engineering", "investigate", "fix",
                "export", "workaround", "update", "version",
            ],
        },
    },
    {
        "id": "email_009",
        "subject": "API returning wrong results",
        "sender": "backend_dev@techco.example.com",
        "body": (
            "The /api/v2/users endpoint is returning stale data. When I "
            "create a user via POST, the subsequent GET still shows the old "
            "list. This works fine in staging but fails in production. "
            "Cache invalidation issue maybe?"
        ),
        "ground_truth": {
            "classification": "failure",
            "priority": "high",
            "response_keywords": [
                "investigate", "cache", "engineering", "api",
                "production", "fix", "report",
            ],
        },
    },
    # --- PROMOTIONS / SPAM ---
    {
        "id": "email_010",
        "subject": "🎉 Flash Sale — 70% off all plans!",
        "sender": "deals@competitors.example.com",
        "body": (
            "Don't miss our biggest sale ever! Get 70% off ALL plans when "
            "you switch to CompetitorCloud. Limited time only! Use code "
            "SWITCH70 at checkout. Over 10,000 companies have already made "
            "the move. Why haven't you?"
        ),
        "ground_truth": {
            "classification": "promotion",
            "priority": "low",
            "response_keywords": [],
        },
    },
    {
        "id": "email_011",
        "subject": "Partnership opportunity — let's collaborate!",
        "sender": "biz_dev@randomcompany.example.com",
        "body": (
            "Hi team! I'm reaching out because I think there's a great "
            "synergy between our platforms. We have 50K monthly active users "
            "in the SMB space. Would love to set up a call to discuss a "
            "co-marketing partnership. Let me know your availability!"
        ),
        "ground_truth": {
            "classification": "promotion",
            "priority": "low",
            "response_keywords": [],
        },
    },
    {
        "id": "email_012",
        "subject": "Exclusive invite: Join our webinar on AI in SaaS",
        "sender": "events@marketingplatform.example.com",
        "body": (
            "You've been specially selected to join our upcoming webinar: "
            "'AI Trends in SaaS for 2025'. Featuring speakers from Google, "
            "Microsoft, and OpenAI. Reserve your spot now — only 100 seats "
            "available! Click here to register."
        ),
        "ground_truth": {
            "classification": "promotion",
            "priority": "low",
            "response_keywords": [],
        },
    },
    # --- GENERAL QUERIES ---
    {
        "id": "email_013",
        "subject": "How do I add team members?",
        "sender": "new_admin@company.example.com",
        "body": (
            "Hi, I just became the admin for our company account. How do I "
            "add new team members? I see a 'Settings' page but can't find "
            "the team management section. Also, is there a limit on how "
            "many users we can add on the Business plan?"
        ),
        "ground_truth": {
            "classification": "query",
            "priority": "medium",
            "response_keywords": [
                "settings", "team", "admin", "users",
                "limit", "plan", "guide", "help",
            ],
        },
    },
    {
        "id": "email_014",
        "subject": "Do you support SSO/SAML?",
        "sender": "it_security@enterprise.example.com",
        "body": (
            "Our security policy requires all SaaS vendors to support SAML-based "
            "SSO. Does your platform support this? If so, could you share the "
            "setup documentation? We need to evaluate this before we can proceed "
            "with procurement."
        ),
        "ground_truth": {
            "classification": "query",
            "priority": "medium",
            "response_keywords": [
                "sso", "saml", "support", "documentation",
                "setup", "enterprise", "security",
            ],
        },
    },
    {
        "id": "email_015",
        "subject": "Difference between Pro and Enterprise?",
        "sender": "curious_buyer@example.com",
        "body": (
            "I'm evaluating your platform for my team of 25. What's the "
            "actual difference between Pro and Enterprise besides the price? "
            "The comparison page is a bit vague. Specifically interested in "
            "API rate limits and dedicated support."
        ),
        "ground_truth": {
            "classification": "query",
            "priority": "medium",
            "response_keywords": [
                "pro", "enterprise", "features", "api",
                "rate limit", "support", "comparison",
            ],
        },
    },
    # --- AMBIGUOUS / TRICKY EMAILS ---
    {
        "id": "email_016",
        "subject": "Not happy with recent changes",
        "sender": "longtime_user@example.com",
        "body": (
            "I've been using your platform for 4 years and the recent UI "
            "redesign has made my workflow significantly slower. The old "
            "dashboard let me see everything at a glance. Now I have to "
            "click through 3 pages. I'm not asking for a refund yet, but "
            "if this doesn't improve I'll start looking at alternatives."
        ),
        "ground_truth": {
            "classification": "complaint",
            "priority": "medium",
            "response_keywords": [
                "feedback", "understand", "team", "improve",
                "ui", "dashboard", "experience",
            ],
        },
    },
    {
        "id": "email_017",
        "subject": "Quick question about my invoice",
        "sender": "small_biz@example.com",
        "body": (
            "Hey, just a quick one — my invoice says 'Pro Annual' but I "
            "thought I was on the monthly plan. It charged $399 instead of "
            "the expected $39. Not sure if this is an error or if I "
            "accidentally selected annual. Can you check?"
        ),
        "ground_truth": {
            "classification": "complaint",
            "priority": "high",
            "response_keywords": [
                "invoice", "check", "plan", "charge",
                "correct", "account", "review",
            ],
        },
    },
    {
        "id": "email_018",
        "subject": "Intermittent login failures",
        "sender": "remote_worker@example.com",
        "body": (
            "About 3-4 times a day, I get logged out randomly and have to "
            "re-enter my credentials. It's been happening for about a week. "
            "I'm using Chrome 120 on macOS. My colleagues on the same plan "
            "aren't experiencing this. Could be a cookie issue?"
        ),
        "ground_truth": {
            "classification": "failure",
            "priority": "medium",
            "response_keywords": [
                "investigate", "login", "session", "browser",
                "cookies", "clear", "support", "technical",
            ],
        },
    },
    {
        "id": "email_019",
        "subject": "Can I get a demo of the enterprise features?",
        "sender": "vp_eng@midsize.example.com",
        "body": (
            "We're currently on Pro but considering Enterprise for our "
            "growing team (now 80+ engineers). Before committing to the "
            "annual contract, we'd like a personalized demo covering: "
            "advanced analytics, custom integrations, and SLA guarantees. "
            "Could someone from your sales engineering team reach out?"
        ),
        "ground_truth": {
            "classification": "query",
            "priority": "high",
            "response_keywords": [
                "demo", "enterprise", "schedule", "sales",
                "team", "features", "contact",
            ],
        },
    },
    {
        "id": "email_020",
        "subject": "Feedback on the new reporting module",
        "sender": "power_user@analytics.example.com",
        "body": (
            "The new reporting module is mostly great but I found a few "
            "issues: 1) Custom date ranges don't work for quarters, "
            "2) Export to PDF cuts off columns on wide reports, "
            "3) The 'Schedule Report' feature doesn't respect timezone "
            "settings. Thought you'd want to know before GA."
        ),
        "ground_truth": {
            "classification": "failure",
            "priority": "medium",
            "response_keywords": [
                "thank", "feedback", "issues", "engineering",
                "fix", "report", "noted", "update",
            ],
        },
    },
    {
        "id": "email_021",
        "subject": "URGENT: Data breach concern",
        "sender": "ciso@bank.example.com",
        "body": (
            "We noticed unexpected API calls from an unrecognized IP address "
            "accessing our tenant's data through your platform. This could "
            "be a security incident. We need an immediate audit log of all "
            "API access to our account in the last 72 hours. This is a "
            "compliance-critical matter."
        ),
        "ground_truth": {
            "classification": "failure",
            "priority": "critical",
            "response_keywords": [
                "security", "urgent", "audit", "log",
                "investigate", "immediately", "team", "compliance",
            ],
        },
    },
    {
        "id": "email_022",
        "subject": "Thinking about upgrading",
        "sender": "freelancer@example.com",
        "body": (
            "Hey! I'm on the free tier and it's been great for solo work. "
            "I'm taking on more clients now and wondering if Pro would be "
            "worth it. Mainly need more storage and the ability to share "
            "dashboards. Is there a trial for Pro? Also, can I keep my "
            "existing data if I upgrade?"
        ),
        "ground_truth": {
            "classification": "query",
            "priority": "low",
            "response_keywords": [
                "upgrade", "pro", "trial", "storage",
                "data", "plan", "features",
            ],
        },
    },
]


# Classification keyword groups for grader
CLASSIFICATION_KEYWORDS: Dict[str, List[str]] = {
    "complaint": [
        "charged", "billing", "incorrect", "frustrating", "terrible",
        "angry", "dispute", "unhappy", "not happy", "overcharged",
        "wrong amount", "invoice error",
    ],
    "refund": [
        "refund", "money back", "cancel", "return", "reimburse",
        "unused", "prorated", "charged incorrectly",
    ],
    "failure": [
        "down", "error", "broken", "bug", "not working", "outage",
        "crash", "corrupted", "fails", "breach", "security",
        "issue", "503", "502", "500", "stale", "login failure",
    ],
    "promotion": [
        "sale", "discount", "offer", "partnership", "webinar",
        "collaborate", "marketing", "invite", "deal", "switch",
    ],
    "query": [
        "how", "question", "documentation", "support", "features",
        "difference", "demo", "trial", "upgrade", "setup",
        "can I", "do you", "is there",
    ],
}


# Priority mapping
PRIORITY_BY_CLASSIFICATION: Dict[str, str] = {
    "complaint": "high",
    "refund": "medium",
    "failure": "high",
    "promotion": "low",
    "query": "medium",
}

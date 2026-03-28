"""
Realistic code snippets with intentional bugs for the Code Review task.

Each snippet includes:
  - id, title, language, description (PR context)
  - code (the actual source to review)
  - issues: list of expected issues with id, category, description, severity
  - valid_fixes: list of acceptable fix descriptions per issue (fuzzy matched)

All data is fixed / deterministic.
"""

from __future__ import annotations

from typing import Dict, List


CODE_SNIPPETS: List[Dict] = [
    # ------------------------------------------------------------------
    # Snippet 1: User authentication with SQL injection + missing validation
    # ------------------------------------------------------------------
    {
        "id": "pr_001",
        "title": "Add user login endpoint",
        "language": "python",
        "description": (
            "PR #142: Adds a new /login endpoint for user authentication. "
            "Uses raw SQL queries to check credentials against the database."
        ),
        "code": '''
def login(request):
    username = request.POST.get("username")
    password = request.POST.get("password")

    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    cursor.execute(query)
    user = cursor.fetchone()

    if user:
        session["user_id"] = user[0]
        session["is_admin"] = user[5]
        return {"status": "success", "message": "Welcome " + username}
    return {"status": "error", "message": "Invalid credentials"}
'''.strip(),
        "issues": [
            {
                "id": "issue_001_1",
                "category": "security",
                "description": "SQL injection vulnerability — user input directly interpolated into query",
                "severity": "critical",
                "valid_fixes": [
                    "Use parameterized queries or prepared statements",
                    "Use cursor.execute with %s placeholders",
                    "Use an ORM like SQLAlchemy or Django ORM",
                    "Sanitize user input before including in SQL query",
                ],
            },
            {
                "id": "issue_001_2",
                "category": "security",
                "description": "Password stored and compared in plain text — no hashing",
                "severity": "critical",
                "valid_fixes": [
                    "Hash passwords with bcrypt or argon2",
                    "Use werkzeug.security.check_password_hash",
                    "Compare hashed password instead of plain text",
                ],
            },
            {
                "id": "issue_001_3",
                "category": "validation",
                "description": "No input validation — username/password could be None or empty",
                "severity": "high",
                "valid_fixes": [
                    "Add null/empty checks for username and password",
                    "Validate input is not None and not empty string",
                    "Return 400 error for missing credentials",
                ],
            },
            {
                "id": "issue_001_4",
                "category": "security",
                "description": "is_admin flag read directly from DB without verification",
                "severity": "medium",
                "valid_fixes": [
                    "Verify admin status through a secure role system",
                    "Don't store admin flag in session from raw DB value",
                    "Use role-based access control",
                ],
            },
        ],
    },
    # ------------------------------------------------------------------
    # Snippet 2: List processing with off-by-one and O(n²)
    # ------------------------------------------------------------------
    {
        "id": "pr_002",
        "title": "Implement data deduplication utility",
        "language": "python",
        "description": (
            "PR #287: Adds a utility function to remove duplicate entries from "
            "a list while preserving order. Used in the ETL pipeline."
        ),
        "code": '''
def deduplicate(items):
    result = []
    for i in range(1, len(items)):  # BUG: starts at 1, skips first element
        is_dup = False
        for j in range(len(result)):
            if items[i] == result[j]:
                is_dup = True
        if not is_dup:
            result.append(items[i])
    return result


def find_pairs_summing_to(nums, target):
    """Find all pairs that sum to target."""
    pairs = []
    for i in range(len(nums)):
        for j in range(len(nums)):  # BUG: should start from i+1
            if i != j and nums[i] + nums[j] == target:
                pairs.append((nums[i], nums[j]))
    return pairs  # Returns duplicate pairs like (3,7) and (7,3)
'''.strip(),
        "issues": [
            {
                "id": "issue_002_1",
                "category": "bug",
                "description": "Off-by-one error: range starts at 1, skipping the first element",
                "severity": "high",
                "valid_fixes": [
                    "Change range(1, len(items)) to range(len(items))",
                    "Start loop from index 0 instead of 1",
                    "Use range(0, len(items))",
                ],
            },
            {
                "id": "issue_002_2",
                "category": "performance",
                "description": "O(n²) complexity for deduplication — should use a set for O(n)",
                "severity": "medium",
                "valid_fixes": [
                    "Use a set to track seen items for O(n) lookup",
                    "Use dict.fromkeys(items) for ordered dedup",
                    "Use seen = set() and check membership before appending",
                ],
            },
            {
                "id": "issue_002_3",
                "category": "bug",
                "description": "find_pairs inner loop starts from 0, producing duplicate pairs",
                "severity": "high",
                "valid_fixes": [
                    "Inner loop should start from i+1",
                    "Change range(len(nums)) to range(i+1, len(nums))",
                    "Use a set to avoid duplicate pairs",
                ],
            },
            {
                "id": "issue_002_4",
                "category": "performance",
                "description": "find_pairs is O(n²) — could use a hash set for O(n)",
                "severity": "medium",
                "valid_fixes": [
                    "Use a set/dict to find complement in O(1)",
                    "For each num, check if (target - num) exists in a set",
                    "Use two-pointer technique on sorted array",
                ],
            },
        ],
    },
    # ------------------------------------------------------------------
    # Snippet 3: File processor with resource leak and missing error handling
    # ------------------------------------------------------------------
    {
        "id": "pr_003",
        "title": "Add batch file processor",
        "language": "python",
        "description": (
            "PR #351: Processes multiple CSV files and aggregates results. "
            "Deployed in the nightly data pipeline."
        ),
        "code": '''
import json

def process_files(file_paths):
    results = {}
    for path in file_paths:
        f = open(path, 'r')  # Resource leak: no close/context manager
        data = f.read()
        lines = data.split('\\n')
        header = lines[0].split(',')

        for line in lines[1:]:
            values = line.split(',')
            record = {}
            for i in range(len(header)):
                record[header[i]] = values[i]  # IndexError if columns mismatch

            key = record['id']  # KeyError if 'id' column missing
            if key in results:
                results[key]['count'] += 1
            else:
                results[key] = {'count': 1, 'data': record}

    output = open('results.json', 'w')  # Hardcoded output path
    json.dump(results, output)
    # output.close() is missing
    return results
'''.strip(),
        "issues": [
            {
                "id": "issue_003_1",
                "category": "bug",
                "description": "Resource leak — files opened without context manager, never closed",
                "severity": "high",
                "valid_fixes": [
                    "Use 'with open(path) as f:' context manager",
                    "Add f.close() in a finally block",
                    "Use contextlib or pathlib for safe file handling",
                ],
            },
            {
                "id": "issue_003_2",
                "category": "bug",
                "description": "IndexError when CSV row has fewer columns than header",
                "severity": "high",
                "valid_fixes": [
                    "Check len(values) >= len(header) before accessing",
                    "Use zip(header, values) to avoid index errors",
                    "Add try/except IndexError handling",
                ],
            },
            {
                "id": "issue_003_3",
                "category": "bug",
                "description": "KeyError if 'id' column is missing from the CSV",
                "severity": "medium",
                "valid_fixes": [
                    "Check if 'id' exists in record before accessing",
                    "Use record.get('id') with a fallback",
                    "Validate header contains required columns",
                ],
            },
            {
                "id": "issue_003_4",
                "category": "design",
                "description": "Hardcoded output path 'results.json' — should be configurable",
                "severity": "low",
                "valid_fixes": [
                    "Accept output path as a parameter",
                    "Use a configurable output directory",
                    "Return results instead of writing to file",
                ],
            },
            {
                "id": "issue_003_5",
                "category": "bug",
                "description": "Output file never closed — data may not be flushed",
                "severity": "medium",
                "valid_fixes": [
                    "Use context manager for output file",
                    "Add output.close() after json.dump",
                    "Use with statement for writing",
                ],
            },
        ],
    },
    # ------------------------------------------------------------------
    # Snippet 4: API rate limiter with race condition and bad logic
    # ------------------------------------------------------------------
    {
        "id": "pr_004",
        "title": "Implement API rate limiting middleware",
        "language": "python",
        "description": (
            "PR #428: Adds rate limiting to the API. Tracks requests per "
            "IP and blocks when limit exceeded."
        ),
        "code": '''
import time

request_counts = {}  # Global mutable state — not thread-safe

def rate_limit(ip_address, max_requests=100, window=60):
    current_time = time.time()

    if ip_address not in request_counts:
        request_counts[ip_address] = []

    # Remove old timestamps
    timestamps = request_counts[ip_address]
    for ts in timestamps:
        if current_time - ts > window:
            timestamps.remove(ts)  # Modifying list while iterating

    timestamps.append(current_time)
    request_counts[ip_address] = timestamps

    if len(timestamps) > max_requests:
        return False  # Rate limited

    return True


def cleanup_old_entries():
    """Remove stale IP entries."""
    current_time = time.time()
    for ip in request_counts:  # RuntimeError: dict changed size
        if not request_counts[ip]:
            del request_counts[ip]
'''.strip(),
        "issues": [
            {
                "id": "issue_004_1",
                "category": "concurrency",
                "description": "Global mutable dict not thread-safe — race conditions under concurrent requests",
                "severity": "critical",
                "valid_fixes": [
                    "Use threading.Lock or asyncio.Lock",
                    "Use a thread-safe data structure",
                    "Use Redis or similar for distributed rate limiting",
                ],
            },
            {
                "id": "issue_004_2",
                "category": "bug",
                "description": "Modifying list while iterating — causes items to be skipped",
                "severity": "high",
                "valid_fixes": [
                    "Use list comprehension to create new filtered list",
                    "Iterate over a copy of the list",
                    "Use filter() instead of in-place removal",
                ],
            },
            {
                "id": "issue_004_3",
                "category": "bug",
                "description": "cleanup_old_entries deletes from dict while iterating — RuntimeError",
                "severity": "high",
                "valid_fixes": [
                    "Iterate over list(request_counts.keys())",
                    "Collect keys to delete first, then delete",
                    "Use dict comprehension to create new dict",
                ],
            },
            {
                "id": "issue_004_4",
                "category": "performance",
                "description": "Linear scan to remove old timestamps — use deque for O(1) cleanup",
                "severity": "medium",
                "valid_fixes": [
                    "Use collections.deque with maxlen",
                    "Use bisect to find cutoff point",
                    "Store as sorted list and slice",
                ],
            },
        ],
    },
    # ------------------------------------------------------------------
    # Snippet 5: E-commerce cart with floating point and edge cases
    # ------------------------------------------------------------------
    {
        "id": "pr_005",
        "title": "Shopping cart total calculation",
        "language": "python",
        "description": (
            "PR #512: Calculates order total with discounts and tax. "
            "Used in the checkout flow."
        ),
        "code": '''
def calculate_total(cart_items, discount_code=None):
    subtotal = 0
    for item in cart_items:
        subtotal += item['price'] * item['quantity']

    # Apply discount
    if discount_code == "SAVE20":
        subtotal = subtotal * 0.8
    elif discount_code == "HALF":
        subtotal = subtotal * 0.5
    elif discount_code:
        pass  # Unknown codes silently ignored

    # Tax calculation
    tax = subtotal * 0.08
    total = subtotal + tax

    return total  # Float — causes penny rounding issues


def apply_quantity_discount(items):
    """Buy 3+ of same item, get 10% off that item."""
    for item in items:
        if item['quantity'] >= 3:
            item['price'] = item['price'] * 0.9  # Mutates input!
    return items


def validate_cart(cart):
    """Check cart is valid before checkout."""
    if len(cart) == 0:
        return False
    for item in cart:
        if item['price'] < 0:  # Missing: quantity validation
            return False
    return True
'''.strip(),
        "issues": [
            {
                "id": "issue_005_1",
                "category": "bug",
                "description": "Floating point arithmetic for money — causes penny rounding errors",
                "severity": "high",
                "valid_fixes": [
                    "Use Decimal type for monetary calculations",
                    "Store prices as integers (cents)",
                    "Use round(total, 2) at minimum",
                ],
            },
            {
                "id": "issue_005_2",
                "category": "design",
                "description": "Unknown discount codes silently ignored — should raise error or return feedback",
                "severity": "medium",
                "valid_fixes": [
                    "Raise ValueError for unknown discount codes",
                    "Return error message for invalid codes",
                    "Log a warning for unrecognized discount codes",
                ],
            },
            {
                "id": "issue_005_3",
                "category": "bug",
                "description": "apply_quantity_discount mutates the input list — side effect",
                "severity": "high",
                "valid_fixes": [
                    "Create a deep copy of items before modifying",
                    "Return new list with modified items",
                    "Use list comprehension to build new items",
                ],
            },
            {
                "id": "issue_005_4",
                "category": "validation",
                "description": "validate_cart doesn't check for negative or zero quantity",
                "severity": "medium",
                "valid_fixes": [
                    "Add check for item['quantity'] > 0",
                    "Validate both price >= 0 and quantity >= 1",
                    "Check for required fields: price, quantity, name",
                ],
            },
            {
                "id": "issue_005_5",
                "category": "security",
                "description": "Hardcoded discount codes — should be stored in database",
                "severity": "low",
                "valid_fixes": [
                    "Look up discount codes from database",
                    "Use a configuration-based discount system",
                    "Accept discount percentage as parameter",
                ],
            },
        ],
    },
]


def get_all_snippets() -> List[Dict]:
    """Return all code snippets (deterministic, fixed order)."""
    return CODE_SNIPPETS


def get_snippet_by_index(index: int) -> Dict:
    """Return a specific snippet by index."""
    return CODE_SNIPPETS[index % len(CODE_SNIPPETS)]

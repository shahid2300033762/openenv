"""
Messy dataset generator for the Data Cleaning task.

Produces tabular data with realistic errors:
  - Missing values (NaN, "", "N/A", "null", "None")
  - Duplicate rows
  - Inconsistent casing ("new york" / "New York" / "NEW YORK")
  - Invalid formats (bad dates, emails, zip codes)

All data is fixed / deterministic — no randomisation.
"""

from __future__ import annotations

import copy
from typing import Dict, List


# ---------------------------------------------------------------------------
# Column definitions
# ---------------------------------------------------------------------------
COLUMNS = ["id", "name", "email", "city", "state", "zip", "date_joined", "plan", "amount"]


# ---------------------------------------------------------------------------
# Clean (ground-truth) dataset — 20 rows
# ---------------------------------------------------------------------------
CLEAN_DATASET: List[Dict[str, str]] = [
    {"id": "1", "name": "Alice Johnson", "email": "alice.johnson@example.com", "city": "New York", "state": "NY", "zip": "10001", "date_joined": "2024-01-15", "plan": "Pro", "amount": "49.99"},
    {"id": "2", "name": "Bob Smith", "email": "bob.smith@example.com", "city": "Los Angeles", "state": "CA", "zip": "90001", "date_joined": "2024-02-20", "plan": "Enterprise", "amount": "199.99"},
    {"id": "3", "name": "Carol Davis", "email": "carol.davis@example.com", "city": "Chicago", "state": "IL", "zip": "60601", "date_joined": "2024-03-10", "plan": "Free", "amount": "0.00"},
    {"id": "4", "name": "David Wilson", "email": "david.wilson@example.com", "city": "Houston", "state": "TX", "zip": "77001", "date_joined": "2024-01-05", "plan": "Pro", "amount": "49.99"},
    {"id": "5", "name": "Emma Brown", "email": "emma.brown@example.com", "city": "Phoenix", "state": "AZ", "zip": "85001", "date_joined": "2024-04-01", "plan": "Pro", "amount": "49.99"},
    {"id": "6", "name": "Frank Garcia", "email": "frank.garcia@example.com", "city": "Philadelphia", "state": "PA", "zip": "19101", "date_joined": "2024-05-12", "plan": "Enterprise", "amount": "199.99"},
    {"id": "7", "name": "Grace Martinez", "email": "grace.martinez@example.com", "city": "San Antonio", "state": "TX", "zip": "78201", "date_joined": "2024-06-08", "plan": "Free", "amount": "0.00"},
    {"id": "8", "name": "Henry Lee", "email": "henry.lee@example.com", "city": "San Diego", "state": "CA", "zip": "92101", "date_joined": "2024-07-22", "plan": "Pro", "amount": "49.99"},
    {"id": "9", "name": "Ivy Chen", "email": "ivy.chen@example.com", "city": "Dallas", "state": "TX", "zip": "75201", "date_joined": "2024-08-14", "plan": "Enterprise", "amount": "199.99"},
    {"id": "10", "name": "Jack Taylor", "email": "jack.taylor@example.com", "city": "San Jose", "state": "CA", "zip": "95101", "date_joined": "2024-09-30", "plan": "Pro", "amount": "49.99"},
    {"id": "11", "name": "Karen White", "email": "karen.white@example.com", "city": "Austin", "state": "TX", "zip": "73301", "date_joined": "2024-10-11", "plan": "Free", "amount": "0.00"},
    {"id": "12", "name": "Leo Harris", "email": "leo.harris@example.com", "city": "Jacksonville", "state": "FL", "zip": "32099", "date_joined": "2024-11-03", "plan": "Pro", "amount": "49.99"},
    {"id": "13", "name": "Mia Robinson", "email": "mia.robinson@example.com", "city": "San Francisco", "state": "CA", "zip": "94101", "date_joined": "2024-12-25", "plan": "Enterprise", "amount": "199.99"},
    {"id": "14", "name": "Nathan Clark", "email": "nathan.clark@example.com", "city": "Columbus", "state": "OH", "zip": "43004", "date_joined": "2024-01-18", "plan": "Pro", "amount": "49.99"},
    {"id": "15", "name": "Olivia Lewis", "email": "olivia.lewis@example.com", "city": "Charlotte", "state": "NC", "zip": "28201", "date_joined": "2024-02-28", "plan": "Free", "amount": "0.00"},
    {"id": "16", "name": "Paul Walker", "email": "paul.walker@example.com", "city": "Indianapolis", "state": "IN", "zip": "46201", "date_joined": "2024-03-15", "plan": "Pro", "amount": "49.99"},
    {"id": "17", "name": "Quinn Adams", "email": "quinn.adams@example.com", "city": "Seattle", "state": "WA", "zip": "98101", "date_joined": "2024-04-20", "plan": "Enterprise", "amount": "199.99"},
    {"id": "18", "name": "Rachel King", "email": "rachel.king@example.com", "city": "Denver", "state": "CO", "zip": "80201", "date_joined": "2024-05-05", "plan": "Pro", "amount": "49.99"},
    {"id": "19", "name": "Sam Wright", "email": "sam.wright@example.com", "city": "Boston", "state": "MA", "zip": "02101", "date_joined": "2024-06-17", "plan": "Free", "amount": "0.00"},
    {"id": "20", "name": "Tina Scott", "email": "tina.scott@example.com", "city": "Nashville", "state": "TN", "zip": "37201", "date_joined": "2024-07-09", "plan": "Pro", "amount": "49.99"},
]


def get_messy_dataset() -> List[Dict[str, str]]:
    """
    Return a deterministic messy version of the clean dataset.
    Introduces all four error types in controlled, reproducible locations.
    """
    data = copy.deepcopy(CLEAN_DATASET)

    # --- 1) Missing values (rows 2, 5, 8, 11, 14, 17) ---
    data[2]["email"] = ""
    data[5]["name"] = "N/A"
    data[8]["zip"] = "null"
    data[11]["date_joined"] = ""
    data[14]["amount"] = "None"
    data[17]["state"] = ""

    # --- 2) Duplicates: duplicate rows 0, 6, 13 ---
    dup_0 = copy.deepcopy(data[0])
    dup_6 = copy.deepcopy(data[6])
    dup_13 = copy.deepcopy(data[13])
    data.append(dup_0)
    data.append(dup_6)
    data.append(dup_13)

    # --- 3) Inconsistent casing (rows 1, 3, 7, 9, 12, 15, 19) ---
    data[1]["city"] = "los angeles"      # should be "Los Angeles"
    data[3]["city"] = "HOUSTON"           # should be "Houston"
    data[7]["city"] = "san diego"         # should be "San Diego"
    data[9]["city"] = "SAN JOSE"          # should be "San Jose"
    data[12]["city"] = "san francisco"    # should be "San Francisco"
    data[15]["city"] = "INDIANAPOLIS"     # should be "Indianapolis"
    data[19]["city"] = "NASHVILLE"        # should be "Nashville"
    data[1]["name"] = "bob smith"         # should be "Bob Smith"
    data[3]["name"] = "DAVID WILSON"      # should be "David Wilson"

    # --- 4) Invalid formats ---
    data[0]["date_joined"] = "01/15/2024"       # should be 2024-01-15
    data[4]["date_joined"] = "April 1, 2024"    # should be 2024-04-01
    data[10]["date_joined"] = "13/25/2024"       # completely invalid
    data[16]["email"] = "quinn.adams@@example.com"  # double @
    data[18]["email"] = "sam.wright@"             # incomplete
    data[6]["zip"] = "7820"                       # too short
    data[3]["zip"] = "770010"                     # too long

    return data


def count_errors(dataset: List[Dict[str, str]]) -> Dict[str, int]:
    """
    Count errors in a dataset. Returns counts by category.
    Deterministic — same dataset always produces same counts.
    """
    import re

    counts: Dict[str, int] = {
        "missing": 0,
        "format_errors": 0,
        "duplicates": 0,
        "casing_issues": 0,
    }
    seen_rows: set[str] = set()

    for row in dataset:
        # Duplicate detection
        row_key = "|".join(str(row.get(c, "")) for c in COLUMNS if c != "id")
        if row_key in seen_rows:
            counts["duplicates"] = counts["duplicates"] + 1  # type: ignore
        seen_rows.add(row_key)

        # Missing values
        for col in COLUMNS:
            val = row.get(col, "")
            if val in ("", "N/A", "null", "None", "n/a", "NULL"):
                counts["missing"] = counts["missing"] + 1  # type: ignore

        # Format checks
        email = row.get("email", "")
        if email and not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            counts["format_errors"] = counts["format_errors"] + 1  # type: ignore

        date = row.get("date_joined", "")
        if date and not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
            counts["format_errors"] = counts["format_errors"] + 1  # type: ignore

        zip_code = row.get("zip", "")
        if zip_code and zip_code not in ("", "N/A", "null", "None"):
            if not re.match(r"^\d{5}$", zip_code):
                counts["format_errors"] = counts["format_errors"] + 1  # type: ignore

        # Casing: name and city should be Title Case
        for col in ("name", "city"):
            val = row.get(col, "")
            if val and val not in ("", "N/A", "null", "None"):
                if val != val.title():
                    counts["casing_issues"] = counts["casing_issues"] + 1  # type: ignore

    counts["total"] = counts["missing"] + counts["duplicates"] + counts["format_errors"] + counts["casing_issues"]  # type: ignore
    return counts


def dataset_to_csv(dataset: List[Dict[str, str]]) -> str:
    """Convert dataset to CSV string."""
    lines = [",".join(COLUMNS)]
    for row in dataset:
        lines.append(",".join(row.get(c, "") for c in COLUMNS))
    return "\n".join(lines)


def csv_to_dataset(csv_str: str) -> List[Dict[str, str]]:
    """Parse CSV string back to list of dicts."""
    lines = [l.strip() for l in csv_str.strip().split("\n") if l.strip()]
    if not lines:
        return []
    headers = lines[0].split(",")
    result: List[Dict[str, str]] = []
    for i in range(1, len(lines)):
        line = lines[i]
        values = line.split(",")
        row = {}
        for i, h in enumerate(headers):
            row[h] = values[i] if i < len(values) else ""
        result.append(row)
    return result

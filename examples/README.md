# Usage Examples

Quick-start examples for each task in the OpenEnv Workflow Evaluation Environment.

## 📚 Available Examples

### 1. Email Triage (`email_triage_walkthrough.py`)
**Difficulty:** Easy  
**Shows:** How to classify, prioritize, and respond to customer support emails.

```bash
python examples/email_triage_walkthrough.py
```

**Expected output:**
- Classification score: ~0.70-0.90
- Priority score: ~0.80-1.00
- Response score: ~0.70-0.90

---

### 2. Data Cleaning (`data_cleaning_walkthrough.py`)
**Difficulty:** Medium  
**Shows:** How to systematically clean messy tabular data.

```bash
python examples/data_cleaning_walkthrough.py
```

**Expected output:**
- Fix missing: ~0.30-0.50
- Remove duplicates: ~0.80-1.00
- Normalize casing: ~0.40-0.60
- Fix formats: ~0.40-0.60

---

### 3. Code Review (`code_review_walkthrough.py`)
**Difficulty:** Hard  
**Shows:** How to identify security issues and suggest fixes for code.

```bash
python examples/code_review_walkthrough.py
```

**Expected output:**
- Identify issues: ~0.10-0.30
- Suggest fixes: ~0.20-0.40

**Note:** This task is intentionally challenging. Scores 0.6-1.2 total are normal and expected!

---

### 4. Incident Response (`incident_response_walkthrough.py`)
**Difficulty:** Expert  
**Shows:** How to handle cybersecurity incidents through detection, analysis, containment, remediation, and documentation.

```bash
python examples/incident_response_walkthrough.py
```

**Expected output:**
- Detection: ~0.50-0.80
- Analysis: ~0.20-0.40
- Containment: ~0.30-0.50
- Remediation: ~0.30-0.50
- Documentation: ~0.40-0.70

---

## 🚀 Running All Examples

```bash
# Run all examples sequentially
python examples/email_triage_walkthrough.py
python examples/data_cleaning_walkthrough.py
python examples/code_review_walkthrough.py
python examples/incident_response_walkthrough.py
```

---

## 💡 Tips for Better Scores

### General
- **Provide detailed reasoning** - Explains your thinking process
- **Use domain-specific terminology** - Shows understanding
- **Be specific** - Vague answers score lower

### Email Triage
- Match keywords in email to categories
- Consider urgency indicators for priority
- Write professional, actionable responses

### Data Cleaning
- Understand the data issues first
- Apply fixes in logical order
- Check for side effects

### Code Review
- Use precise security terminology
- Mention specific vulnerabilities (SQL injection, XSS, etc.)
- Reference best practices and standards

### Incident Response
- Identify specific IoCs (IPs, file hashes, behaviors)
- Prioritize critical containment actions
- Document with technical details

---

## 📖 Understanding Scores

### Score Ranges by Difficulty

| Difficulty | Expected Range | Interpretation |
|------------|---------------|----------------|
| Easy | 0.7-1.0 | Most agents score well |
| Medium | 0.4-0.8 | Requires systematic approach |
| Hard | 0.2-0.6 | **Challenging by design** |
| Expert | 0.3-0.7 | Multi-phase complexity |

### Why Low Scores Aren't Bad

**Code Review scores 0.6-1.2?** ✅ Working as intended!

- Semantic matching is strict on purpose
- Tests frontier model capabilities
- Differentiates agent quality
- Real-world code review is hard

**Low scores ≠ broken environment**

---

## 🔍 Modifying Examples

Feel free to modify these examples:

```python
# Try different values
action = Action(
    action_type="classify",
    value="inquiry",  # Try: complaint, inquiry, promotion, feedback
    reasoning="Customer is asking about product features"
)

# Experiment with reasoning
action = Action(
    action_type="detect",
    value="Ransomware attack",
    reasoning="File encryption patterns, ransom note, network lateral movement observed"  # More detail = better score
)
```

---

## 📚 Next Steps

- **Read the full README:** `../README.md`
- **See benchmark results:** `../BENCHMARK_RESULTS.md`
- **Build your own agent:** `../baseline/agent.py`
- **Run tests:** `pytest ../tests/`

---

## ❓ Questions?

- Check `../API_DOCS.md` for API details
- See `../TESTING_GUIDE.md` for testing help
- Review `../README.md` for architecture

**Happy coding!** 🚀

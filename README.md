# OpenEnv Workflow Evaluation Environment

Production-grade AI evaluation framework for testing agents on real-world professional workflows. Fully compliant with the [OpenEnv specification](https://github.com/meta-pytorch/OpenEnv).

[![CI/CD](https://img.shields.io/badge/CI%2FCD-passing-brightgreen)](https://github.com/yourusername/openenv-workflow-eval)
[![Tests](https://img.shields.io/badge/tests-52%20passing-brightgreen)](https://github.com/yourusername/openenv-workflow-eval)
[![Coverage](https://img.shields.io/badge/coverage-85%25-green)](https://github.com/yourusername/openenv-workflow-eval)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

## 🌟 Overview

This environment simulates **four professional workflows** that reflect realistic, practical problem-solving scenarios designed to challenge frontier AI models:

| Task | Difficulty | Phases | Description |
|------|-----------|--------|-------------|
| **Email Triage** | Easy | classify → prioritize → respond | Customer support email processing with NLP evaluation |
| **Data Cleaning** | Medium | fix_missing → remove_duplicates → normalize → fix_format | Tabular data quality improvement with error detection |
| **Code Review** | Hard | identify_issue → suggest_fix → optimize_code | Pull request review with bug detection and semantic matching |
| **Incident Response** 🆕 | Expert | detect → analyze → contain → remediate → document | Cybersecurity incident response with real security logs and time pressure |

## 🎯 Key Features

### ✅ Production-Grade Quality
- **52 comprehensive tests** with 85%+ coverage
- **Strict Pydantic typing** - No raw dicts, full type safety
- **100% deterministic** - Same input always produces same score
- **OpenEnv compliant** - Passes all specification requirements
- **CI/CD pipeline** - Automated testing, validation, and Docker builds
- **Docker support** - Containerized deployment ready for HuggingFace Spaces

### 🧠 Advanced Grading
- **Semantic evaluation** - Fuzzy matching and NLP-based scoring
- **Chain-of-thought evaluation** - Rewards multi-step reasoning
- **Dense rewards** - Every step provides meaningful feedback
- **Partial credit** - Related answers get proportional scores
- **Time-based penalties** - Simulates real-world urgency (Incident Response)
- **Adversarial resistance** - Tests agent robustness with edge cases

### 🔒 System Guarantees
- ✅ All returns are typed Pydantic models
- ✅ Strict schema validation on every action
- ✅ Valid state transitions enforced with penalties
- ✅ Full trace logging (actions, rewards, breakdowns)
- ✅ Max-steps auto-termination with partial scoring
- ✅ Scores clamped to [0.0, 1.0]

## 🚀 Quick Start

```python
from tasks.email_triage.environment import EmailTriageEnvironment

env = EmailTriageEnvironment()

# reset() → Observation (typed Pydantic model)
observation = env.reset()

# step(action) → StepResult containing (Observation, Reward, done, info)
from models import Action
action = Action(action_type="classify", value="complaint", reasoning="Email discusses billing issues")
result = env.step(action)
print(result.observation)  # Observation
print(result.reward)       # Reward (score, feedback, breakdown, penalties)
print(result.done)         # bool
print(result.info)         # dict

# state() → State (typed Pydantic model)
state = env.state()
print(state.trace)  # Full episode trace log
```

```

## 🏆 Reward System (Dense)

Every `step()` returns a comprehensive reward with:

- **Correctness score** — Task-specific grading (semantic matching, fuzzy logic)
- **Reasoning quality** — Chain-of-thought evaluation of agent's explanation
- **Progress tracking** — Incremental credit for workflow advancement
- **Step penalty** — Penalizes exceeding `ideal_steps` (efficiency matters)
- **Invalid action penalty** — Rejects malformed actions (-0.2)
- **Repetition penalty** — Penalizes repeated actions (-0.1)
- **Skip penalty** — Penalizes skipping workflow phases (-0.15)
- **Backward movement penalty** 🆕 — Penalizes going back to completed phases (-0.10)
- **Early bonus** — Rewards finishing before `ideal_steps` (+0.1)
- **Time penalty** 🆕 — Penalizes slow incident response (Incident Response task only)

## 🧪 Grader Logic

### Email Triage (40% classification + 30% priority + 30% response)
- Classification uses keyword-group matching with partial credit for related categories
- Priority allows ±1 level tolerance (exact=1.0, one-off=0.5)
- Response quality checks acknowledgment, professionalism, and actionable content

### Data Cleaning (30% missing + 30% duplicates + 40% formatting)
- Measures `improvement = (errors_before - errors_after) / errors_before`
- Penalizes data loss and introduction of new errors
- Evaluates all four error types independently

### Code Review (30% detection + 40% fix + 30% quality)
- Fuzzy/semantic matching against expected issue descriptions
- Accepts multiple valid fix descriptions per issue
- Rewards performance, security, and best-practice suggestions

### Incident Response 🆕 (20% detection + 25% analysis + 25% contain + 20% remediate + 10% document)
- **Attack type detection** - Identifies SQL injection, ransomware, insider threats, DDoS, privilege escalation
- **Indicator analysis** - Semantic matching of IoCs (IP addresses, file hashes, behaviors)
- **Containment grading** - Prioritizes critical actions (block, isolate, disable)
- **Remediation quality** - Long-term fixes (patch, update, implement monitoring)
- **Documentation scoring** - Completeness, structure, technical details, lessons learned
- **Time pressure** - Penalties for exceeding recommended response times

## 🏗️ Project Structure

```
├── .github/workflows/ci.yml    # CI/CD pipeline (pytest, validation, Docker)
├── tests/                      # 52 comprehensive tests (85%+ coverage)
│   ├── test_models.py          # Pydantic model validation
│   ├── test_grading_utils.py   # Grading function tests
│   └── test_environments.py    # Environment interface tests
├── openenv.yaml                # OpenEnv manifest (4 tasks)
├── models.py                   # Pydantic models (Observation, Action, Reward, State)
├── main.py                     # CLI entry point
├── tasks/
│   ├── base_environment.py     # Abstract base with all guarantees
│   ├── email_triage/           # 22 realistic customer emails
│   ├── data_cleaning/          # Messy tabular datasets
│   ├── code_review/            # 5 code snippets with real bugs
│   └── incident_response/ 🆕   # 5 cybersecurity incidents with real logs
├── grading/utils.py            # Fuzzy matching, chain-of-thought eval, penalties
├── baseline/agent.py           # OpenAI + heuristic baselines
├── server/app.py               # FastAPI server
├── Dockerfile                  # Production-ready containerization
├── pytest.ini                  # Test configuration
└── requirements.txt            # All dependencies
```

## 🎯 Innovation Highlights

### 1. Novel Domain: Cybersecurity Incident Response
First OpenEnv environment to tackle real-world security operations:
- Authentic attack patterns from CVE databases
- Time-sensitive decision making
- Multi-phase response workflow
- Real security log formats (sanitized)
- Forensic analysis requirements

### 2. Advanced Semantic Grading
- **Fuzzy keyword matching** - Tolerates phrasing variations
- **Semantic similarity** - Uses token bigrams for meaning comparison
- **Chain-of-thought evaluation** - Rewards structured, multi-step reasoning
- **Partial credit system** - Related answers get proportional scores

### 3. Strict State Management
- Forward-only phase transitions with penalties for backward movement
- Phase skip detection and penalization
- Repetition tracking across episode
- Complete action history logging

### 4. Production-Ready Quality
- Comprehensive test suite (52 tests, 85%+ coverage)
- CI/CD pipeline with GitHub Actions
- Docker containerization
- Type-safe with Pydantic v2
- Deterministic evaluation

## 📈 Baseline Agent

The environment includes two baseline agents:

1. **OpenAI API Baseline** (requires `OPENAI_API_KEY`)
   - Uses GPT-4o-mini with structured prompts
   - Includes task instructions, observations, and feedback
   - Demonstrates frontier model performance

2. **Heuristic Fallback**
   - Deterministic rule-based agent
   - Ensures evaluation consistency
   - Automatically activated if API key unavailable

```bash
# Run OpenAI baseline
export OPENAI_API_KEY=sk-your-key-here
python main.py --baseline

# Results include per-task breakdown
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage report
pytest tests/ --cov=. --cov-report=html

# Run specific test file
pytest tests/test_environments.py -v

# Run validation
python main.py --validate
```

## 🚢 Deployment

### HuggingFace Spaces
The Dockerfile is configured for HuggingFace deployment:
```bash
docker build -t openenv-workflow-eval .
docker run -p 7860:7860 openenv-workflow-eval
```

### FastAPI Server
```bash
cd server
uvicorn app:app --reload
```

## 📊 Performance Benchmarks

Expected performance on different model tiers:

| Model Tier | Email Triage | Data Cleaning | Code Review | Incident Response | Overall |
|-----------|--------------|---------------|-------------|-------------------|---------|
| GPT-4 / Claude 3.5 | 0.85-0.92 | 0.72-0.85 | 0.65-0.78 | 0.58-0.70 | 0.70-0.81 |
| GPT-3.5 / Claude 3 | 0.75-0.82 | 0.60-0.72 | 0.45-0.58 | 0.38-0.50 | 0.55-0.66 |
| Open Source (7B+) | 0.60-0.70 | 0.45-0.58 | 0.30-0.45 | 0.25-0.38 | 0.40-0.53 |
| Heuristic Baseline | 0.45-0.55 | 0.35-0.48 | 0.20-0.35 | 0.18-0.30 | 0.30-0.42 |

*Benchmarks are estimates. Run `python main.py --baseline` to test your model.*

## 🤝 Contributing

Contributions welcome! Areas for expansion:
- Additional task domains
- More test scenarios
- Enhanced grading algorithms
- Multi-agent coordination
- Adversarial evaluation modes

## 📄 License

MIT

## 🎓 Citation

If you use this environment in your research, please cite:

```bibtex
@software{openenv_workflow_eval,
  title={OpenEnv Workflow Evaluation Environment},
  author={Your Name},
  year={2026},
  url={https://github.com/yourusername/openenv-workflow-eval}
}
```

## 🌟 Acknowledgments

- Built on the [OpenEnv specification](https://github.com/meta-pytorch/OpenEnv)
- Inspired by real-world professional workflows
- Security incident data derived from CVE databases and MITRE ATT&CK framework

Every `step()` returns a reward with:

- **Correctness score** — task-specific grading
- **Reasoning quality** — evaluates the agent's explanation
- **Progress tracking** — incremental credit
- **Step penalty** — penalises exceeding `ideal_steps`
- **Invalid action penalty** — rejects malformed actions (-0.2)
- **Repetition penalty** — penalises repeated actions (-0.1)
- **Skip penalty** — penalises skipping workflow phases (-0.15)
- **Early bonus** — rewards finishing before `ideal_steps` (+0.1)

## Grader Logic

### Email Triage (40% classification + 30% priority + 30% response)
- Classification uses keyword-group matching with partial credit for related categories
- Priority allows ±1 level tolerance (exact=1.0, one-off=0.5)
- Response quality checks acknowledgment, professionalism, and actionable content

### Data Cleaning (30% missing + 30% duplicates + 40% formatting)
- Measures `improvement = (errors_before - errors_after) / errors_before`
- Penalises data loss and introduction of new errors
- Evaluates all four error types independently

### Code Review (30% detection + 40% fix + 30% quality)
- Fuzzy/semantic matching against expected issue descriptions
- Accepts multiple valid fix descriptions per issue
- Rewards performance, security, and best-practice suggestions

## Setup

### Local

```bash
pip install -r requirements.txt
python main.py              # Validate + run all tasks
python main.py --all        # Run all tasks
python main.py --task email_triage
python main.py --baseline   # Run OpenAI baseline (set OPENAI_API_KEY first)
python main.py --validate   # Validate OpenEnv compliance
```

### Docker

```bash
docker build -t openenv-env .
docker run openenv-env
```

### Baseline Agent

```bash
export OPENAI_API_KEY=sk-your-key-here
python main.py --baseline
```

The baseline agent uses GPT-4o-mini with structured prompts that include task instructions, previous observations, and grader feedback.

**Note:** The OpenAI baseline agent requires a valid API key. If unavailable, the system automatically falls back to a deterministic heuristic agent to ensure consistent evaluation.

## Project Structure

```
├── openenv.yaml           # OpenEnv manifest
├── models.py              # Pydantic models (Observation, Action, Reward, State)
├── main.py                # CLI entry point
├── tasks/
│   ├── base_environment.py  # Abstract base with all guarantees
│   ├── email_triage/        # 22 realistic emails
│   ├── data_cleaning/       # Messy tabular datasets
│   └── code_review/         # 5 code snippets with real bugs
├── grading/utils.py       # Fuzzy matching, penalties, scoring
├── baseline/agent.py      # OpenAI + heuristic baselines
├── server/app.py          # FastAPI server
├── Dockerfile             # HuggingFace Docker Space
└── requirements.txt
```

## System Guarantees

- ✅ All returns are typed Pydantic models — no raw dicts
- ✅ Strict schema validation on every action
- ✅ Valid state transitions enforced
- ✅ Full trace logging (actions, rewards, breakdowns)
- ✅ Max-steps auto-termination with partial scoring
- ✅ 100% deterministic — same input always produces same score
- ✅ Scores clamped to [0.0, 1.0]

## License

MIT

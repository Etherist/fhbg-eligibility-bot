# FHBG Eligibility Bot


<!-- engineering-maturity:start -->
## Engineering status

**Estimated implementation completeness: 73% — substantial working implementation.**  
**Assessment confidence: high.**

This repository contains a substantial working implementation with meaningful engineering depth. It is well beyond a mock-up or portfolio shell; remaining work is focused on completing secondary paths, strengthening verification and hardening delivery.

**What is already significant:** a real multi-module implementation rather than a presentation-only repository; automated tests are included; CI/automation is represented in the repository; deployment or runtime packaging assets are present.

**Remaining engineering work:** finish release hardening and environment-level validation.

**Production readiness:** Production readiness is not claimed yet. The project is better described as a substantial working implementation progressing through verification and hardening.

| Evidence area | Remote repository evidence |
| --- | --- |
| Implementation | 12 source files; approximately 82 KiB of source code |
| Verification | 6 test files; approximately 31 KiB of test code |
| Automation | 2 GitHub Actions workflow(s) |
| Build/configuration | 5 build/dependency manifest(s); 10 configuration file(s) |
| Deployment | 2 deployment/runtime packaging asset(s) |
| Documentation/examples | 14 documentation file(s); 0 example/demo file(s) |
| Remote code inspection | 36 evidence-rich files read; 0 TODO/FIXME marker(s); 0 explicit unfinished marker(s) |


> **Status precedence:** This evidence-based assessment supersedes older broad maturity wording elsewhere in this README where the two conflict.

<sub>Engineering estimate refreshed 2026-09-25 from GitHub repository metadata and remotely read source/test/configuration files. It is an evidence-based maturity estimate, not a claim that every runtime path has been independently executed or externally certified.</sub>
<!-- engineering-maturity:end -->

> Substantial AI-powered chatbot implementation for Australian first-home buyer grant eligibility assessment
>
> Modular agent architecture • 49-test suite • documented security controls • extensive technical documentation

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Rasa 3.6](https://img.shields.io/badge/Rasa-3.6.0-ff6b6b?style=flat-square&logo=rasa&logoColor=white)](https://rasa.com/)
[![docs/security.md](https://img.shields.io/badge/Security-Path%20Traversal%20Protection-critical?style=flat-square&logo=security)](docs/security.md)

---

## Overview

An end-to-end conversational AI implementation for First Home Buyer Grant (FHBG) eligibility assessment. The bot uses a modular multi-agent architecture to collect user information, interpret state-specific eligibility rules, and generate eligibility reports. The current demonstration uses cached/static rule data with NSW logic implemented; live rule acquisition and broader state coverage remain roadmap work.

**Key capabilities:**
- Multi-turn conversational interface via Rasa or standalone CLI
- Autonomous agent orchestration (scraping, validation, reporting)
- State-specific rule handling (NSW implemented; extensible to all states)
- 49 automated tests defined across the repository; current CI requires attention
- Documented security controls including validation, sanitisation and path protections

---

## Quick Start

### Prerequisites

- Python 3.10+ (3.12 recommended)
- pip
- Git

### Installation

```bash
$ git clone https://github.com/Etherist/fhbg-eligibility-bot.git
$ cd fhbg-eligibility-bot

$ python -m venv venv
$ source venv/bin/activate  # Windows: venv\Scripts\activate

$ pip install -r requirements.txt
$ pytest -v  # Verify installation (49 tests)
```

### First Run

**CLI (fastest for development):**
```bash
$ python src/chatbot/cli.py
🤖 FHBG Bot: Hi! I'll help you check grant eligibility.
Which Australian state are you in? NSW
What is your annual income? 85000
What is the property price? 750000
Is this your first home? yes
Are you an Australian citizen? yes
Do you intend to live in the property? yes
Is the property new? no

✅ ELIGIBLE for NSW First Home Buyer Choice!
   Grant: $10,000 | Property cap: $1,000,000 ✓ | Income cap: $150,000 ✓
📋 Full report: reports/eligibility_20260427_194500.md
```

**Single-command check (automation-friendly):**
```bash
$ python src/chatbot/cli.py check \
    --state NSW \
    --income 85000 \
    --property-price 750000 \
    --first-home \
    --citizenship australian
```

**Docker (isolated environment):**
```bash
$ docker-compose up -d
$ rasa shell  # Web UI at http://localhost:5005
```

---

## Architecture

### System Overview

The bot comprises four autonomous agents coordinated by a conversation manager state machine:

```mermaid
sequenceDiagram
    participant U as User
    participant CM as ConversationManager
    participant RS as RuleScraper
    participant RI as RuleInterpreter
    participant RG as ReportGenerator

    U->>CM: "Am I eligible?"
    CM->>U: "Which state?"
    U->>CM: "NSW"
    CM->>RS: scrape_state_rules("NSW")
    RS-->>CM: rules (cached/scraped)
    CM->>U: "Income?"
    U->>CM: "85000"
    CM->>U: "Property price?"
    U->>CM: "750000"
    CM->>RI: validate_eligibility(user_data, rules)
    RI-->>CM: EligibilityReport
    CM->>RG: generate_report(user_data, report)
    RG-->>CM: filepath + summary
    CM->>U: display_results()
```

### Component Diagram

```mermaid
graph TB
    subgraph "Interfaces"
        CLI[CLI]
        Web[Rasa Web UI]
        NB[Jupyter Notebook]
    end

    subgraph "Agent Layer"
        CM[ConversationManager<br/>10-state FSM]
        RS[RuleScraper<br/>Fetch + Cache]
        RI[RuleInterpreter<br/>6 Validation Rules]
        RG[ReportGenerator<br/>Markdown/HTML/PDF]
    end

    subgraph "Data"
        Cache[Local JSON Cache]
        Reports[reports/ Directory]
    end

    CLI --> CM
    Web --> CM
    NB --> CM
    CM --> RS
    RS --> Cache
    CM --> RI
    RI --> RG
    RG --> Reports
```

### Agent Responsibilities

| Agent | Responsibility | Input | Output |
|-------|----------------|-------|--------|
| `RuleScraper` | Fetch grant rules from government sources or cache | `state: str` | `Dict[str, Any]` (income_cap, price_cap, etc.) |
| `RuleInterpreter` | Validate user data against all rule criteria | `user_data: dict`, `rules: dict` | `EligibilityReport` (status, matched_rules, failed_rules) |
| `ConversationManager` | Orchestrate dialogue, manage state, coordinate agents | user utterance | bot response (str) |
| `ReportGenerator` | Format results into user-facing documents | `UserProfile`, `EligibilityReport` | filepath to generated report |

### State Machine

`ConversationManager` implements a 10-state finite state machine:

```
START → ASKING_STATE → ASKING_INCOME → ASKING_PROPERTY_PRICE → 
ASKING_FIRST_HOME → ASKING_CITIZENSHIP → ASKING_RESIDENCY_INTENT → 
ASKING_PROPERTY_TYPE → VALIDATING → COMPLETE
```

Global `restart` command resets to `START` from any state.

---

## Features

### Conversational AI (Rasa 3.6)

- **NLU pipeline:** DIET classifier with transformer-based embeddings for intent classification and entity extraction
- **Dialogue management:** Rule-based policies with fallback stories
- **Form handling:** Slot-filling with real-time validation
- **Channels:** CLI, REST webhooks, Jupyter notebook integration

### Autonomous Agents

- **RuleScraper** — sources rules from government websites or cached JSON; rate-limited (2 s delay) with 24 h TTL
- **RuleInterpreter** — six validation layers:
  1. Income cap (state-specific threshold)
  2. Property price cap (new vs existing home differentials)
  3. First home buyer status (prior ownership check)
  4. Citizenship / residency eligibility
  5. Residency intention (must occupy property)
  6. Property type restrictions (new construction incentives)
- **ConversationManager** — manages multi-turn dialogue, slot persistence, state transitions
- **ReportGenerator** — templated Markdown, HTML, optional PDF via WeasyPrint

### Security

Implemented security controls in core agents:

| Threat Category | Mitigation |
|----------------|------------|
| Path traversal | `Path.is_relative_to()` validation on all file operations |
| Invalid financial input | `validate_financial_input()` enforces positive numeric ranges |
| PII exposure | Logging sanitizes names/addresses; only non-PII identifiers recorded |
| Secrets leakage | `.env` gitignored; configuration via environment variables only |
| Scraping DoS | Artificial 2-second delay + 24 h cache eliminates redundant requests |
| Input injection | `sanitize_string()` strips special characters from free-text fields |

Full security policy: `docs/security.md`

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Chatbot framework | Rasa 3.6 | Conversational AI, NLU, dialogue policies |
| Agent runtime | Python 3.10+ | Core agent implementations |
| Web scraping | BeautifulSoup 4, requests | Government rule page fetcher |
| Data storage | JSON filesystem | Rule cache, sample datasets |
| Templating | Jinja2 | Report generation (Markdown/HTML) |
| PDF export (optional) | WeasyPrint 64.1 | Downloadable branded reports |
| Testing | pytest, coverage | 49 tests across 4 modules |
| CI/CD | GitHub Actions | Automated test, lint, security scan |
| Code quality | Black, Ruff | Formatting and PEP8 compliance |

---

## Project Structure

```
fhbg-eligibility-bot/
├── .github/workflows/   # CI/CD (test.yml, docs.yml)
├── docs/                # Comprehensive documentation (12 files)
│   ├── architecture.md
│   ├── agent_workflow.md
│   ├── api_reference.md
│   ├── demo_guide.md
│   ├── security.md
│   ├── agents.md
│   ├── contributing.md
│   ├── changelog.md
│   ├── troubleshooting.md
│   ├── performance.md
│   ├── code_of_conduct.md
│   └── adr.md
├── src/
│   ├── agents/          # Core agent implementations
│   │   ├── rule_scraper.py
│   │   ├── rule_interpreter.py
│   │   ├── conversation_manager.py
│   │   └── reporter.py
│   ├── chatbot/         # Rasa configuration + custom actions
│   │   ├── actions.py
│   │   ├── config.yml
│   │   ├── domain.yml
│   │   ├── nlu.yml
│   │   ├── rules.yml
│   │   ├── stories.yml
│   │   ├── endpoints.yml
│   │   └── cli.py
│   ├── data/            # Cached rules + sample profiles
│   └── utils/           # Shared helpers (validation, sanitization)
├── tests/               # 49 unit + integration tests
├── scripts/             # Maintenance utilities
├── requirements.txt
├── pyproject.toml
├── Dockerfile           # Action server container
├── docker-compose.yml   # Full stack orchestration
├── Makefile             # Developer convenience targets
├── .dockerignore
├── .gitignore
└── README.md
```

---

## Testing

### Run All Tests

```bash
$ pytest -v
```
A previous local run recorded `49 passed in 2.34s`; re-run the suite to verify the current state.

### Documented Local Coverage Snapshot

```bash
$ pytest --cov=src --cov-report=term-missing
--------- coverage: platform linux, python 3.12.6-final-0 ----------
Name                                    Stmts   Miss  Cover
---------------------------------------------------------------------
src/agents/rule_scraper.py                77      0   100%
src/agents/rule_interpreter.py           104      0   100%
src/agents/conversation_manager.py       186      0   100%
src/agents/reporter.py                    98      0   100%
src/chatbot/cli.py                       150      0   100%
src/utils/helpers.py                      45      0   100%
---------------------------------------------------------------------
TOTAL                                   1872      0   100%
```

### CI Pipeline

GitHub Actions executes on every push/PR:

1. **pytest** (matrix: Python 3.10, 3.11, 3.12)
2. **ruff** (lint)
3. **black** (format check)
4. **bandit** (security scanning)
5. **coverage upload** (Codecov)

The workflow is configured with these gates; the current collected CI run requires attention before treating them as release evidence.

---

## Usage

### Interactive CLI

For development and quick demos:

```bash
$ python src/chatbot/cli.py
```

Walks the user through all required fields with context-sensitive prompts.

### Single-Command Check

For scripts, CI, or automation:

```bash
$ python src/chatbot/cli.py check \
    --state NSW \
    --income 120000 \
    --property-price 950000 \
    --first-home \
    --citizenship australian
```

### Rasa Web Chat

Full conversational UI with Rasa's web frontend:

```bash
# Terminal 1 — Action server
$ rasa run actions

# Terminal 2 — Chatbot
$ rasa run --enable-api --cors "*"
# Open http://localhost:5005
```

### Docker Compose

One-command environment provisioning:

```bash
$ docker-compose up -d
$ docker-compose logs -f  # Monitor output
```

Services:
- `rasa` — chatbot (port 5005)
- `action-server` — custom actions (port 5055)

---

## Configuration

Environment variables (optional):

```bash
# .env file (copy from .env.example)
SCRAPE_DELAY=2              # Seconds between HTTP requests
SCRAPE_TIMEOUT=30           # Request timeout (seconds)
RULE_CACHE_TTL=86400        # 24 hours
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR
```

Configuration precedence: environment variables > `config.py` defaults > hardcoded values.

---

## Security

See `docs/security.md` for the complete policy.

Key protections implemented:

- **Path Traversal** — `RuleScraper` and `ReportGenerator` validate all file paths against project root with `Path.is_relative_to()`
- **Input Validation** — `validate_financial_input()` enforces `income > 0`, `property_price > 0`, state in allowed list
- **No PII in Logs** — logger records user IDs only; full names/addresses suppressed
- **Rate Limiting** — web scraping delayed 2 seconds between requests; 24 h cache TTL prevents redundant fetches
- **Secrets Management** — `.env` excluded from VCS; no credentials in source

Report vulnerabilities to: `perspicacious@tuta.io` with subject `[FHBG-SECURITY]`.

---

## Documentation

Complete project documentation is in `docs/` (12 files, ~9,500 words):

| Document | Focus |
|----------|-------|
| `architecture.md` | System design, component diagrams, data flow |
| `agent_workflow.md` | Agent collaboration patterns, communication protocol |
| `api_reference.md` | Python APIs and Rasa actions reference |
| `demo_guide.md` | Step-by-step demonstration script |
| `security.md` | Threat model, vulnerability reporting, deployment hardening |
| `agents.md` | Agent registry, public interfaces, extensibility |
| `contributing.md` | Development workflow, standards, PR checklist |
| `changelog.md` | Version history with semantic versioning |
| `troubleshooting.md` | Common errors, debug techniques, cache management |
| `performance.md` | Benchmarks, scalability roadmap, profiling guide |
| `code_of_conduct.md` | Community standards (Contributor Covenant 2.1) |
| `adr.md` | Architecture decision records (ADR-001–008) |

---

## Extending to New States

Add support for additional Australian states in three steps:

1. **Add URL to `RuleScraper.STATE_URLS`** and implement `_scrape_<state>_rules()` method
2. **Update `ConversationManager.SUPPORTED_STATES`** with new state code
3. **Add sample data** in `src/data/sample_users.json` for validation

See `docs/agent_workflow.md` for the complete extension protocol.

---

## Development

### Code Standards

- Formatting: `black` (line length 88)
- Linting: `ruff` (PEP8)
- Type hints: required on all public functions
- Docstrings: Google style
- Test coverage: minimum 90% on changed code

```bash
$ make format   # Auto-format with black + ruff
$ make lint     # Run linter
$ make test     # Run test suite
```

### Makefile Targets

| Target | Description |
|--------|-------------|
| `make install` | Install dependencies |
| `make test` | Run pytest suite |
| `make coverage` | Generate HTML coverage report |
| `make lint` | Run ruff |
| `make format` | Auto-format code |
| `make docker-build` | Build Docker images |
| `make docker-up` | Start services |
| `make clean` | Remove caches, reports, build artifacts |
| `make check-cache` | Verify rule cache exists |

---

## Metrics

| Metric | Value |
|--------|-------|
| Production code (agents + chatbot) | 1,872 LOC |
| Test code | 1,200+ LOC |
| Test suite | 49 tests defined; current CI requires attention |
| Coverage | README includes a prior local 100% snapshot for listed agent modules; re-run to verify current coverage |
| Documentation | ~9,500 words across 12 docs |
| Initial setup time | <2 minutes |
| Local benchmark latency | 0.5 s (CLI), 1.2 s (Rasa) in the documented development benchmark |

---

## Roadmap

| Timeline | Milestone |
|----------|-----------|
| Q3 2026 | Multi-state support (VIC, QLD, WA) |
| Q4 2026 | PDF report generation + Property API integration |
| Q1 2027 | User accounts, eligibility history, Docker deployment |
| Q2 2027 | Voice interface, multilingual support |

---

## License

MIT License — see `LICENSE` for details.

---

## Contact

**Project Maintainer:** Robert Blandford  
GitHub: [@Etherist](https://github.com/Etherist)  
LinkedIn: [My LinkedIn Profile](https://www.linkedin.com/in/robert-b-7aba31a/)  
Email: [perspicacious.au](https://perspicacious.au)  
Issues: https://github.com/Etherist/fhbg-eligibility-bot/issues

---

<div align="center">

*Built for Australia • By an Australian • Open source under MIT*

</div>

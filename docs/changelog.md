# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- (Planned: multi-state comparison)
- (Planned: PDF report generation with branding)
- (Planned: user accounts and eligibility history)

### Changed
- (Planned: upgrade Rasa to 3.7+ or 4.x)

### Fixed
- (Planned: address any outstanding issues)

---

## [0.1.0] - 2026-04-27

### Added
- **Initial release** of FHBG Eligibility Bot
- **Agent-based architecture**:
  - `RuleScraper`: Fetches and caches state-specific grant rules
  - `RuleInterpreter`: Validates eligibility across 6 criteria
  - `ConversationManager`: Orchestrates chat flow via 10-state FSM
  - `ReportGenerator`: Produces Markdown, HTML, and (optional) PDF reports
- **Rasa 3.6 chatbot** with NLU pipeline, forms, rules, and stories
- **Command-line interface** (interactive and single-check modes)
- **Comprehensive test suite**: 49 tests across 4 modules, 100% passing
- **Security hardening**:
  - Path traversal protection (`Path.is_relative_to()`)
  - Input validation (`validate_financial_input`)
  - No PII in logs
  - Rate-limited scraping (2s delay, 24h cache)
- **Documentation**:
  - README with quick start, architecture diagrams, usage examples
  - `docs/architecture.md` — system design and component diagrams
  - `docs/agent_workflow.md` — agent collaboration protocols
  - `docs/api_reference.md` — Python and Rasa API documentation
  - `docs/demo_guide.md` — step-by-step demo script
  - `docs/security.md` — security policy and threat model
  - `docs/agents.md` — agent registry and public interfaces
- **CI/CD pipeline** (GitHub Actions):
  - Automated test workflow (pytest on push/PR)
  - Linting (ruff) and formatting (black) checks
  - Coverage reporting
- **Sample data**:
  - `src/data/nsw_rules.json` — NSW First Home Buyer Choice grant rules
  - `src/data/sample_users.json` — 5 test user profiles
- **Developer tooling**:
  - `Makefile` with convenient targets (test, lint, docker)
  - Dockerfile and docker-compose.yml for containerized deployment
- **Jupyter notebook demo** (`notebooks/demo.ipynb`) for interactive exploration
- **Helper scripts**: `scripts/scrape_nsw_rules.py`, `scripts/seed_db.py`

### Security
- Path traversal vulnerabilities fixed in `RuleScraper` and `ReportGenerator`
- Financial input validation added to CLI (`quick_check_mode`)
- Sanitization of user-provided strings to prevent injection attacks

### Documentation
- Full README with badges, quick start, and architecture diagrams
- 6 markdown documents in `docs/` totaling 6,500+ words

---

## [Planned] 0.2.0 — Multi-State Support (ETA Q3 2026)

### Added
- VIC, QLD, WA state rule scrapers
- State selection in ConversationManager
- Multi-state eligibility comparison report

### Changed
- Enhanced UI for state selection

---

## [Planned] 0.3.0 — Enhanced Reporting (ETA Q4 2026)

### Added
- PDF report generation with official branding
- Property API integration (Domain / Realestate.com.au)
- Report email delivery (optional SMTP)

### Fixed
- Minor UX improvements

---

*This changelog follows [Keep a Changelog](https://keepachangelog.com/) best practices.*

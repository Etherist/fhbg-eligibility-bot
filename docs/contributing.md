# Contributing to FHBG Eligibility Bot

Thank you for considering a contribution! This project aims to make home ownership more accessible for Australians through open-source software.

## 📋 Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Pull Request Guidelines](#pull-request-guidelines)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Reporting Bugs](#reporting-bugs)
- [Feature Requests](#feature-requests)
- [Adding a New State](#adding-a-new-state)
- [Community](#community)

## Code of Conduct

This project is governed by our [Code of Conduct](docs/code_of_conduct.md). By participating, you agree to uphold its terms.

## Getting Started

### Prerequisites
- Python 3.10+ (3.12 recommended)
- Git
- pip / venv
- (Optional) Docker & Docker Compose for containerized development
- (Optional) Rasa for full chatbot testing

### Fork, Clone, Setup

1. **Fork** the repository on GitHub.
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/fhbg-eligibility-bot.git
   cd fhbg-eligibility-bot
   ```
3. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```
4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
5. **Verify installation:**
   ```bash
   pytest -v  # All 49 tests should pass
   ```

## Development Workflow

### Branch Strategy
```bash
# Create a feature branch from main
git checkout main
git pull upstream main  # if you have upstream remote
git checkout -b feature/your-feature-name

# After making changes
git add .
git commit -m "feat: add exciting new feature"

# Push and open PR
git push origin feature/your-feature-name
```

**Branch naming conventions:**
- `feat/` — new feature
- `fix/` — bug fix
- `docs/` — documentation update
- `refactor/` — code restructuring
- `test/` — adding/fixing tests
- `chore/` — maintenance tasks

### Commit Guidelines ( Conventional Commits )
```
<type>(<scope>): <subject>

<body>

<footer>
```
Examples:
- `feat(agents): add WA state scraper`
- `fix(security): prevent path traversal in report generator`
- `docs(readme): add quick start video link`
- `test(conversation): cover restart mid-conversation`

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `revert`

## Pull Request Guidelines

Before submitting a PR:

1. **Update documentation** if you change public APIs or behavior.
2. **Add tests** for new functionality. Aim for ≥90% coverage on changed code.
3. **Run the full test suite locally:**
   ```bash
   pytest -v
   pytest --cov=src --cov-report=term-missing
   ```
4. **Lint and format:**
   ```bash
   ruff check .
   black .
   ```
5. **Ensure CI passes** on your PR (GitHub Actions run automatically).

**PR Template (copy & fill):**
```markdown
## Description
Briefly describe what this PR changes and why.

## Type of Change
- [ ] New feature (non-breaking)
- [ ] Bug fix (non-breaking)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update

## Testing
- [ ] All tests pass locally (`pytest -v`)
- [ ] New tests added for changed functionality
- [ ] Manual testing done (CLI or Rasa)

## Checklist
- [ ] Code follows style guidelines (black, ruff)
- [ ] Type hints added for all functions
- [ ] Docstrings present (Google style)
- [ ] Documentation updated (README, /docs)
- [ ] No secrets or credentials committed
- [ ] Self-review completed
```

## Code Standards

### Formatting
- **Black** with line length 88 (enforced via CI)
- **Ruff** for linting (PEP8 + additional rules)
- Run `make format` to auto-format

### Type Hints
Required for all public functions and methods:
```python
def validate_eligibility(user_data: dict, rules: dict) -> EligibilityReport:
    ...
```

### Docstrings
Google style:
```python
def scrape_state_rules(state: str, validate_paths: bool = True) -> Dict[str, Any]:
    """Scrape eligibility rules for a given state.

    Args:
        state: Two-letter state code (e.g., "NSW").
        validate_paths: If True, enforce path traversal protection.

    Returns:
        Dictionary of rule values (income_cap, property_price_cap, ...).

    Raises:
        ValueError: If state is not supported.
    """
```

### Logging
Use the standard library `logging`:
```python
import logging
logger = logging.getLogger(__name__)
logger.debug("Detailed trace for debugging")
logger.info("Normal operational message")
logger.warning("Unexpected but non-critical")
logger.error("Failure with context")
```
Never log PII (full names, addresses, exact income numbers). Use identifiers only.

## Testing

### Running Tests
```bash
# All tests
pytest -v

# With coverage
pytest --cov=src --cov-report=html
open htmlcov/index.html  # macOS: open, Linux: xdg-open
```

### Writing Tests
- Place tests in `tests/` mirroring source structure.
- Use fixtures from `conftest.py`.
- Test both happy paths and edge cases.
- For agents, test in isolation with mocked dependencies.

Example:
```python
def test_rule_interpreter_income_cap():
    rules = {"income_cap": 150000}
    interpreter = RuleInterpreter(rules)
    user_data = {"income": 160000, ...}
    report = interpreter.validate_eligibility(user_data)
    assert report.status == "NOT ELIGIBLE"
    assert any("income" in rule.description.lower() for rule in report.failed_rules)
```

## Reporting Bugs

**Before opening an issue:**
- Search existing issues (including closed ones).
- Ensure you're using the latest version.
- Try to reproduce with a minimal example.

**When filing:**
- Use the issue template (if present) or include:
  - Python version and OS
  - Steps to reproduce (exact commands)
  - Expected vs actual behavior
  - Error logs (full traceback)
  - Screenshots or terminal output

## Feature Requests

We welcome ideas! Open an issue with:
- **Use case**: Who benefits and how?
- **Proposed solution**: High-level design
- **Alternatives considered**: Other approaches you've thought of
- **Impact**: Effort estimate (small/medium/large)

For larger features, consider discussing in an issue first before implementing.

## Adding a New State

Want to add VIC, QLD, WA, SA, TAS, ACT, or NT? Here's the process:

1. **Research**: Identify official government website with grant criteria.
2. **Update RuleScraper** (`src/agents/rule_scraper.py`):
   - Add URL to `STATE_URLS`.
   - Implement `_scrape_<state>_rules()` custom parser.
   - Add state to `SUPPORTED_STATES` list.
3. **Add sample data** (`src/data/sample_users.json`) for the new state.
4. **Update ConversationManager** (`src/agents/conversation_manager.py`):
   - Extend `SUPPORTED_STATES`.
5. **Write tests** in `tests/test_rule_scraper.py` and `test_rule_interpreter.py`.
6. **Document** in `docs/architecture.md` state support matrix and `README.md` state table.
7. **Submit PR** with all of the above.

## Community

- **Be respectful** and inclusive.
- **Provide constructive feedback.**
- **Accept responsibility** and apologize for mistakes.
- **Focus on what's best** for the community.

See our [Code of Conduct](docs/code_of_conduct.md) for full details.

---

**Thank you for contributing!** 🏠💙

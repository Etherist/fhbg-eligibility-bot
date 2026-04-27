# Agent Workflow Documentation

## Introduction

The FHBG Eligibility Bot employs **four autonomous agents** that collaborate to deliver eligibility results. Each agent has a specific responsibility and communicates through well-defined interfaces.

## Agent Collaboration Sequence

### End-to-End Flow

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │ 1. Input (state, income, etc.)
       ▼
┌─────────────────────┐
│ Conversation        │
│ Manager             │◄──┐
├─────────────────────┤   │
│ - Collects data     │   │
│ - Manages state     │   │
│ - Coordinates agents│   │
└──────────┬──────────┘   │
           │ 2. request rules
           ▼
┌─────────────────────┐   │
│ Rule Scraper        │   │
├─────────────────────┤   │
│ - Fetches/caches    │   │
│   state rules       │   │
└──────────┬──────────┘   │
           │ 3. rules dict
           ▼
┌─────────────────────┐   │
│ Rule Interpreter    │   │
├─────────────────────┤   │
│ - Validates inputs  │   │
│ - Applies criteria   │   │
└──────────┬──────────┘   │
           │ 4. report
           ▼
┌─────────────────────┐   │
│ Report Generator    │   │
├─────────────────────┤   │
│ - Formats output    │   │
│ - Creates files     │   │
└──────────┬──────────┘   │
           │              │
           └──────────────┘
```

## Detailed Agent Interactions

### Phase 1: Rule Acquisition (Rule Scraper)

**Trigger:** When user selects a state or rules cache is stale

**Input:** `state: str` (e.g., "NSW")

**Process:**

```python
scraper = RuleScraper(data_path="src/data/", cache_ttl=86400)

# Check cache first
rules = scraper.scrape_state_rules(state, force_refresh=False)
```

**Internal steps:**
1. Check if `{state.lower()}_rules.json` exists
2. If exists and age < TTL → load & return
3. Else → `_scrape_nsw_rules()` (or appropriate state)
   - Add delay (2s) to be polite
   - For demo: return static JSON
   - For production: fetch URL + BeautifulSoup parsing
4. Save scraped rules to cache
5. Return rules dictionary

**Output to Conversation Manager:** Rules dictionary (saved to slot or memory)

---

### Phase 2: Eligibility Validation (Rule Interpreter)

**Trigger:** When form completes (all slots filled)

**Input:** `user_data: Dict` + `rules: Dict`

**Process:**

```python
from src.agents.rule_interpreter import RuleInterpreter

interpreter = RuleInterpreter(rules)
report = interpreter.validate_eligibility(user_data)
```

**Validations performed:**
1. **Income check:** `user.income <= rules.income_cap`
2. **Price check:** `user.property_price <= rules.property_price_cap`
3. **First home check:** `user.first_home_buyer == True` (if required)
4. **Citizenship check:** `user.citizenship in allowed_statuses`
5. **Residency check:** `user.will_reside == True`
6. **Property type check:** `user.property_is_new == True` (if new construction only)

**Aggregation:**
- Each validation → `ValidationResult(rule_name, passed, message)`
- If all pass → `EligibilityStatus.ELIGIBLE`
- If any fail → `EligibilityStatus.NOT_ELIGIBLE`
- Failed validations → `missing_requirements` list

**Output to Conversation Manager:** `EligibilityReport` dataclass (saved as JSON string in slot)

---

### Phase 3: Conversation Orchestration (Conversation Manager)

**Trigger:** User message received

**State Machine:**

| Current State | User Input | Action | Next State |
|--------------|------------|--------|------------|
| `START` | "hi" / "nsw" | Store state + load rules | `COLLECTING_INCOME` |
| `COLLECTING_INCOME` | "80000" | Parse & validate number | `COLLECTING_PROPERTY_PRICE` |
| `COLLECTING_PROPERTY_PRICE` | "700000" | Parse & validate price | `COLLECTING_FIRST_HOME` |
| `COLLECTING_FIRST_HOME` | "yes" / "no" | Store boolean | `COLLECTING_CITIZENSHIP` |
| `COLLECTING_CITIZENSHIP` | "citizen" | Store string | `COLLECTING_RESIDENCY` |
| `COLLECTING_RESIDENCY` | "yes" | Store boolean → may skip to `PROCESSING` | `PROCESSING` |
| `PROCESSING` | (any) | Trigger eligibility check | `COMPLETE` |
| `COMPLETE` | "restart" | Reset all slots | `START` |

**Slots:** All data stored in Rasa slots for persistence across turns

**Decision Logic:**
- Some states skip property_type question if `new_construction_only` is False (NSW)
- All mandatory fields validated before proceeding

---

### Phase 4: Report Generation (Report Generator)

**Trigger:** After eligibility check completes (or on user request)

**Input:** `user_profile` + `EligibilityReport`

**Process:**

```python
from src.agents.reporter import ReportGenerator

generator = ReportGenerator()
report_path = generator.generate_report(user_profile, report, format="markdown")
```

**Templates:**

| Format | Target | Use Case |
|--------|--------|----------|
| Markdown | Chat display + CLI | Human-readable in terminal |
| HTML | Web chat | Rendered in Rasa X web UI |
| PDF | Download | Print/save for records |

**Report sections:**
1. Header (title, timestamp)
2. User details table
3. Eligibility status (✅/❌)
4. Grant amount
5. Passed/failed rules list
6. Missing requirements (if not eligible)
7. Next steps (actionable items)
8. Source links

**Output:** Returns filepath + content for bot to display

---

## Error Handling & Recovery

### Rule Scraper Errors

| Error Type | Handling |
|------------|----------|
| `FileNotFoundError` | Try scraping if URL available |
| `JSONDecodeError` | Log error, try to re-scrape |
| `NetworkError` | Wait and retry (up to 3 attempts) |
| `UnsupportedState` | Return None → bot says "State not supported" |

### Rule Interpreter Errors

| Error Type | Handling |
|------------|----------|
| Missing required rule | Log warning, skip check |
| Invalid user type | Treat as failure with descriptive message |
| All validations fail | Return NOT_ELIGIBLE with all missing items |

### Conversation Manager Errors

| Error Type | Handling |
|------------|----------|
| Invalid state input | Re-prompt with state list |
| Non-numeric income | "Please enter a number" |
| Ambiguous yes/no | Re-prompt "Please answer yes or no" |
| Exception during processing | Log error, restart conversation |

---

## Agent Communication Patterns

### Synchronous (Current)

All agents called in sequence within the same process:

```
ConversationManager.process_input()
  └─> RuleScraper.scrape_state_rules()  (blocking)
       └─> RuleInterpreter.validate_eligibility()  (blocking)
            └─> ReportGenerator.generate_report()  (blocking)
```

**Pros:** Simple, deterministic, easy to debug
**Cons:** Can't parallelize, blocks during network I/O

### Future: Asynchronous

For production, consider async implementation:

```python
async def process_eligibility_async(user_data):
    rules = await scraper.async_scrape(state)
    report = await interpreter.async_validate(user_data, rules)
    return await reporter.async_generate(report)
```

Or use a task queue (Celery/Redis) for long-running scrapes.

---

## Extensibility Guide

### Adding a New Validation Rule

1. **Define rule in `nsw_rules.json`** (or other state):
```json
{
  "rules": {
    "age_cap": 50  // New rule
  }
}
```

2. **Implement check in `RuleInterpreter`:**
```python
def _check_age_cap(self, user_data, rules_dict, report):
    age_cap = rules_dict.get("age_cap")
    if age_cap:
        user_age = user_data.get("age", 0)
        passed = user_age <= age_cap
        # Add ValidationResult...
```

3. **Add slot to Rasa domain** if collecting via form

4. **Update chatbot training** with age examples

### Adding a New State

1. Add URL in `RuleScraper.state_urls`
2. Implement `_scrape_<state>_rules()` method
3. Update `supported_states` list in `ConversationManager`
4. Add state abbreviation mapping in `_normalize_state()`
5. Create test cases in `sample_users.json`
6. Optionally, create `<state>_rules.json` for offline caching

---

## Logging & Observability

Each agent logs key events:

```python
# Rule Scraper
logger.info(f"Loaded rules for {state}")
logger.error(f"Failed to scrape rules: {e}")

# Rule Interpreter
logger.info(f"Eligibility check: {report.status.value}")
logger.debug(f"Rule '{name}' passed: {result.passed}")

# Conversation Manager
logger.debug(f"State transition: {old_state} → {new_state}")

# Report Generator
logger.info(f"Report saved to {filepath}")
```

All logs prefixed with agent name for filtering:
```
2024-01-01 12:00:00 - src.agents.rule_scraper - INFO - Loaded rules for NSW
2024-01-01 12:00:01 - src.agents.rule_interpreter - INFO - Eligibility check complete: eligible
```

---

## Configuration Management

All agent behavior controlled via environment variables:

| Variable | Agent Affected | Purpose |
|----------|----------------|---------|
| `SCRAPE_DELAY` | RuleScraper | Rate limiting |
| `RULE_CACHE_TTL` | RuleScraper | Cache freshness |
| `LOG_LEVEL` | All agents | Verbosity |
| `REPORT_OUTPUT_DIR` | ReportGenerator | Output location |

  Accessed via `src/utils/config.py` Config singleton.

---

## Security Considerations

### Path Validation

Both `RuleScraper` and `ReportGenerator` implement path traversal protection:

- `RuleScraper.__init__()` validates `data_path` to ensure it resolves within the project root using `Path.is_relative_to(project_root)`.
- `ReportGenerator.__init__()` validates `output_dir` to ensure it stays within `reports/` subfolder.
- Validation can be disabled for testing via `validate_paths=False` parameter.

### Input Validation

All user-provided data is validated before use:

- **Numeric inputs** — Checked for reasonable bounds (income ≤ $10M, price ≤ $50M) and positivity
- **State names** — Normalized to allowed set only (NSW, VIC, QLD, WA)
- **Text fields** — Sanitized to remove control characters and limit length (max 200 chars)

Validation happens at the edges:
- CLI argument parsing
- Conversation Manager handlers
- Any public API entry points

### Testing Exception

Unit tests often use temporary directories (`tmp_path` fixture) which lie outside the project root. To accommodate this, the validation is **disabled by default in tests** by passing `validate_paths=False` to agents.

**Important:** Never disable `validate_paths` in production.

---

## Agent Testing Strategy

### Unit Tests (per agent)

**Rule Scraper:**
- Test loading from cache
- Test scraping NSW rules
- Test invalid state handling
- Test cache clearing

**Rule Interpreter:**
- Test all validation rules individually
- Test eligible user passes all
- Test each failure mode
- Test edge cases (exactly at cap)

**Conversation Manager:**
- Test each state transition
- Test input validation/normalization
- Test restart functionality
- Test profile completeness check

**Report Generator:**
- Test Markdown output structure
- Test HTML rendering
- Test flagged outputs (eligible vs not)
- Test filename uniqueness

### Integration Tests

Full conversation flow using sample users:
```python
def test_full_eligibility_flow():
    manager = ConversationManager()
    # Simulate full conversation...
    # Assert final report is eligible
```

---

## Conclusion

This agent-based design enables:
- **Modularity:** Swap out one agent without touching others
- **Reusability:** Use RuleInterpreter independently for API
- **Testability:** Mock dependencies between agents
- **Scalability:** Each agent could be a microservice in future
- **Maintainability:** Clear separation, single responsibility

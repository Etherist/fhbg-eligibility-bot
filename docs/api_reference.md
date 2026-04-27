# API Reference

> **Note:** This reference covers both the **agent API** (for programmatic use) and the **Rasa chatbot API** (for HTTP integration).

---

## Agent API (Python)

### `RuleScraper`

The rule scraper agent provides programmatic access to grant rules.

```python
from src.agents.rule_scraper import RuleScraper

# Initialize
scraper = RuleScraper(
    data_path="src/data/",
    cache_ttl=86400,  # 24 hours
    scrape_delay=2.0
)

# Get rules (from cache or scrape)
rules = scraper.scrape_state_rules("NSW", force_refresh=False)

if rules:
    print(rules["grant_name"])  # "First Home Buyer Choice"
    print(rules["rules"]["income_cap"])  # 150000
```

**Methods:**

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `scrape_state_rules(state, force_refresh)` | `state: str`<br>`force_refresh: bool=False` | `Dict \| None` | Get rules for state, using cache if valid |
| `get_supported_states()` | None | `List[str]` | List of supported state abbreviations (NSW, VIC, QLD, WA) |
| `validate_state(state)` | `state: str` | `bool` | Check if state is supported |
| `clear_cache(state=None)` | `state: Optional[str]` | `bool` | Delete cached JSON files |

**Exceptions:** No exceptions thrown - returns `None` on failure.

---

### `RuleInterpreter`

Validates user data against grant rules and produces an eligibility report.

```python
from src.agents.rule_interpreter import RuleInterpreter, EligibilityReport

# Initialize with rules from scraper
interpreter = RuleInterpreter(rules)

# User data
user_data = {
    "state": "NSW",
    "income": 80000,
    "property_price": 700000,
    "first_home_buyer": True,
    "citizenship_status": "citizen",
    "will_reside": True,
}

# Validate
report: EligibilityReport = interpreter.validate_eligibility(user_data)

# Inspect results
if report.status.value == "eligible":
    print(f"Grant: ${report.grant_amount:,.0f}")
else:
    print(f"Missing: {report.missing_requirements}")
```

**Data Classes:**

```python
@dataclass
class EligibilityReport:
    status: EligibilityStatus          # ELIGIBLE or NOT_ELIGIBLE
    state: str                         # e.g., "NSW"
    grant_amount: float                # e.g., 10000.0
    grant_name: str                    # e.g., "First Home Buyer Choice"
    passed_rules: List[str]            # e.g., ["Income Cap", "Property Price Cap"]
    failed_rules: List[ValidationResult]  # Detailed failure info
    warnings: List[str]                # Non-blocking issues
    missing_requirements: List[str]    # User-friendly messages
    next_steps: List[str]              # Actionable advice
    sources: List[str]                 # URLs to official sources

@dataclass
class ValidationResult:
    rule_name: str
    passed: bool
    user_value: Any
    required_value: Any
    message: str                       # Failure explanation
```

**Methods:**

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `validate_eligibility(user_data)` | `user_data: Dict` | `EligibilityReport` | Run all validation checks |

---

### `ConversationManager`

Orchestrates multi-turn conversation flow.

```python
from src.agents.conversation_manager import ConversationManager

manager = ConversationManager()

# Initial greeting
print(manager.get_next_prompt())
# Output: "Hello! Which state are you buying in?"

# Process user input
response = manager.process_input("NSW")
print(response)
# Output: "What is your annual household income?"

# Continue...
manager.process_input("80000")
manager.process_input("700000")
# ...

# When complete
summary = manager.get_summary()
print(summary)
# {
#   "state": "processing",
#   "user_profile": { "state": "NSW", ... },
#   "eligibility_status": "eligible",
#   "grant_amount": 10000
# }
```

**Key Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `state` | `ConversationState` enum | Current stage in conversation |
| `user_profile` | `UserProfile` | Collected user data |
| `eligibility_report` | `EligibilityReport \| None` | Result after processing |

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_next_prompt()` | `str` | Bot's next question |
| `process_input(text)` | `str` | Process user message, return bot reply |
| `reset()` | `None` | Restart conversation from beginning |
| `get_summary()` | `Dict` | Current state snapshot |

**Conversation States (Enum):**

```python
ConversationState.START                  # Initial prompt
ConversationState.COLLECTING_STATE      # Asking state
ConversationState.COLLECTING_INCOME     # Asking income
ConversationState.COLLECTING_PROPERTY_PRICE  # Asking price
ConversationState.COLLECTING_FIRST_HOME # First home question
ConversationState.COLLECTING_CITIZENSHIP
ConversationState.COLLECTING_RESIDENCY
ConversationState.COLLECTING_PROPERTY_TYPE
ConversationState.PROCESSING            # Running eligibility check
ConversationState.COMPLETE              # Showing results
```

---

### `ReportGenerator`

Generates formatted eligibility reports.

```python
from src.agents.reporter import ReportGenerator, ReportConfig

config = ReportConfig(
    output_dir="reports/",
    format="markdown"  # or "html"
)
generator = ReportGenerator(config)

# Generate report
report_path = generator.generate_report(
    user_profile={
        "state": "NSW",
        "income": 80000,
        "property_price": 700000,
        "first_home_buyer": True,
    },
    eligibility_report=report,  # EligibilityReport object
    output_format="markdown"    # overrides config.format
)

print(f"Report saved to: {report_path}")
```

**Methods:**

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `generate_report(user_profile, eligibility_report, output_format)` | `Dict, EligibilityReport, Optional[str]` | `str` filepath | Generate and save report file |

**Supported Formats:**
- `"markdown"` → `.md` files
- `"html"` → `.html` files

**Helper Method:**

```python
summary_card = generator.generate_summary_card(user_profile, report)
print(summary_card)
# Returns compact HTML/Markdown card for chat display
```

---

## Rasa Action Server API

### Custom Actions

#### `ActionCheckEligibility`

**Name:** `action_check_eligibility`

**Triggers:** Form submission `eligibility_form`

**Input:** All form slots populated:
- `state`
- `income`
- `property_price`
- `first_home_buyer`
- `citizenship_status`
- `will_reside`
- `property_is_new` (optional)

**Side Effects:**
- Sets `eligibility_status` slot to `"eligible"` or `"not_eligible"`
- Sets `eligibility_report` slot (JSON string with full report data)
- Displays summary message to user

**Errors:** If any required slot missing → sets `eligibility_status` = `"incomplete"`

---

#### `ActionGenerateReport`

**Name:** `action_generate_report`

**Triggers:** Intent `request_report` or explicit user command

**Input:** `eligibility_report` slot must be populated

**Side Effects:**
- Saves Markdown report to `reports/` directory
- Sends report text in chat
- Provides file path

**Errors:** Reports "No eligibility data found" if slot empty

---

#### `ActionResetSlots`

**Name:** `action_reset_slots`

**Triggers:** Intent `restart`

**Effect:** Clears all slots, effectively resetting conversation

---

## Rasa Core Endpoints

### HTTP API (if running with `--enable-api`)

**Base URL:** `http://localhost:5005`

**Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/webhooks/rest/webhook` | POST | Send user message, get bot response |
| `/model` | GET | Get loaded model info |
| `/status` | GET | Server health check |

**Example cURL:**

```bash
curl -XPOST http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "test_user", "message": "hi"}'
```

**Response:**
```json
[
  {"recipient_id": "test_user", "text": "Hello! How can I help?"}
]
```

---

### Action Server Endpoint

**URL:** `http://localhost:5055/webhook`

**POST body:**
```json
{
  "next_action": "action_check_eligibility",
  "tracker": {
    "sender_id": "test_user",
    "slots": {
      "state": "NSW",
      "income": 80000,
      ...
    }
  },
  "domain": { ... }
}
```

**Response:**
```json
{
  "events": [
    {"event": "slot", "name": "eligibility_status", "value": "eligible"}
  ],
  "responses": [
    {"text": "✅ You are eligible..."}
  ]
}
```

*Note: Action server is normally only called by Rasa internally.*

---

## CLI Commands

### Main Entry Point

```bash
python src/chatbot/cli.py [OPTIONS] [COMMAND]
```

**Options:**
- `--log-level {DEBUG,INFO,WARNING,ERROR}` - Set logging verbosity

**Commands:**

#### Interactive Mode (default)

```bash
python src/chatbot/cli.py
```

Interactive prompt with typed input.

#### Quick Check

```bash
python src/chatbot/cli.py check \
  --state NSW \
  --income 80000 \
  --property-price 700000 \
  --first-home \
  --citizenship citizen \
  --will-reside
```

**Arguments:**

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--state` | `str` | Yes | State: NSW, VIC, QLD, WA |
| `--income` | `float` | Yes | Annual household income |
| `--property-price` | `float` | Yes | Purchase price |
| `--first-home` | flag | No | First home buyer (default: False) |
| `--citizenship` | `str` | No | Citizenship status (default: "citizen") |
| `--will-reside` | flag | No | Will live in property |
| `--is-new` | flag | No | New construction |

**Exit Codes:**
- `0` - Eligible
- `1` - Not eligible or error

---

### Agent Scripts

#### Rule Scraper CLI

```bash
python src/agents/rule_scraper.py NSW [OPTIONS]
```

**Options:**
- `--force` - Re-scrape even if cache valid
- `--output PATH` - Output file path (default: `src/data/nsw_rules.json`)
- `--clear-cache` - Delete cache instead of scraping

**Examples:**

```bash
# Scrape (or load cached) NSW rules
python src/agents/rule_scraper.py NSW

# Force refresh from government site
python src/agents/rule_scraper.py NSW --force

# Save to custom location
python src/agents/rule_scraper.py VIC --output custom_data/vic_rules.json

# Clear cache
python src/agents/rule_scraper.py NSW --clear-cache
```

#### Rule Interpreter CLI

```bash
python src/agents/rule_interpreter.py \
  --state NSW \
  --income 80000 \
  --property-price 700000 \
  --first-home
```

Same arguments as main CLI `check` command (delegates).

---

## Data Formats

### Rules JSON

Each state's rules are stored as:

```json
{
  "state": "NSW",
  "grant_name": "First Home Buyer Choice",
  "effective_date": "2024-01-01",
  "rules": {
    "income_cap": 150000,
    "property_price_cap": 1500000,
    "first_home_buyer_required": true,
    "citizenship_required": "australian_citizen_or_permanent_resident",
    "residency_requirement": "must_live_in_property_within_6_months",
    "new_construction_only": false,
    "grant_amount": 10000,
    "additional_benefits": ["stamp_duty_exemption", ...]
  },
  "sources": ["https://..."]
}
```

### User Profile JSON

```json
{
  "state": "NSW",
  "income": 80000,
  "property_price": 700000,
  "first_home_buyer": true,
  "citizenship_status": "citizen",
  "will_reside": true,
  "property_is_new": false
}
```

### Eligibility Report JSON (from slot)

```json
{
  "status": "eligible",
  "state": "NSW",
  "grant_amount": 10000,
  "grant_name": "First Home Buyer Choice",
  "passed_rules": ["Income Cap", "Property Price Cap", ...],
  "failed_rules": [],
  "missing_requirements": [],
  "next_steps": ["Apply online", "Gather documents", ...],
  "sources": ["https://revenue.nsw.gov.au/..."]
}
```

---

## Development API

### Adding a New Agent

1. Create `src/agents/your_agent.py`
2. Define class with clear `Input` and `Output` dataclasses
3. Add constructor args for any dependencies
4. Keep methods pure (no side effects unless intentional)
5. Add unit tests in `tests/test_your_agent.py`
6. Wire into `conversation_manager.py` or `actions.py`

### Writing Custom Actions

```python
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

class ActionMyFeature(Action):
    def name(self) -> Text:
        return "action_my_feature"

    async def run(self, dispatcher, tracker, domain):
        # Extract data
        slot_value = tracker.get_slot("my_slot")

        # Call agents
        result = my_agent.do_something(slot_value)

        # Set slots / send messages
        dispatcher.utter_message(text=f"Result: {result}")
        return [SlotSet("output_slot", result)]
```

Register in `src/chatbot/domain.yml`:
```yaml
actions:
  - action_my_feature
```

---

## Error Messages & UX

### CLI Errors

| Condition | Message |
|-----------|---------|
| Invalid state | "Please select a valid state: NSW, VIC, QLD, WA" |
| Non-numeric income | "Please enter a valid number" |
| No rules available | "Unable to load grant rules. Please try again." |
| All required fields not filled | "Missing required information: income, property_price" |

### Chatbot Errors

| Condition | Bot Response |
|-----------|--------------|
| Low NLU confidence | "I'm not sure I understood that. Could you rephrase?" |
| Network/scrape failure | "I'm having trouble loading the latest rules. Using cached data." |
| Unhandled exception | "An error occurred. Let's start over." |

---

## Performance Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Rule scrape time | < 5s | ~2.5s (with delay) |
| Eligibility check | < 1s | ~0.2s |
| Report generation | < 1s | ~0.1s (Markdown) |
| CLI startup | Instant | < 0.5s |
| Rasa model load | < 10s | ~5s |
| Total conversation | < 30s | ~20s |

---

## Future API Extensions

Potential future endpoints:

- **REST API** (`/api/check-eligibility` POST) - for web/mobile apps
- **WebSocket** - for real-time chat
- **Batch validation** - `/api/batch-check` with multiple profiles
- **Rule inspection** - `/api/rules/{state}` to fetch raw rules
- **Report download** - `/api/report/{id}` to get PDF

---

**This API reference will be expanded as the project grows.**

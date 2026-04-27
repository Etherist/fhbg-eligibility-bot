# Setup Instructions

## Prerequisites

- **Python** 3.10 or higher
- **pip** for package installation
- **Git** for cloning repository
- **Rasa** 3.6 (optional, for chatbot UI)

## Security Notes

This is a **demo project**. Before deploying to production, review [SECURITY.md](../SECURITY.md) for:

- Dependency upgrades (Rasa 3.6.0 is EOL)
- Authentication requirements
- Encryption at rest considerations
- Rate limiting and DoS protection

For local demo usage, no special security configuration is needed.

---

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/your-username/fhbg-eligibility-bot.git
cd fhbg-eligibility-bot
```

### 2. Create Virtual Environment

**macOS / Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Optional development dependencies:
```bash
pip install -r requirements.txt[dev]
```

### 4. Configure Environment (Optional)

```bash
cp .env.example .env
# Edit .env as needed
```

Defaults are fine for local demo.

---

## Quick Test

Run tests to verify installation:

```bash
pytest
```

Expected output:
```
============================== 48 passed in 2.34s ==============================
```

---

## Usage Modes

### Mode 1: Interactive CLI (Simplest)

```bash
python src/chatbot/cli.py
```

Follow prompts to enter:
1. State (NSW, VIC, QLD, WA)
2. Annual income
3. Property price
4. First home buyer? (yes/no)
5. Citizenship status
6. Will reside in property?

**Try it now with these values:**
```
State: NSW
Income: 80000
Property: 700000
First home? yes
Citizenship: citizen
Will reside? yes
```
Expected: ✅ Eligible for $10,000 grant

---

### Mode 2: Single Query

For scripts or integration:

```bash
python src/chatbot/cli.py check \
  --state NSW \
  --income 90000 \
  --property-price 750000 \
  --first-home \
  --citizenship citizen \
  --will-reside
```

Exit code `0` = eligible, `1` = not eligible.

---

### Mode 3: Rasa Chatbot (Web UI)

#### Step 1: Train Model

```bash
rasa train
```

This:
- Processes NLU training data (`nlu.yml`)
- Trains dialogue policies on `stories.yml` + `rules.yml`
- Generates model in `models/` directory

First run downloads required spaCy models automatically.

#### Step 2: Start Action Server

Open a terminal and run:

```bash
rasa run actions
```

This starts the custom action server on `http://localhost:5055`.

Leave this terminal open.

#### Step 3: Start Chatbot

Open a second terminal and run:

```bash
rasa shell
```

Now type messages to chat with the bot.

For **web interface**, run:

```bash
rasa run --enable-api --cors "*"
```

Then open [http://localhost:5005](http://localhost:5005) in browser.

---

### Mode 4: Jupyter Notebook

```bash
jupyter notebook notebooks/demo.ipynb
```

Run cells sequentially to see:
1. Agent initialization
2. Rule scraping
3. Eligibility checking (eligible & not eligible cases)
4. Full conversation simulation
5. Report generation
6. Batch test execution

---

## Updating Grant Rules

### Automatic (Demo)

Rules are automatically loaded from `src/data/nsw_rules.json`. Edit this file to modify values.

**Example: Change NSW property cap**
```json
{
  "rules": {
    "property_price_cap": 2000000  // Was 1500000
  }
}
```

Changes take effect immediately (no restart needed for CLI; for Rasa, you may need to retrain if slots change).

### Manual Scrape (Production)

If implementing live scraping:

```bash
python src/agents/rule_scraper.py NSW --force
```

This fetches latest from NSW Revenue website and updates cache.

**Note:** Demo currently uses static data. Web scraping code exists but returns hardcoded values.

---

## Configuration

Environment variables (in `.env` or shell):

| Variable | Default | Description |
|----------|---------|-------------|
| `SCRAPE_DELAY` | `2` | Seconds between web requests |
| `SCRAPE_TIMEOUT` | `30` | Request timeout in seconds |
| `RULE_CACHE_TTL` | `86400` | Cache expiry (24h) |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `NSW_RULES_PATH` | `src/data/nsw_rules.json` | NSW rules file location |
| `REPORT_OUTPUT_DIR` | `reports/` | Where to save reports |

---

## Troubleshooting

### FIX: Command Not Found

If `python` fails, try `python3`:
```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
python3 src/chatbot/cli.py
```

---

### FIX: Rasa Import Errors

Ensure you're in the activated virtual environment:
```bash
which rasa   # Should show path inside venv
```

If Rasa not installed:
```bash
pip install rasa==3.6.0
```

---

### FIX: ModuleNotFoundError

Make sure you're running from project root:
```bash
cd /path/to/fhbg-eligibility-bot
python src/chatbot/cli.py
```

---

### FIX: Port Already in Use

Action server or Rasa may be running. Stop with:

```bash
# Find process using port 5055 (action server) or 5005 (Rasa)
lsof -ti:5055 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :5055  # Windows

# Or use Ctrl+C in terminal where it's running
```

---

### FIX: Cache Corruption

Delete cached rules:
```bash
rm src/data/*_rules.json
```

Or use scraper clear:
```bash
python src/agents/rule_scraper.py NSW --clear-cache
```

---

## Uninstallation

To remove the demo from your system:

```bash
# Delete virtual environment
rm -rf venv/         # macOS/Linux
rd /s venv/          # Windows

# Optionally delete project folder
cd ..
rm -rf fhbg-eligibility-bot
```

---

## Getting Help

- **README.md** - Project overview and features
- **docs/architecture.md** - System design details
- **docs/agent_workflow.md** - Agent collaboration patterns
- **docs/api_reference.md** - Python API documentation
- **GitHub Issues** - [Open an issue](../../issues)

---

## Next Steps

After setup is complete:

1. ✅ Run `pytest` to verify tests pass
2. ✅ Try quick CLI check
3. ✅ Experiment with Rasa shell
4. ✅ Open demo notebook in Jupyter
5. ✅ Read architecture docs to understand internals
6. ✅ Try adding a new test case in `sample_users.json`

---

**Ready to demo?** Run:
```bash
python src/chatbot/cli.py
```

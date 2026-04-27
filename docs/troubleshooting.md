# Troubleshooting

Solutions to common issues encountered during development and deployment.

## Rasa Action Server Won't Start

**Symptom:**
```bash
$ rasa run actions
ModuleNotFoundError: No module named 'src.chatbot.actions'
```

**Cause:** Python path does not include the project root.

**Fix:**
- Run from the project root directory (where `src/` lives).
- Ensure `src/` contains an `__init__.py` (it does).
- Explicitly set PYTHONPATH:
  ```bash
  export PYTHONPATH=/path/to/project:$PYTHONPATH
  rasa run actions
  ```
- Alternatively, use Docker Compose which configures paths automatically:
  ```bash
  docker-compose up action-server
  ```

**Tip:** The action server expects the module path `src.chatbot.actions`. If you move files, update the command accordingly.

## Port 5005 Already in Use

**Symptom:**
```
OSError: [Errno 98] Address already in use
```

**Cause:** Another process (perhaps a previous Rasa instance) is already bound to port 5005.

**Fix (Linux/macOS):**
```bash
# Find and kill the process
lsof -ti:5005 | xargs kill -9

# Or use pkill
pkill -f "rasa run"
```

**Fix (Windows):**
```powershell
netstat -ano | findstr :5005
taskkill /PID <pid> /F
```

**Alternative:** Change the port:
```bash
rasa run --port 5006
# Update docker-compose.yml if using Docker
```

## CLI Reports "Invalid Financial Input"

**Symptom:**
```
ValueError: Income must be a positive number
```

**Cause:** The CLI expects raw numeric values; currency symbols or commas cause parsing errors.

**Fix:** Provide numbers without formatting:
```bash
# Correct
python src/chatbot/cli.py check --income 85000 --property-price 750000

# Incorrect (will fail)
python src/chatbot/cli.py check --income $85,000 --property-price $750,000
```

**Note:** The `check` command accepts floats as well: `--income 85000.50`.

## Eligibility Always False

**Symptom:** Every user profile results in NOT ELIGIBLE, even clearly eligible ones.

**Cause:** Rules file missing, malformed, or outdated.

**Fix:**
1. Verify the rules file exists:
   ```bash
   ls -la src/data/nsw_rules.json
   ```
2. If missing, re-run the scraper:
   ```bash
   python scripts/scrape_nsw_rules.py
   ```
3. If corrupted, delete and re-scrape:
   ```bash
   rm src/data/nsw_rules.json
   python scripts/scrape_nsw_rules.py
   ```
4. For a fresh cache, also clear Rasa's model cache:
   ```bash
   rm -rf .rasa/
   ```

**Tip:** Use the CLI's quick-check mode to isolate agent logic from Rasa:
```bash
python src/chatbot/cli.py check --state NSW --income 80000 --property-price 700000 --first-home
```

## Report Not Generated or Missing

**Symptom:** `Report generated: None` or file not found in `reports/`.

**Cause:** Reports directory not writable, or disk full.

**Fix:**
```bash
# Ensure directory exists
mkdir -p reports
chmod 755 reports  # Linux/macOS

# Check disk space
df -h

# Test manually
python -c "from agents.reporter import ReportGenerator; print(ReportGenerator().generate_report({}, {}))"
```

If using Docker, ensure volume mounts are correct and container has write permissions.

## Docker Containers Exit Immediately

**Symptom:**
```bash
$ docker-compose up
action-server_1  | exited with code 1
rasa_1          | exited with code 0
```

**Cause:** Missing dependencies or misconfigured paths.

**Debug:**
```bash
# View logs
docker-compose logs rasa
docker-compose logs action-server

# Common fixes:
docker-compose down -v  # Remove volumes
docker-compose build --no-cache  # Rebuild images
docker-compose up
```

**Checklist:**
- `requirements.txt` includes all needed packages (especially `rasa`, `rasa-sdk`, `beautifulsoup4`).
- No leftover host directory conflicts (e.g., a stale `__pycache__` with incompatible bytecode).
- On Windows, disable Docker Compose file line ending conversion (`git config core.autocrlf false`).

## Rasa Model Fails to Train

**Symptom:**
```bash
$ rasa train
... [E] Failed to train ...
```

**Cause:** Invalid training data (YAML syntax error), insufficient examples, or incompatible Rasa version.

**Fix:**
1. Validate YAML syntax:
   ```bash
   rasa data validate stories
   rasa data validate nlu
   ```
2. Ensure at least 10 examples per intent (recommended) in `nlu.yml`.
3. Check that `config.yml` uses valid components (no typos).
4. Delete old models and retrain:
   ```bash
   rm -rf models/
   rasa train
   ```
5. If using custom actions, ensure they import without errors:
   ```bash
   python -c "import src.chatbot.actions"
   ```

## Slow Response Times

**Symptom:** Bot takes >5 seconds to reply.

**Causes & Fixes:**
- **First-run model loading:** Rasa loads the NLU model on first request; subsequent responses are faster. Warm up the model with a test message.
- **Large rule set:** If you've added many states, scraping may be slow. Cache rules (24h TTL) or pre-warm the cache.
- **Network latency:** If scraping live government sites, network delays are inevitable (2s delay + fetch time). Use cached rules for development.
- **Docker overhead:** If running in Docker with synced volumes on Windows/macOS, file I/O can be slower. Use `:delegated` or `:cached` mount options.

**Profiling:** See `docs/performance.md` for detailed benchmarks and optimization tips.

## Tests Fail on Python 3.12

**Symptom:** Some tests error with `DeprecationWarning` or import errors.

**Cause:** Minor version-specific behavior.

**Fix:** Ensure all dependencies are up-to-date:
```bash
pip install --upgrade -r requirements.txt
```

If a specific test fails due to conditional imports, see `tests/conftest.py` for version-agnostic fixtures.

## "Restart" Command Not Working

**Symptom:** Typing "restart" does not reset the conversation.

**Cause:** The `restart` intent is only handled in the `COMPLETE` state by default.

**Fix:** The ConversationManager now handles a global `restart` command in all states (as of latest commit). If your version doesn't have this, pull the latest changes:
```bash
git pull origin main
```

Alternatively, use the Rasa `/restart` slash command if enabled:
```
/restart
```

## Cache Staleness

**Symptom:** New grant rules not reflected in eligibility checks.

**Cause:** Rule cache TTL is 24 hours. The scraper returns cached data if fresh.

**Force refresh:**
```bash
# Delete the cached file
rm src/data/nsw_rules.json

# Re-scrape
python scripts/scrape_nsw_rules.py
```

Or set environment variable to bypass cache temporarily:
```bash
export SCRAPE_FORCE_REFRESH=1
```

## Debug Mode

Enable verbose logging to diagnose issues:

**CLI:**
```bash
LOG_LEVEL=DEBUG python src/chatbot/cli.py
```

**Rasa shell:**
```bash
rasa shell --debug
```

**Action server:**
```bash
rasa run actions --log-level debug
```

**Docker:**
```bash
docker-compose logs -f action-server
```

Logs include stack traces, slot values (sanitized), and agent decisions.

## Clearing All State

To completely reset the project to a pristine state:

```bash
# Remove caches, reports, models
rm -rf reports/
rm -rf .rasa/
rm -rf models/
rm -f src/data/nsw_rules.json

# Remove virtual environment and reinstall
rm -rf venv/
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Reinitialize
pytest -v  # Verify
```

## Still Stuck?

If none of the above solutions work:

1. **Search existing issues** on GitHub (including closed ones).
2. **Create a new issue** with:
   - Environment details (OS, Python version, Rasa version)
   - Exact command you ran
   - Full error output (use code blocks)
   - Steps to reproduce
   - What you expected to happen

We'll respond within 2–3 business days.

---

*Last updated: 2026-04-27*

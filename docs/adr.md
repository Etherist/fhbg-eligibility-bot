# Architecture Decision Records (ADRs)

This document records significant architectural decisions made for the FHBG Eligibility Bot. Each ADR captures the context, decision, and consequences of a specific design choice.

## ADR-001: Agent-Based Architecture

**Status:** Accepted  
**Date:** 2026-04-27  
**Authors:** Project Team

### Context

We needed a modular system where eligibility checking logic is broken down into independent, testable units. A monolithic script would be hard to maintain, test, and extend.

### Decision

Adopt a four-agent system, each with a single responsibility:
1. **RuleScraper** — fetches and caches eligibility rules
2. **RuleInterpreter** — validates user data against rules
3. **ConversationManager** — manages dialogue state and agent coordination
4. **ReportGenerator** — formats results for output

Agents communicate through simple Python interfaces (no message broker).

### Consequences

**Positive:**
- Clear separation of concerns; each agent is isolated and easily unit-tested.
- Extensibility: new agents (e.g., PropertyLookupAgent) can be added without modifying existing ones.
- Ability to use agents independently (e.g., CLI bypasses ConversationManager).

**Negative:**
- Slightly more code overhead compared to a single function.
- Requires careful management of shared data structures (UserProfile).

---

## ADR-002: Rasa for Conversational AI

**Status:** Accepted  
**Date:** 2026-04-27

### Context

We require a robust dialogue management system capable of multi-turn conversations, entity extraction, and integration with custom actions. Options included building a custom state machine or adopting an existing framework.

### Decision

Use **Rasa 3.6** as the chatbot framework, leveraging its rule-based policies, form handling, and NLU pipeline.

### Consequences

**Positive:**
- Proven enterprise framework with large community and documentation.
- Built-in NLU reduces custom ML work; intent classification works out-of-the-box.
- Seamless integration with custom actions (our agents).
- Supports multiple channels (CLI, web, Slack, etc.) without extra code.

**Negative:**
- Heavy dependency (model size ~120MB).
- Rasa 3.6 is end-of-life (2022); future upgrade path needed (to 3.7+ or 4.x).
- Learning curve for contributors unfamiliar with Rasa.

---

## ADR-003: JSON File Storage vs Database

**Status:** Accepted  
**Date:** 2026-04-27

### Context

The bot needs to store grant rules and cached data persistently. Options were: relational DB (PostgreSQL), NoSQL (MongoDB), or flat files (JSON).

### Decision

Use **JSON files** for rules and cache. For a demo-focused project with small data volume (<100KB), JSON is simplest and requires zero external dependencies.

### Consequences

**Positive:**
- Human-readable and easily editable.
- Fast reads for small datasets.
- No database setup, migrations, or connection pooling.
- Ideal for offline/demo mode.

**Negative:**
- Not suitable for concurrent writes or very large rule sets.
- No built-in query capabilities; must load entire file into memory.
- Requires filesystem write permissions (mitigated by path validation).

**Future Reconsideration:** When scaling to multi-state or real-time updates, migrate to a lightweight embedded database (SQLite) or Redis for shared caching.

---

## ADR-004: Path Traversal Protection via `Path.is_relative_to()`

**Status:** Accepted  
**Date:** 2026-04-27

### Context

File operations (scraper cache, report generation) accept user-provided or constructed file paths. Malicious inputs like `../../../etc/passwd` could escalate to directory traversal attacks, exposing sensitive files or overwriting system files.

### Decision

Validate all file paths by checking: `Path.resolve().is_relative_to(project_root)`. Reject any path that resolves outside the allowed directory.

### Consequences

**Positive:**
- Robust, cross-platform protection against path traversal.
- Simple, one-line check in critical functions.
- Works in both agent code and CLI.

**Negative:**
- `Path.is_relative_to()` requires Python 3.9+, but project targets 3.10+ so this is fine.
- Adds a small performance cost (~µs) for path resolution; negligible.

---

## ADR-005: Separate Report Generator Agent

**Status:** Accepted  
**Date:** 2026-04-27

### Context

Eligibility results need to be presented in multiple formats (Markdown, HTML, optional PDF). The formatting logic could live in `ConversationManager` or `RuleInterpreter`, but that would violate single responsibility.

### Decision

Create a dedicated **ReportGenerator** agent responsible solely for formatting and file output. `ConversationManager` delegates report generation to this agent after validation completes.

### Consequences

**Positive:**
- Single responsibility principle preserved.
- Easy to add new output formats (e.g., plain text, JSON) without touching business logic.
- Templates can be swapped or themed independently.
- Report generation can be mocked in tests.

**Negative:**
- Adds another component to the system (minor complexity increase).

---

## ADR-006: CLI as Primary Development Interface

**Status:** Accepted  
**Date:** 2026-04-27

### Context

During development, we needed a fast way to test eligibility logic without starting the Rasa server (which adds overhead ~2–3 seconds for model loading).

### Decision

Build a standalone CLI (`src/chatbot/cli.py`) that directly invokes agents in sequence: scrape → validate → report. Used for rapid iteration and as a demo fallback when Rasa is unavailable.

### Consequences

**Positive:**
- Instant feedback loop (<1s per check).
- Tests agent decoupling (agents work without Rasa).
- Provides an alternative interface for headless environments.
- Serves as a reference implementation for how to use the agents programmatically.

**Negative:**
- Duplicate input validation logic? No, shared via `helpers.validate_financial_input`.
- Must maintain CLI documentation separately (done in README).

---

## ADR-007: Rule Caching with 24-Hour TTL

**Status:** Accepted  
**Date:** 2026-04-27

### Context

Scraping government websites on every eligibility check would be slow and could violate rate limits. Rules rarely change (typically once per year).

### Decision

Cache scraped rules to `src/data/nsw_rules.json` with a 24-hour time-to-live. Subsequent requests within the TTL use the cached file; scraping only occurs when cache is stale or missing.

### Consequences

**Positive:**
- Dramatically improves response time for cached rules (<0.1s vs ~3s).
- Reduces load on government servers; respects rate limits.
- Enables offline/demo mode.

**Negative:**
- Users may get stale data if rules change and cache hasn't expired.
- Invalidation strategy is simple TTL; could be improved with ETag/Last-Modified headers.

---

## ADR-008: Global "Restart" Command via State Machine

**Status:** Accepted  
**Date:** 2026-04-27

### Context**

During multi-turn conversations, users may want to reset at any point. The original restart handler only worked in the COMPLETE state.

**Decision**

Move the `restart` command handling to the earliest possible point in `ConversationManager.process_input()`, before state-specific logic. This ensures global availability regardless of current state.

**Consequences**

**Positive:**
- Consistent user experience; "restart" always works.
- Simplifies UX testing and reduces user frustration.

**Negative:**
- Slightly more branching in `process_input()`; mitigated by early return pattern.

---

*More ADRs will be added as the project evolves. To propose an ADR, open an issue with the label `architecture`.*

# Kilo Agent Commands for FHBG Eligibility Bot

This directory contains Kilo agent definitions for the FHBG Eligibility Bot project.

## Available Agents

### `/local-review`

Use this command to perform a local code review on the current project state:

```
/local-review
```

This will trigger a comprehensive review of:
- Code quality and style
- Architecture consistency
- Test coverage
- Documentation completeness

### `/local-review-uncommitted`

Use to review only uncommitted changes:

```
/local-review-uncommitted
```

## Configuration

Project-specific Kilo settings are defined in `kilo.json` at the project root.

## Workspace Context

This project is located at:
- Project root: `/home/aetherist/projects/llm_engineering/fhbg-eligibility-bot/`
- Git repo: Yes
- Platform: Linux

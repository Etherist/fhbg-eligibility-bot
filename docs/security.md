# Security Policy

## Supported Versions

| Version | Supported | EOL |
|---------|-----------|-----|
| 0.1.x   | ✅ Yes    | TBD |

## Reporting a Vulnerability

We take security seriously. If you discover a vulnerability, please report it responsibly.

**Please do not** open a public GitHub issue for security vulnerabilities.

### How to Report

1. **Email**: Send details to `security@fhbg-bot.example.com` (replace with actual)
2. **GitHub**: Open a private security advisory via [GitHub's Private Vulnerability Reporting](https://github.com/your-username/fhbg-eligibility-bot/security/advisories)
3. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

**Response time:** We aim to respond within 48 hours and provide a fix timeline within 7 days.

## Security Features

### Input Validation
- All financial inputs (income, property price) validated for ranges:
  - Income: $0 to $10,000,000
  - Property price: $0 to $50,000,000
- State names normalized against allowed list only (NSW, VIC, QLD, WA)
- Text inputs sanitized to strip control characters and limit length

### Path Traversal Protection
- `RuleScraper.data_path` validated to be within project root using `Path.is_relative_to()`
- `ReportGenerator.output_dir` restricted to `reports/` subfolder only
- Validation can be disabled for testing via `validate_paths=False` parameter

### Secrets Management
- No hardcoded credentials
- `.env` file gitignicked (never commit secrets)
- Environment variables used for configuration

### Logging
- No personally identifiable information (PII) logged
- Only aggregated metrics (counts, status codes)
- Full stack traces only at DEBUG level (not in production)

### Rate Limiting
- Polite delays (2s) between web scrapes
- Caching (24h TTL) reduces external calls
- No hard rate limits (demo only)

## Known Limitations (Demo)

### Insecure Dependencies
- **Rasa 3.6.0** is beyond end-of-life (2022). Known CVEs may exist.
  - Recommendation: Upgrade to Rasa 3.7+ or 4.x for production.
- Dependency versions pinned to major.minor only. Recommend pinning to exact versions (`==`) and using `pip-compile` or `poetry` for production.

### No Authentication
- CLI and chatbot have no user authentication.
- Anyone with access can run eligibility checks.
- For production, add JWT or session-based auth.

### No Encryption at Rest
- Reports saved as plain text (Markdown/HTML). No encryption.
- Cache files (JSON) are plain text.
- Production should encrypt sensitive data at rest.

### No CSRF Protection
- If deployed as web app, CSRF tokens not implemented.
- Use Rasa X or similar that includes CSRF protection.

### Dependency Scanning
- CI does not include `safety check` or `dependabot`.
- Recommend adding:
  ```yaml
  - name: Safety check
    run: pip install safety && safety check --full-report
  ```

## Security Best Practices for Deployers

### Production Deployment
1. **Run as non-root user** in Docker/VM
2. **Enable HTTPS** on all endpoints (let's encrypt)
3. **Set LOG_LEVEL=WARNING** or higher to reduce log noise
4. **Configure firewall** to restrict access to required ports only
5. **Use read-only filesystem** for application code; mount `reports/` as writable volume
6. **Regular updates**: `pip install -r requirements.txt --upgrade`
7. **Monitor logs** for unusual patterns (repeated errors, strange inputs)

### Docker Security
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
USER 1000:1000  # non-root
CMD ["python", "src/chatbot/cli.py"]
```

### OS Hardening
- Keep OS updated
- Use SELinux/AppArmor profiles to restrict file access
- Audit file permissions: `reports/` and `src/data/` should be writable only by app user

## Threat Model

| Threat Actor | Goal | Mitigation |
|--------------|------|------------|
| External attacker | Read sensitive data from reports | Reports contain no PII (only eligibility data). No action needed. |
| Malicious user | Path traversal to read `/etc/passwd` | Prevented by `is_relative_to` checks in `RuleScraper` & `ReportGenerator`. |
| Network attacker | Man-in-the-middle on scraping | HTTPS enforced in `requests`. Add certificate pinning for production. |
| Compromised dependency | Supply chain attack | Pin exact versions, use `pip-compile`, `safety check`, Dependabot. |
| Insider threat | Modify rules JSON to influence outcomes | Git versioning + code review. Sign commits with GPG. |
| DoS attacker | Flood bot with requests | Rate limiting at reverse proxy (nginx) or load balancer. |

## Responsible Disclosure Timeline

1. **Report received** → Acknowledge within 48 hours.
2. **Triage** → Assess severity (Critical/High/Medium/Low) within 7 days.
3. **Fix development** → Create private fork, develop patch.
4. **Coordinated disclosure** → Notify reporter, schedule public advisory.
5. **Public release** → Security advisory published, patch released.

## Past Security Issues

None reported to date.

## References

- [OWASP Top 10](https://owasp.org/Top10/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [Rasa Security Guidelines](https://rasa.com/docs/rasa/security/)

---

*Last updated: 2026-04-27*

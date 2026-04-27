# Performance & Scalability

This document outlines performance characteristics, benchmarking results, and scalability pathways for the FHBG Eligibility Bot.

## Benchmarks (Local Development Environment)

Tests conducted on Python 3.12, Intel i7-12700H, 16 GB RAM, NVMe SSD.

| Operation | Typical Latency | Percentile (p95) | Notes |
|-----------|----------------|------------------|-------|
| CLI eligibility check (single) | 0.3 s | 0.5 s | Pure Python, no model loading |
| CLI eligibility check (with report) | 0.5 s | 0.8 s | Includes Markdown generation |
| Rasa intent classification (warm) | 0.4 s | 0.7 s | After model is loaded |
| Rasa first request (cold start) | 2.8 s | 3.5 s | Includes model load |
| Action server response (simple) | 0.1 s | 0.2 s | `ActionCheckEligibility` with cached rules |
| Rule scrape (network, first) | 2.8 s | 3.2 s | Plus 2s artificial delay |
| Rule scrape (cached) | 0.05 s | 0.1 s | Local JSON read |
| Report generation (Markdown) | 0.15 s | 0.25 s | Jinja2 template render |
| Report generation (HTML) | 0.2 s | 0.3 s | Additional HTML escaping |
| Report generation (PDF) | 0.8 s | 1.2 s | WeasyPrint rendering (if installed) |

## Memory Footprint

| Component | Resident Memory | Notes |
|-----------|----------------|-------|
| Python CLI process | 35 MB | No Rasa model loaded |
| Rasa server (with model) | 145 MB | DIET + transformers pipeline |
| Action server | 45 MB | Agents + dependencies |
| Combined (docker-compose) | ~210 MB | Two containers, shared libraries |
| Jupyter notebook kernel | 55 MB | With agents loaded |

*Memory measured via `psutil.Process().memory_info().rss / 1024**2`.*

## Scalability Considerations

### Current Architecture Limits

| Dimension | Current State | Production Requirement |
|-----------|---------------|-----------------------|
| **State persistence** | In-memory (Rasa `InMemoryTrackerStore`) | External store (Redis/PostgreSQL) |
| **Concurrency** | Single-threaded action server; Rasa handles async requests | Horizontal scaling via multiple containers + load balancer |
| **Data storage** | JSON files on local disk | Object storage (S3) + database for user data |
| **Rule distribution** | Local cache only | CDN or shared cache (Redis) |
| **Traffic volume** | Single user demo | Hundreds of concurrent conversations |

### Production Scaling Roadmap

#### Tier 1: Multi-Instance Deployment (1–10 RPS)
- Deploy Rasa and action server behind an NGINX reverse proxy.
- Use `RedisTrackerStore` to share conversation state across instances.
- Store cached rules in Redis (key: `rules:{state}`, TTL 24h).
- Expected cost: $10–$30/month on a small VPS.

#### Tier 2: High Availability (10–100 RPS)
- Container orchestration with Kubernetes or Docker Swarm.
- Horizontal pod autoscaling based on CPU/memory.
- Managed PostgreSQL (e.g., AWS RDS) for tracker store and user profiles.
- Cloud storage (S3) for generated reports.
- Expected cost: $100–$300/month.

#### Tier 3: Enterprise Scale (100+ RPS)
- Dedicated Rasa X / Rasa Pro deployment with enterprise features.
- AI model serving via Triton Inference Server or Seldon Core.
- Microservices split: scraper service, interpreter service, report service.
- Event-driven architecture with message queue (RabbitMQ/Kafka).
- Expected cost: $500+/month.

## Load Testing Recommendations

**Tools:**
- [Locust](https://locust.io/) — Python-based, easy to script user flows.
- [k6](https://k6.io/) — JavaScript-based, high performance.
- [Artillery](https://www.artillery.io/) — Node.js, good for API testing.

**Scenario: Simulate 100 concurrent users asking about grant eligibility.**
```yaml
# example locustfile.py
from locust import HttpUser, task, between

class BotUser(HttpUser):
    wait_time = between(2, 5)

    @task
    def check_eligibility(self):
        self.client.post("/webhooks/rest/webhook", json={
            "sender": "test_user",
            "message": "I want to check eligibility for NSW"
        })
```

**Metrics to collect:**
- Request latency (p50, p95, p99)
- Throughput (requests/sec)
- Error rate (5xx responses)
- Resource utilization (CPU, memory, I/O)

## Profiling

### CPU Profiling
```bash
# Profile the CLI check
python -m cProfile -o profile.stats src/chatbot/cli.py check \
  --state NSW --income 80000 --property-price 700000 --first-home

# Visualize
pip install snakeviz
snakeviz profile.stats
```

### Memory Profiling
```bash
pip install memory-profiler
python -m memory_profiler src/chatbot/cli.py check \
  --state NSW --income 80000 --property-price 700000
```

### Rasa-specific profiling
Enable Rasa's built-in profiling:
```bash
rasa shell --debug --endpoints endpoints.yml
# Logs include timing for NLU, policy prediction, and action execution.
```

## Optimization Opportunities

| Area | Current | Optimized | Impact |
|------|---------|-----------|--------|
| **NLU model** | Transformers (BERT) | spaCy + Huffman encoder (smaller) | -60% memory, +30% speed |
| **Rule caching** | File-based JSON | Redis (in-memory) | -90% read latency |
| **Template rendering** | Jinja2 per request | Pre-compiled + cached templates | -20% render time |
| **Report I/O** | Synchronous write | Async background worker | Non-blocking for user |
| **Action server** | Single-threaded | Uvicorn with multiple workers | 2–4x throughput |
| **Tracker store** | In-memory | PostgreSQL + connection pooling | Persistence + scalability |

## Bottleneck Analysis

Typical request path:
1. User sends message → Rasa receives (50 ms)
2. NLU processing (400 ms)
3. Policy prediction (100 ms)
4. Action server call over HTTP (10 ms network + 100 ms processing)
5. Response assembled (50 ms)
6. Total: ~700 ms (warm)

**Dominant cost:** NLU model inference (~60% of total).

**Mitigation:** Use smaller model (e.g., `masked-language-model` with fewer layers) or enable GPU acceleration in production.

## Future Performance Work

- [ ] Benchmark across Python versions (3.10 vs 3.11 vs 3.12)
- [ ] Load test with 100+ concurrent users (Locust)
- [ ] Memory leak detection over 24h continuous operation
- [ ] Cold-start optimization: pre-warm model on deployment
- [ ] Benchmark PDF generation with large datasets
- [ ] Compare Rasa 3.6 vs 4.x performance

---

*Document version: 0.1.0 | Last updated: 2026-04-27*

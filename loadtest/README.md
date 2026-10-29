# Performance and security tests

| File | Test cases | How to run |
|---|---|---|
| `locustfile.py` | TC-43 (NFR-01): 20 users, 5 minutes, p95 ≤ 2 s | `locust -f loadtest/locustfile.py --headless -u 20 -r 5 -t 5m --host https://localhost:8443 --csv loadtest/results/tc43 --html loadtest/results/tc43.html` |
| `security_checks.py` | TC-34, TC-35, TC-36, TC-38, TC-39 against a running deployment | `python3 loadtest/security_checks.py https://localhost:8443` |
| `results/` | Locust report and CSVs from the Sprint 2 run on Kubernetes | open `results/tc43.html` |

Results are recorded in [docs/TEST_LOG.md](../docs/TEST_LOG.md).

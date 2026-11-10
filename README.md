# Backend Engineering Portfolio

[![Tests](https://github.com/yazanus94-dot/backend-engineering-portfolio/actions/workflows/ci.yml/badge.svg)](https://github.com/yazanus94-dot/backend-engineering-portfolio/actions/workflows/ci.yml)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![Java 21](https://img.shields.io/badge/java-21-orange)
![Node 20+](https://img.shields.io/badge/node-20%2B-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

Five senior-level backend engineering projects across **Python, Java, and TypeScript** —
each one built around a skill interviewers actually probe: API design, algorithmic depth,
performance work on inherited code, concurrency/TTL semantics in a stateful service, and
traffic-gating middleware. Every README explains the *why*, every claim is backed by tests
or benchmarks, and CI runs all five on every push.

| # | Project | Language | Demonstrates | Headline |
|---|---------|----------|--------------|----------|
| 1 | [task-api-python](senior_swe_proj1_task_api_python/) | Python/Flask | Realistic REST API design: CRUD, defensive input validation, structured error responses, filtering + pagination | 22 unit tests incl. validation and error-shape contracts |
| 2 | [algorithms-python](senior_swe_proj2_algorithms_python/) | Python | LRU cache, graph algorithms (BFS/DFS/topo/Dijkstra), sorting — implemented from scratch, no stdlib shortcuts | Benchmarks compare real runtimes against theoretical complexity |
| 3 | [refactor-perf-python](senior_swe_proj3_refactor_perf_python/) | Python | Inherited-code work: reproduce real bugs in tests, fix without regressions, optimize with evidence | Duplicate detection **up to 326x faster** after refactor |
| 4 | [kv-store-java](senior_swe_proj4_kv_store_java/) | Java 21 | Thread-safe, TTL-aware in-memory KV store behind a built-in-JDK HTTP server (no Spring by design) | 25 tests covering concurrency + TTL expiry + HTTP layer |
| 5 | [rate-limiter-typescript](senior_swe_proj5_rate_limiter_typescript/) | TypeScript | **Token bucket** and **sliding window log** from scratch, wired as real HTTP middleware | 18 unit + HTTP integration tests against the live server |

## Running the test matrix locally

```bash
# Python projects (1-3): each is standalone, tests are unittest-discoverable
python -m unittest discover -s senior_swe_proj1_task_api_python/tests -t senior_swe_proj1_task_api_python
python -m unittest discover -s senior_swe_proj2_algorithms_python/tests -t senior_swe_proj2_algorithms_python
python -m unittest discover -s senior_swe_proj3_refactor_perf_python/tests -t senior_swe_proj3_refactor_perf_python

# Java project (4): JDK + bundled JUnit jars, zero network needed
bash senior_swe_proj4_kv_store_java/build_and_test.sh

# TypeScript project (5): needs npm
cd senior_swe_proj5_rate_limiter_typescript && npm install && npm test && npm run typecheck
```

CI (`.github/workflows/ci.yml`) runs: Python projects on 3.11/3.12/3.13 (plus benchmark
sweeps), the Java JUnit suite on Temurin 21, and the TypeScript suite + typecheck on Node 20/22.

## Selection rationale

Projects 2–3 intentionally cover both sides of algorithmic engineering: writing data
structures from scratch (2), and the messier day-to-day reality of inheriting buggy, slow code
and fixing it *with proof* (3, which keeps regression tests that reproduce each legacy bug).
Project 4 deliberately avoids Spring to show raw JDK concurrency and socket-level work;
project 5 exists because rate limiting is the classic mid-level backend interview problem,
implemented here as production-shaped middleware rather than a toy loop.

## License

MIT, see [LICENSE](LICENSE).

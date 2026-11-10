# API Rate Limiter (TypeScript)

Personal portfolio project: two production-grade rate-limiting
algorithms — **token bucket** and **sliding window log** — implemented
from scratch in TypeScript, wired into a working HTTP API as real
request-gating middleware, with unit tests for both algorithms and
integration tests against the live HTTP server.

## Why this project

Rate limiting is a common, concrete backend engineering problem that
exercises several things at once: correct concurrent state management,
precise handling of time, awareness of known algorithmic pitfalls (the
fixed-window boundary-burst bug, specifically avoided here), and the
discipline to make time-dependent code actually testable.

## Why no Express

Built and verified in an offline environment with no internet access to
install external framework dependencies, so the HTTP layer uses Node's
built-in `http` module instead of Express — zero external runtime
dependencies. This is disclosed deliberately: in a normal environment,
Express (or Fastify) would be the practical choice for a real production
service, and this project doesn't claim otherwise. The rate-limiting
algorithms themselves are the point, and they're framework-agnostic —
the same `TokenBucketRateLimiter`/`SlidingWindowRateLimiter` classes
would plug into an Express middleware unchanged.

## What's included

- **`tokenBucket.ts`** — Token Bucket limiter: allows bursts up to a
  configured capacity, then refills at a steady rate (the algorithm used
  by API gateways like AWS API Gateway for its burst tolerance).
- **`slidingWindow.ts`** — Sliding Window Log limiter: tracks exact
  per-client request timestamps within a rolling window for precise rate
  enforcement, explicitly avoiding the well-known fixed-window bug where
  up to 2x the limit can slip through right at a window boundary.
- **`server.ts`** — a minimal HTTP server using `SlidingWindowRateLimiter`
  as real request-gating middleware (`GET /api/data`, rate-limited per
  `x-client-id`; `GET /health`, unthrottled).
- **Tests** (`node:test`, run via `tsx`):
  - `tokenBucket.test.ts` / `slidingWindow.test.ts` — unit tests using an
    injectable fake clock, so refill/expiry timing is deterministic
    instead of relying on real `sleep()` calls (a common source of flaky
    tests in time-based code).
  - `server.test.ts` — integration tests that start the real HTTP server
    on an ephemeral port and verify rate-limiting behavior, per-client
    isolation, and status codes over actual HTTP requests — not just
    testing the algorithm in isolation.

Both limiter classes validate constructor arguments and throw on invalid
input (non-positive capacity/rate/window), and the sliding-window tests
specifically include a regression test for the fixed-window boundary-burst
failure mode this implementation was designed to avoid.

## Run it

```bash
npm install          # only needed for optional devDependencies if you add any;
                      # tsx and typescript are expected to be available globally
                      # or already present, see package.json scripts
npm test              # runs all *.test.ts files via tsx + node:test
npm run typecheck     # tsc --noEmit
npm start              # starts the demo HTTP server on port 3000
```

Manual check once the server is running:

```bash
curl http://localhost:3000/health
curl -H "x-client-id: demo" http://localhost:3000/api/data   # repeat 6x to see the 429
```

## Project structure

```
ts_rate_limiter/
├── README.md
├── package.json
├── tsconfig.json
└── src/
    ├── tokenBucket.ts
    ├── tokenBucket.test.ts
    ├── slidingWindow.ts
    ├── slidingWindow.test.ts
    ├── server.ts
    └── server.test.ts
```

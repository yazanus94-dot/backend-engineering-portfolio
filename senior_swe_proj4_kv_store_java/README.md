# In-Memory Key-Value Store — Backend Service (Java)

Personal portfolio project: a small backend service — a thread-safe,
TTL-aware in-memory key-value store exposed over a REST-style HTTP API —
built and tested with the JDK standard library only.

## Why this project, and why no Spring Boot

This was built and verified in an offline environment with no internet
access to pull Maven/Gradle dependencies, so instead of Spring Boot it
uses the JDK's built-in `com.sun.net.httpserver` for the HTTP layer and
`java.net.http.HttpClient` for integration testing — both ship with the
JDK, zero external dependencies. This is disclosed here deliberately: in
a normal environment, Spring Boot (or a similar framework) would be the
practical choice for a real production service, and this project doesn't
claim otherwise. What it does demonstrate is understanding of what such
a framework provides under the hood — routing, request/response
handling, status codes, structured error responses, concurrency — by
building it directly.

## What it does

- **`KVStore`** — thread-safe (`ConcurrentHashMap`-backed) store with
  `put`, `get`, `delete`, and `putWithTtl` (per-key expiration). Takes a
  `java.time.Clock` as a constructor dependency specifically so TTL
  expiry can be tested deterministically (a `MutableClock` in the test
  suite advances time without real sleeps) rather than relying on
  flaky `Thread.sleep`-based tests.
- **`KVHttpServer`** — REST-style HTTP front end:
  - `GET /health`
  - `GET /kv/{key}`
  - `PUT /kv/{key}?ttl={seconds}` (body = value; `ttl` optional)
  - `DELETE /kv/{key}`

  Returns proper status codes (200/204/400/404/405/500) and structured
  JSON error bodies.

## Tests — 25 total, two layers

- **`KVStoreTest`** (17 tests) — unit tests on the store logic directly:
  CRUD correctness, null/empty-key/negative-TTL validation, TTL expiry
  at/before/after the boundary (including an exact-boundary edge case),
  `purgeExpired`, and overwriting an expired key.
- **`KVHttpServerTest`** (8 tests) — integration tests that start a real
  server on an OS-assigned free port and make real HTTP requests against
  it with `HttpClient`: round-trip PUT/GET, 404s, DELETE, invalid TTL
  parameter handling, and one real-wall-clock TTL-expiry test over HTTP
  (deliberately using a real `Thread.sleep` here, since this test is
  specifically verifying real-time behavior end-to-end — the
  deterministic clock-based TTL logic itself is already covered in
  `KVStoreTest`).

## Build & run

Requires only a JDK (built with OpenJDK 21). JUnit 4 + Hamcrest jars are
vendored in `lib/` so the test suite runs without needing network access
to a Maven repository.

```bash
# compile
javac -d build/classes src/main/java/com/yazan/kvstore/*.java
javac -cp "build/classes:lib/junit-4.13.2.jar:lib/hamcrest-core-1.3.jar" \
      -d build/test-classes src/test/java/com/yazan/kvstore/*.java

# run tests
java -cp "build/classes:build/test-classes:lib/junit-4.13.2.jar:lib/hamcrest-core-1.3.jar" \
     org.junit.runner.JUnitCore com.yazan.kvstore.KVStoreTest com.yazan.kvstore.KVHttpServerTest

# run the server (port 8080 by default)
java -cp build/classes com.yazan.kvstore.KVHttpServer
```

Or just run `./build_and_test.sh`, which does all of the above.

## Project structure

```
java_kv_store/
├── README.md
├── build_and_test.sh
├── lib/                              # vendored JUnit4 + Hamcrest jars
├── src/main/java/com/yazan/kvstore/
│   ├── KVStore.java                  # thread-safe store + TTL logic
│   └── KVHttpServer.java             # HTTP routing + REST endpoints
└── src/test/java/com/yazan/kvstore/
    ├── MutableClock.java             # test-only advanceable clock
    ├── KVStoreTest.java              # 17 unit tests
    └── KVHttpServerTest.java         # 8 integration tests (real HTTP)
```

import test from "node:test";
import assert from "node:assert/strict";
import { TokenBucketRateLimiter } from "./tokenBucket";

/** Controllable fake clock: starts at `startMs`, advanced manually by
 *  tests, so TTL/refill timing is deterministic instead of relying on
 *  real sleeps. */
function makeFakeClock(startMs: number) {
  let current = startMs;
  const now = () => current;
  const advance = (ms: number) => {
    current += ms;
  };
  return { now, advance };
}

test("allows requests up to capacity, then rejects", () => {
  const clock = makeFakeClock(0);
  const limiter = new TokenBucketRateLimiter({ capacity: 3, refillRatePerSecond: 1, now: clock.now });

  assert.equal(limiter.tryConsume(), true);
  assert.equal(limiter.tryConsume(), true);
  assert.equal(limiter.tryConsume(), true);
  assert.equal(limiter.tryConsume(), false); // capacity exhausted
});

test("refills tokens over time at the configured rate", () => {
  const clock = makeFakeClock(0);
  const limiter = new TokenBucketRateLimiter({ capacity: 2, refillRatePerSecond: 1, now: clock.now });

  assert.equal(limiter.tryConsume(), true);
  assert.equal(limiter.tryConsume(), true);
  assert.equal(limiter.tryConsume(), false);

  clock.advance(1000); // 1 second -> 1 token refilled
  assert.equal(limiter.tryConsume(), true);
  assert.equal(limiter.tryConsume(), false);
});

test("refill never exceeds capacity even after a long idle period", () => {
  const clock = makeFakeClock(0);
  const limiter = new TokenBucketRateLimiter({ capacity: 5, refillRatePerSecond: 2, now: clock.now });

  clock.advance(100_000); // huge gap
  assert.equal(limiter.availableTokens(), 5); // capped at capacity, not overflowed
});

test("tryConsume with cost > 1 draws multiple tokens at once", () => {
  const clock = makeFakeClock(0);
  const limiter = new TokenBucketRateLimiter({ capacity: 10, refillRatePerSecond: 1, now: clock.now });

  assert.equal(limiter.tryConsume(5), true);
  assert.equal(limiter.availableTokens(), 5);
  assert.equal(limiter.tryConsume(6), false); // not enough left
  assert.equal(limiter.availableTokens(), 5); // unchanged on rejection
});

test("partial refill between requests is fractional, not rounded", () => {
  const clock = makeFakeClock(0);
  const limiter = new TokenBucketRateLimiter({ capacity: 10, refillRatePerSecond: 2, now: clock.now });

  limiter.tryConsume(10); // drain to 0
  clock.advance(250); // 0.25s * 2 tokens/s = 0.5 tokens
  assert.equal(limiter.availableTokens(), 0.5);
});

test("rejects non-positive capacity and refill rate in constructor", () => {
  assert.throws(() => new TokenBucketRateLimiter({ capacity: 0, refillRatePerSecond: 1 }));
  assert.throws(() => new TokenBucketRateLimiter({ capacity: 1, refillRatePerSecond: 0 }));
  assert.throws(() => new TokenBucketRateLimiter({ capacity: -1, refillRatePerSecond: 1 }));
});

test("rejects non-positive cost in tryConsume", () => {
  const limiter = new TokenBucketRateLimiter({ capacity: 5, refillRatePerSecond: 1 });
  assert.throws(() => limiter.tryConsume(0));
  assert.throws(() => limiter.tryConsume(-1));
});

import test from "node:test";
import assert from "node:assert/strict";
import { SlidingWindowRateLimiter } from "./slidingWindow";

function makeFakeClock(startMs: number) {
  let current = startMs;
  const now = () => current;
  const advance = (ms: number) => {
    current += ms;
  };
  return { now, advance };
}

test("allows up to maxRequests within the window, then rejects", () => {
  const clock = makeFakeClock(0);
  const limiter = new SlidingWindowRateLimiter({ maxRequests: 3, windowSeconds: 10, now: clock.now });

  assert.equal(limiter.allow("client-a"), true);
  assert.equal(limiter.allow("client-a"), true);
  assert.equal(limiter.allow("client-a"), true);
  assert.equal(limiter.allow("client-a"), false);
});

test("does not allow bursting past the limit at a window boundary (fixed-window bug this avoids)", () => {
  // This is the classic failure mode of a *fixed*-window counter: allow
  // maxRequests right before the boundary and maxRequests right after,
  // for up to 2x the limit in a short span. A sliding window must not
  // allow this.
  const clock = makeFakeClock(0);
  const limiter = new SlidingWindowRateLimiter({ maxRequests: 5, windowSeconds: 10, now: clock.now });

  for (let i = 0; i < 5; i++) {
    assert.equal(limiter.allow("client-a"), true);
  }
  clock.advance(9_900); // 100ms before the first request would expire
  assert.equal(limiter.allow("client-a"), false, "fixed-window-style burst must be rejected");
});

test("old requests roll out of the window, freeing capacity", () => {
  const clock = makeFakeClock(0);
  const limiter = new SlidingWindowRateLimiter({ maxRequests: 2, windowSeconds: 5, now: clock.now });

  assert.equal(limiter.allow("client-a"), true);
  clock.advance(1000);
  assert.equal(limiter.allow("client-a"), true);
  assert.equal(limiter.allow("client-a"), false);

  clock.advance(4100); // first request (t=0) is now outside the 5s window
  assert.equal(limiter.allow("client-a"), true);
});

test("different clients are tracked independently", () => {
  const clock = makeFakeClock(0);
  const limiter = new SlidingWindowRateLimiter({ maxRequests: 1, windowSeconds: 10, now: clock.now });

  assert.equal(limiter.allow("client-a"), true);
  assert.equal(limiter.allow("client-a"), false);
  assert.equal(limiter.allow("client-b"), true, "a different client must have its own quota");
});

test("currentCount reflects only timestamps inside the current window", () => {
  const clock = makeFakeClock(0);
  const limiter = new SlidingWindowRateLimiter({ maxRequests: 10, windowSeconds: 5, now: clock.now });

  limiter.allow("client-a");
  clock.advance(1000);
  limiter.allow("client-a");
  assert.equal(limiter.currentCount("client-a"), 2);

  clock.advance(4100); // first request now outside the window
  assert.equal(limiter.currentCount("client-a"), 1);
});

test("pruneInactiveClients removes clients with no requests left in window", () => {
  const clock = makeFakeClock(0);
  const limiter = new SlidingWindowRateLimiter({ maxRequests: 2, windowSeconds: 5, now: clock.now });

  limiter.allow("client-a");
  limiter.allow("client-b");
  clock.advance(5100); // both clients' entries have now expired

  const pruned = limiter.pruneInactiveClients();
  assert.equal(pruned, 2);
  assert.equal(limiter.currentCount("client-a"), 0);
});

test("rejects non-positive maxRequests and windowSeconds in constructor", () => {
  assert.throws(() => new SlidingWindowRateLimiter({ maxRequests: 0, windowSeconds: 10 }));
  assert.throws(() => new SlidingWindowRateLimiter({ maxRequests: 5, windowSeconds: 0 }));
  assert.throws(() => new SlidingWindowRateLimiter({ maxRequests: -1, windowSeconds: 10 }));
});

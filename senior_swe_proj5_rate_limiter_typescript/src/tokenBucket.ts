/**
 * Token Bucket rate limiter.
 *
 * Allows bursts up to `capacity`, then refills at `refillRatePerSecond`
 * tokens/second. This is the algorithm commonly used by API gateways
 * (e.g. AWS API Gateway, Stripe's public documentation on rate limiting)
 * because it tolerates short bursts while enforcing a steady-state rate.
 *
 * Takes an injectable `now` clock function (defaults to Date.now) so
 * tests can control time deterministically instead of using real sleeps.
 */
export interface TokenBucketOptions {
  capacity: number;
  refillRatePerSecond: number;
  now?: () => number;
}

export class TokenBucketRateLimiter {
  private readonly capacity: number;
  private readonly refillRatePerSecond: number;
  private readonly now: () => number;

  private tokens: number;
  private lastRefillMs: number;

  constructor(options: TokenBucketOptions) {
    if (options.capacity <= 0) {
      throw new Error("capacity must be positive");
    }
    if (options.refillRatePerSecond <= 0) {
      throw new Error("refillRatePerSecond must be positive");
    }
    this.capacity = options.capacity;
    this.refillRatePerSecond = options.refillRatePerSecond;
    this.now = options.now ?? Date.now;
    this.tokens = options.capacity;
    this.lastRefillMs = this.now();
  }

  private refill(): void {
    const nowMs = this.now();
    const elapsedSeconds = Math.max(0, (nowMs - this.lastRefillMs) / 1000);
    if (elapsedSeconds <= 0) {
      return;
    }
    const refillAmount = elapsedSeconds * this.refillRatePerSecond;
    this.tokens = Math.min(this.capacity, this.tokens + refillAmount);
    this.lastRefillMs = nowMs;
  }

  /** Attempts to consume `cost` tokens (default 1). Returns true if
   *  allowed, false if the request should be rejected/throttled. */
  tryConsume(cost: number = 1): boolean {
    if (cost <= 0) {
      throw new Error("cost must be positive");
    }
    this.refill();
    if (this.tokens >= cost) {
      this.tokens -= cost;
      return true;
    }
    return false;
  }

  /** Current token count (after applying refill), for inspection/metrics. */
  availableTokens(): number {
    this.refill();
    return this.tokens;
  }
}

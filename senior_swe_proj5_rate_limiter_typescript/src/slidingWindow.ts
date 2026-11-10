/**
 * Sliding Window Log rate limiter.
 *
 * Tracks exact request timestamps per client within a rolling window,
 * giving precise rate enforcement (unlike a fixed-window counter, which
 * allows up to 2x the limit right at a window boundary — a well-known
 * fixed-window bug this implementation deliberately avoids). Trades
 * memory (O(requests in window) per client) for that precision, which
 * is the standard tradeoff discussed when choosing between rate-limiter
 * algorithms.
 */
export interface SlidingWindowOptions {
  maxRequests: number;
  windowSeconds: number;
  now?: () => number;
}

export class SlidingWindowRateLimiter {
  private readonly maxRequests: number;
  private readonly windowMs: number;
  private readonly now: () => number;
  private readonly requestsByClient: Map<string, number[]> = new Map();

  constructor(options: SlidingWindowOptions) {
    if (options.maxRequests <= 0) {
      throw new Error("maxRequests must be positive");
    }
    if (options.windowSeconds <= 0) {
      throw new Error("windowSeconds must be positive");
    }
    this.maxRequests = options.maxRequests;
    this.windowMs = options.windowSeconds * 1000;
    this.now = options.now ?? Date.now;
  }

  /** Returns true if the request for `clientId` is allowed under the
   *  current rolling window; records the request if allowed. */
  allow(clientId: string): boolean {
    const nowMs = this.now();
    const windowStart = nowMs - this.windowMs;

    const timestamps = this.requestsByClient.get(clientId) ?? [];
    // drop timestamps that have fallen out of the window
    const recent = timestamps.filter((t) => t > windowStart);

    if (recent.length >= this.maxRequests) {
      this.requestsByClient.set(clientId, recent);
      return false;
    }

    recent.push(nowMs);
    this.requestsByClient.set(clientId, recent);
    return true;
  }

  /** Number of requests currently counted within the window for a client. */
  currentCount(clientId: string): number {
    const nowMs = this.now();
    const windowStart = nowMs - this.windowMs;
    const timestamps = this.requestsByClient.get(clientId) ?? [];
    return timestamps.filter((t) => t > windowStart).length;
  }

  /** Removes stale per-client entries whose entire window has elapsed,
   *  to bound memory growth across many distinct clients over time. */
  pruneInactiveClients(): number {
    const nowMs = this.now();
    const windowStart = nowMs - this.windowMs;
    let pruned = 0;
    for (const [clientId, timestamps] of this.requestsByClient.entries()) {
      const recent = timestamps.filter((t) => t > windowStart);
      if (recent.length === 0) {
        this.requestsByClient.delete(clientId);
        pruned++;
      } else if (recent.length !== timestamps.length) {
        this.requestsByClient.set(clientId, recent);
      }
    }
    return pruned;
  }
}

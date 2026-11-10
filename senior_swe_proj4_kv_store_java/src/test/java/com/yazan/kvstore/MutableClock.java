package com.yazan.kvstore;

import java.time.Clock;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;

/**
 * A test-only {@link Clock} whose instant can be advanced manually, so
 * TTL-expiry tests are deterministic and fast (no Thread.sleep).
 */
final class MutableClock extends Clock {
    private Instant current;

    MutableClock(Instant start) {
        this.current = start;
    }

    void advanceSeconds(long seconds) {
        current = current.plusSeconds(seconds);
    }

    @Override
    public ZoneId getZone() {
        return ZoneOffset.UTC;
    }

    @Override
    public Clock withZone(ZoneId zone) {
        return this;
    }

    @Override
    public Instant instant() {
        return current;
    }
}

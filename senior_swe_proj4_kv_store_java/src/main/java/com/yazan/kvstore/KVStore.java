package com.yazan.kvstore;

import java.time.Clock;
import java.time.Instant;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Thread-safe in-memory key-value store with optional per-key TTL
 * (time-to-live) expiration.
 *
 * Takes a {@link Clock} as a constructor dependency (rather than calling
 * {@code System.currentTimeMillis()} directly) specifically so TTL
 * expiry logic can be tested deterministically with a fixed/advanceable
 * clock, instead of relying on real sleeps in tests.
 */
public final class KVStore {

    private static final class Entry {
        final String value;
        final Instant expiresAt; // null = never expires

        Entry(String value, Instant expiresAt) {
            this.value = value;
            this.expiresAt = expiresAt;
        }

        boolean isExpired(Instant now) {
            return expiresAt != null && !now.isBefore(expiresAt);
        }
    }

    private final ConcurrentHashMap<String, Entry> map = new ConcurrentHashMap<>();
    private final Clock clock;

    public KVStore() {
        this(Clock.systemUTC());
    }

    public KVStore(Clock clock) {
        this.clock = clock;
    }

    /** Stores a value with no expiration. */
    public void put(String key, String value) {
        requireNonEmptyKey(key);
        if (value == null) {
            throw new IllegalArgumentException("value must not be null");
        }
        map.put(key, new Entry(value, null));
    }

    /** Stores a value that expires after {@code ttlSeconds} seconds. */
    public void putWithTtl(String key, String value, long ttlSeconds) {
        requireNonEmptyKey(key);
        if (value == null) {
            throw new IllegalArgumentException("value must not be null");
        }
        if (ttlSeconds <= 0) {
            throw new IllegalArgumentException("ttlSeconds must be positive");
        }
        Instant expiresAt = clock.instant().plusSeconds(ttlSeconds);
        map.put(key, new Entry(value, expiresAt));
    }

    /** Returns the value for {@code key}, or empty if absent or expired. */
    public Optional<String> get(String key) {
        requireNonEmptyKey(key);
        Entry entry = map.get(key);
        if (entry == null) {
            return Optional.empty();
        }
        if (entry.isExpired(clock.instant())) {
            // lazy expiration: remove on read rather than running a
            // background sweeper thread, keeping this class simple and
            // dependency-free
            map.remove(key, entry);
            return Optional.empty();
        }
        return Optional.of(entry.value);
    }

    /** Deletes {@code key}. Returns true if a (non-expired) key was removed. */
    public boolean delete(String key) {
        requireNonEmptyKey(key);
        Entry removed = map.remove(key);
        return removed != null && !removed.isExpired(clock.instant());
    }

    public boolean containsKey(String key) {
        return get(key).isPresent();
    }

    /** Number of entries currently stored, INCLUDING not-yet-lazily-expired
     *  ones (an expired-but-not-yet-read entry still counts until the next
     *  get() for that key, or an explicit purgeExpired() call). */
    public int size() {
        return map.size();
    }

    /** Explicitly removes all expired entries now, rather than waiting for
     *  lazy expiration on next read. Useful for size()/metrics accuracy. */
    public int purgeExpired() {
        Instant now = clock.instant();
        int removed = 0;
        for (var iterator = map.entrySet().iterator(); iterator.hasNext(); ) {
            var e = iterator.next();
            if (e.getValue().isExpired(now)) {
                iterator.remove();
                removed++;
            }
        }
        return removed;
    }

    private static void requireNonEmptyKey(String key) {
        if (key == null || key.isEmpty()) {
            throw new IllegalArgumentException("key must not be null or empty");
        }
    }
}

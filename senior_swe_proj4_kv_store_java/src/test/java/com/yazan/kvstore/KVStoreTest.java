package com.yazan.kvstore;

import org.junit.Before;
import org.junit.Test;

import java.time.Instant;
import java.util.Optional;

import static org.junit.Assert.*;

public class KVStoreTest {

    private MutableClock clock;
    private KVStore store;

    @Before
    public void setUp() {
        clock = new MutableClock(Instant.parse("2026-01-01T00:00:00Z"));
        store = new KVStore(clock);
    }

    @Test
    public void putAndGet_returnsStoredValue() {
        store.put("name", "Yazan");
        assertEquals(Optional.of("Yazan"), store.get("name"));
    }

    @Test
    public void get_missingKey_returnsEmpty() {
        assertEquals(Optional.empty(), store.get("missing"));
    }

    @Test
    public void put_overwritesExistingValue() {
        store.put("k", "v1");
        store.put("k", "v2");
        assertEquals(Optional.of("v2"), store.get("k"));
    }

    @Test(expected = IllegalArgumentException.class)
    public void put_nullKey_throws() {
        store.put(null, "v");
    }

    @Test(expected = IllegalArgumentException.class)
    public void put_emptyKey_throws() {
        store.put("", "v");
    }

    @Test(expected = IllegalArgumentException.class)
    public void put_nullValue_throws() {
        store.put("k", null);
    }

    @Test
    public void delete_existingKey_returnsTrueAndRemoves() {
        store.put("k", "v");
        assertTrue(store.delete("k"));
        assertEquals(Optional.empty(), store.get("k"));
    }

    @Test
    public void delete_missingKey_returnsFalse() {
        assertFalse(store.delete("missing"));
    }

    @Test
    public void containsKey_reflectsPresence() {
        assertFalse(store.containsKey("k"));
        store.put("k", "v");
        assertTrue(store.containsKey("k"));
    }

    // --- TTL expiry ---

    @Test
    public void putWithTtl_valueAvailableBeforeExpiry() {
        store.putWithTtl("session", "abc123", 60);
        clock.advanceSeconds(59);
        assertEquals(Optional.of("abc123"), store.get("session"));
    }

    @Test
    public void putWithTtl_valueExpiredAtExactTtl() {
        store.putWithTtl("session", "abc123", 60);
        clock.advanceSeconds(60); // exactly at TTL -> should be expired
        assertEquals(Optional.empty(), store.get("session"));
    }

    @Test
    public void putWithTtl_valueExpiredAfterTtl() {
        store.putWithTtl("session", "abc123", 60);
        clock.advanceSeconds(61);
        assertEquals(Optional.empty(), store.get("session"));
    }

    @Test(expected = IllegalArgumentException.class)
    public void putWithTtl_zeroTtl_throws() {
        store.putWithTtl("k", "v", 0);
    }

    @Test(expected = IllegalArgumentException.class)
    public void putWithTtl_negativeTtl_throws() {
        store.putWithTtl("k", "v", -5);
    }

    @Test
    public void delete_expiredKey_returnsFalse() {
        store.putWithTtl("k", "v", 10);
        clock.advanceSeconds(11);
        assertFalse(store.delete("k")); // already expired, nothing real to delete
    }

    @Test
    public void purgeExpired_removesOnlyExpiredEntries() {
        store.put("permanent", "stays");
        store.putWithTtl("temp1", "v1", 10);
        store.putWithTtl("temp2", "v2", 100);
        clock.advanceSeconds(50); // temp1 expired, temp2 not yet, permanent never

        int removed = store.purgeExpired();

        assertEquals(1, removed);
        assertTrue(store.containsKey("permanent"));
        assertFalse(store.containsKey("temp1"));
        assertTrue(store.containsKey("temp2"));
    }

    @Test
    public void overwritingExpiredKey_withNewNonExpiringValue_works() {
        store.putWithTtl("k", "old", 10);
        clock.advanceSeconds(20); // expired
        store.put("k", "new"); // overwrite with a permanent value
        assertEquals(Optional.of("new"), store.get("k"));
    }
}

package com.yazan.kvstore;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

import static org.junit.Assert.*;

/**
 * Integration tests: starts a real KVHttpServer on an ephemeral port and
 * exercises it with real HTTP requests via java.net.http.HttpClient
 * (JDK built-in, no external HTTP client dependency), rather than
 * testing the handler logic in isolation.
 */
public class KVHttpServerTest {

    private KVHttpServer server;
    private HttpClient client;
    private String baseUrl;

    @Before
    public void setUp() throws IOException {
        server = new KVHttpServer(new KVStore(), 0); // port 0 = let OS assign a free port
        server.start();
        baseUrl = "http://localhost:" + server.getPort();
        client = HttpClient.newHttpClient();
    }

    @After
    public void tearDown() {
        server.stop();
    }

    private HttpResponse<String> send(String method, String path, String body) throws Exception {
        HttpRequest.Builder builder = HttpRequest.newBuilder(URI.create(baseUrl + path));
        switch (method) {
            case "GET" -> builder.GET();
            case "DELETE" -> builder.DELETE();
            case "PUT" -> builder.PUT(HttpRequest.BodyPublishers.ofString(body == null ? "" : body));
            default -> throw new IllegalArgumentException(method);
        }
        return client.send(builder.build(), HttpResponse.BodyHandlers.ofString());
    }

    @Test
    public void healthCheck_returns200() throws Exception {
        HttpResponse<String> resp = send("GET", "/health", null);
        assertEquals(200, resp.statusCode());
        assertTrue(resp.body().contains("\"ok\""));
    }

    @Test
    public void putThenGet_roundTrips() throws Exception {
        HttpResponse<String> put = send("PUT", "/kv/name", "Yazan");
        assertEquals(204, put.statusCode());

        HttpResponse<String> get = send("GET", "/kv/name", null);
        assertEquals(200, get.statusCode());
        assertTrue(get.body().contains("Yazan"));
    }

    @Test
    public void get_missingKey_returns404() throws Exception {
        HttpResponse<String> resp = send("GET", "/kv/does-not-exist", null);
        assertEquals(404, resp.statusCode());
        assertTrue(resp.body().contains("error"));
    }

    @Test
    public void delete_existingKey_returns204ThenGetReturns404() throws Exception {
        send("PUT", "/kv/temp", "value");
        HttpResponse<String> del = send("DELETE", "/kv/temp", null);
        assertEquals(204, del.statusCode());

        HttpResponse<String> get = send("GET", "/kv/temp", null);
        assertEquals(404, get.statusCode());
    }

    @Test
    public void delete_missingKey_returns404() throws Exception {
        HttpResponse<String> resp = send("DELETE", "/kv/never-existed", null);
        assertEquals(404, resp.statusCode());
    }

    @Test
    public void put_withTtl_expiresAfterRealTime() throws Exception {
        HttpResponse<String> put = send("PUT", "/kv/shortlived?ttl=1", "bye-soon");
        assertEquals(204, put.statusCode());

        HttpResponse<String> immediately = send("GET", "/kv/shortlived", null);
        assertEquals(200, immediately.statusCode());

        Thread.sleep(1200); // wait past the 1-second TTL (real sleep is
                             // acceptable here since this is an
                             // integration test of real wall-clock TTL
                             // behavior over HTTP, not a unit test of
                             // the expiry logic itself — that's covered
                             // deterministically in KVStoreTest)

        HttpResponse<String> afterExpiry = send("GET", "/kv/shortlived", null);
        assertEquals(404, afterExpiry.statusCode());
    }

    @Test
    public void put_invalidTtl_returns400() throws Exception {
        HttpResponse<String> resp = send("PUT", "/kv/k?ttl=not-a-number", "v");
        assertEquals(400, resp.statusCode());
    }

    @Test
    public void getWithEmptyKey_returns400() throws Exception {
        HttpResponse<String> resp = send("GET", "/kv/", null);
        assertEquals(400, resp.statusCode());
    }
}

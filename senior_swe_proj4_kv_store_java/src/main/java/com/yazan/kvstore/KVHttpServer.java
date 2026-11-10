package com.yazan.kvstore;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.Executors;

/**
 * REST-style HTTP front end for {@link KVStore}, built entirely on the
 * JDK's built-in {@code com.sun.net.httpserver} package — zero external
 * web-framework dependency (e.g. no Spring Boot). This was a deliberate
 * choice for this project to keep it buildable/runnable with nothing but
 * a JDK, but it also demonstrates understanding of what a framework like
 * Spring normally does under the hood (routing, request parsing, status
 * codes, error handling).
 *
 * Endpoints:
 *   GET    /health
 *   GET    /kv/{key}
 *   PUT    /kv/{key}?ttl={seconds}   body = raw value
 *   DELETE /kv/{key}
 */
public final class KVHttpServer {

    private final KVStore store;
    private final HttpServer server;

    public KVHttpServer(KVStore store, int port) throws IOException {
        this.store = store;
        this.server = HttpServer.create(new InetSocketAddress(port), 0);
        this.server.createContext("/health", this::handleHealth);
        this.server.createContext("/kv/", this::handleKv);
        this.server.setExecutor(Executors.newFixedThreadPool(8));
    }

    public void start() {
        server.start();
    }

    public void stop() {
        server.stop(0);
    }

    public int getPort() {
        return server.getAddress().getPort();
    }

    private void handleHealth(HttpExchange exchange) throws IOException {
        sendJson(exchange, 200, "{\"status\":\"ok\"}");
    }

    private void handleKv(HttpExchange exchange) throws IOException {
        String path = exchange.getRequestURI().getPath();
        String key = extractKey(path);

        if (key == null || key.isEmpty()) {
            sendJson(exchange, 400, errorJson("key is required, e.g. /kv/mykey"));
            return;
        }

        try {
            switch (exchange.getRequestMethod()) {
                case "GET" -> handleGet(exchange, key);
                case "PUT" -> handlePut(exchange, key);
                case "DELETE" -> handleDelete(exchange, key);
                default -> sendJson(exchange, 405, errorJson("method not allowed"));
            }
        } catch (IllegalArgumentException badRequest) {
            sendJson(exchange, 400, errorJson(badRequest.getMessage()));
        } catch (Exception unexpected) {
            sendJson(exchange, 500, errorJson("internal error: " + unexpected.getMessage()));
        }
    }

    private void handleGet(HttpExchange exchange, String key) throws IOException {
        Optional<String> value = store.get(key);
        if (value.isEmpty()) {
            sendJson(exchange, 404, errorJson("key not found: " + key));
            return;
        }
        sendJson(exchange, 200, "{\"key\":" + jsonString(key) + ",\"value\":" + jsonString(value.get()) + "}");
    }

    private void handlePut(HttpExchange exchange, String key) throws IOException {
        String body = new String(exchange.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
        Map<String, String> query = parseQuery(exchange.getRequestURI());
        String ttlParam = query.get("ttl");

        if (ttlParam != null) {
            long ttlSeconds;
            try {
                ttlSeconds = Long.parseLong(ttlParam);
            } catch (NumberFormatException e) {
                sendJson(exchange, 400, errorJson("ttl must be an integer number of seconds"));
                return;
            }
            store.putWithTtl(key, body, ttlSeconds);
        } else {
            store.put(key, body);
        }
        sendJson(exchange, 204, "");
    }

    private void handleDelete(HttpExchange exchange, String key) throws IOException {
        boolean removed = store.delete(key);
        sendJson(exchange, removed ? 204 : 404, removed ? "" : errorJson("key not found: " + key));
    }

    private static String extractKey(String path) {
        // path looks like "/kv/mykey"
        String prefix = "/kv/";
        if (!path.startsWith(prefix)) {
            return null;
        }
        return path.substring(prefix.length());
    }

    private static Map<String, String> parseQuery(URI uri) {
        Map<String, String> result = new java.util.HashMap<>();
        String query = uri.getRawQuery();
        if (query == null || query.isEmpty()) {
            return result;
        }
        for (String pair : query.split("&")) {
            int eq = pair.indexOf('=');
            if (eq < 0) continue;
            result.put(pair.substring(0, eq), pair.substring(eq + 1));
        }
        return result;
    }

    private static String errorJson(String message) {
        return "{\"error\":" + jsonString(message) + "}";
    }

    private static String jsonString(String s) {
        return "\"" + s.replace("\\", "\\\\").replace("\"", "\\\"") + "\"";
    }

    private void sendJson(HttpExchange exchange, int status, String body) throws IOException {
        byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().add("Content-Type", "application/json");
        exchange.sendResponseHeaders(status, bytes.length == 0 ? -1 : bytes.length);
        if (bytes.length > 0) {
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(bytes);
            }
        }
    }

    public static void main(String[] args) throws IOException {
        int port = args.length > 0 ? Integer.parseInt(args[0]) : 8080;
        KVHttpServer server = new KVHttpServer(new KVStore(), port);
        server.start();
        System.out.println("KV store listening on port " + server.getPort());
    }
}

/**
 * A minimal HTTP server demonstrating the rate limiters in actual use as
 * request-gating middleware — built on Node's built-in `http` module
 * (no Express), since this project was verified in an offline
 * environment with no internet access to install external framework
 * dependencies. See README for the reasoning.
 *
 * Endpoints:
 *   GET /api/data   — rate-limited to 5 requests / 10 seconds per client
 *                      (identified by the `x-client-id` header, falling
 *                      back to remote socket address)
 *   GET /health     — unthrottled liveness check
 */
import * as http from "node:http";
import { SlidingWindowRateLimiter } from "./slidingWindow";

const limiter = new SlidingWindowRateLimiter({ maxRequests: 5, windowSeconds: 10 });

function getClientId(req: http.IncomingMessage): string {
  const header = req.headers["x-client-id"];
  if (typeof header === "string" && header.length > 0) {
    return header;
  }
  return req.socket.remoteAddress ?? "unknown";
}

function sendJson(res: http.ServerResponse, status: number, body: unknown): void {
  const payload = JSON.stringify(body);
  res.writeHead(status, { "Content-Type": "application/json" });
  res.end(payload);
}

export function createServer(): http.Server {
  return http.createServer((req, res) => {
    const url = new URL(req.url ?? "/", "http://localhost");

    if (url.pathname === "/health") {
      sendJson(res, 200, { status: "ok" });
      return;
    }

    if (url.pathname === "/api/data") {
      const clientId = getClientId(req);
      if (!limiter.allow(clientId)) {
        sendJson(res, 429, {
          error: "rate_limit_exceeded",
          message: "Too many requests. Try again shortly.",
        });
        return;
      }
      sendJson(res, 200, { data: "here is your data", requestsThisWindow: limiter.currentCount(clientId) });
      return;
    }

    sendJson(res, 404, { error: "not_found" });
  });
}

if (require.main === module) {
  const port = Number(process.argv[2] ?? 3000);
  const server = createServer();
  server.listen(port, () => {
    console.log(`Rate-limited API demo listening on port ${port}`);
  });
}

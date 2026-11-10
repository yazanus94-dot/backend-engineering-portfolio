import test from "node:test";
import assert from "node:assert/strict";
import * as http from "node:http";
import { createServer } from "./server";

/** Starts the server on an ephemeral port and returns its base URL + a
 *  close() handle, so each test gets an isolated instance (the limiter
 *  is module-level state in server.ts, so sharing a server instance
 *  across tests would leak rate-limit state between them). */
function startServer(): Promise<{ baseUrl: string; close: () => Promise<void> }> {
  return new Promise((resolve) => {
    const server = createServer();
    server.listen(0, () => {
      const address = server.address();
      const port = typeof address === "object" && address ? address.port : 0;
      resolve({
        baseUrl: `http://127.0.0.1:${port}`,
        close: () => new Promise((res) => server.close(() => res())),
      });
    });
  });
}

function get(url: string, headers: Record<string, string> = {}): Promise<{ status: number; body: any }> {
  return new Promise((resolve, reject) => {
    http
      .get(url, { headers }, (res) => {
        let data = "";
        res.on("data", (chunk) => (data += chunk));
        res.on("end", () => {
          resolve({ status: res.statusCode ?? 0, body: JSON.parse(data) });
        });
      })
      .on("error", reject);
  });
}

test("GET /health returns 200 and is never rate-limited", async () => {
  const { baseUrl, close } = await startServer();
  try {
    const res = await get(`${baseUrl}/health`);
    assert.equal(res.status, 200);
    assert.deepEqual(res.body, { status: "ok" });
  } finally {
    await close();
  }
});

test("GET /unknown-route returns 404", async () => {
  const { baseUrl, close } = await startServer();
  try {
    const res = await get(`${baseUrl}/nope`);
    assert.equal(res.status, 404);
  } finally {
    await close();
  }
});

test("GET /api/data is rate-limited per client after 5 requests in the window", async () => {
  const { baseUrl, close } = await startServer();
  try {
    const headers = { "x-client-id": "integration-test-client" };
    for (let i = 0; i < 5; i++) {
      const res = await get(`${baseUrl}/api/data`, headers);
      assert.equal(res.status, 200, `request ${i + 1} should be allowed`);
    }
    const sixth = await get(`${baseUrl}/api/data`, headers);
    assert.equal(sixth.status, 429);
    assert.equal(sixth.body.error, "rate_limit_exceeded");
  } finally {
    await close();
  }
});

test("different x-client-id values get independent rate-limit quotas", async () => {
  const { baseUrl, close } = await startServer();
  try {
    const clientA = { "x-client-id": "client-a-integration" };
    for (let i = 0; i < 5; i++) {
      await get(`${baseUrl}/api/data`, clientA);
    }
    const sixthForA = await get(`${baseUrl}/api/data`, clientA);
    assert.equal(sixthForA.status, 429);

    const clientB = { "x-client-id": "client-b-integration" };
    const firstForB = await get(`${baseUrl}/api/data`, clientB);
    assert.equal(firstForB.status, 200, "a different client must not be throttled by client A's usage");
  } finally {
    await close();
  }
});

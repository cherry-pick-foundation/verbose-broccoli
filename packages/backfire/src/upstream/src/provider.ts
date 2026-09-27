// Jev-compatible endpoint transport.

import { isRecord } from "./lib.ts";

export type JevProvider = "compatible";

export interface AskResult {
  answers: Record<string, any>;
  usage: { input_tokens: number; output_tokens: number };
  provider: JevProvider;
  model: string;
}

function redactSecret(text: string, secret: string): string {
  return secret ? text.split(secret).join("[redacted]") : text;
}

const positiveIntFromEnv = (name: string, fallback: number): number => {
  const raw = Number(process.env[name]);
  return Number.isInteger(raw) && raw > 0 ? raw : fallback;
};

/** Whole-request deadline (all attempts), overridable for tests and tight hosts. */
const REQUEST_TIMEOUT_MS = positiveIntFromEnv("JEV_MCP_REQUEST_TIMEOUT_MS", 60_000);
/** Total attempts per request, including the first; clamped to 1..6. */
const MAX_ATTEMPTS = Math.min(6, Math.max(1, positiveIntFromEnv("JEV_MCP_MAX_ATTEMPTS", 3)));
const BASE_RETRY_DELAY_MS = 500;
const MAX_RETRY_DELAY_MS = 4_000;
/** Stream-checked ceiling for success and error bodies alike. */
const MAX_RESPONSE_BYTES = 1_000_000;

/** Only the not-processed status allowlist is retried, and 5xx means 500-599: out-of-range statuses are protocol noise, not retry signals. */
const isRetryableStatus = (status: number) => status === 408 || status === 409 || status === 429 || (status >= 500 && status <= 599);

interface Deadline {
  signal: AbortSignal;
  timedOut: () => boolean;
  dispose: () => void;
}

/** One deadline covering every attempt; expiry and caller aborts never retry. */
function deadlineSignal(signal: AbortSignal | undefined, timeoutMs: number): Deadline {
  const controller = new AbortController();
  let timedOut = false;
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs);
  const relay = () => controller.abort(signal?.reason);
  if (signal) {
    if (signal.aborted) relay();
    else signal.addEventListener("abort", relay, { once: true });
  }
  return {
    signal: controller.signal,
    timedOut: () => timedOut,
    dispose: () => {
      clearTimeout(timer);
      signal?.removeEventListener("abort", relay);
    },
  };
}

/** Jittered exponential backoff: 50-100% of the doubling delay, capped. */
function retryDelayMs(attempt: number): number {
  const exp = Math.min(BASE_RETRY_DELAY_MS * 2 ** (attempt - 1), MAX_RETRY_DELAY_MS);
  return exp * (0.5 + Math.random() * 0.5);
}

/**
 * Backoff that ends early, without another attempt, when the deadline expires
 * or the caller aborts: the whole-request deadline must not be overrun by a
 * sleep, and a cancelled call must surface promptly.
 */
function backoffDelay(attempt: number, deadline: Deadline): Promise<void> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      cleanup();
      resolve();
    }, retryDelayMs(attempt));
    const onAbort = () => {
      cleanup();
      reject(
        deadline.timedOut()
          ? new Error(`Jev request exceeded the ${REQUEST_TIMEOUT_MS}ms deadline.`)
          : deadline.signal.reason,
      );
    };
    const cleanup = () => {
      clearTimeout(timer);
      deadline.signal.removeEventListener("abort", onAbort);
    };
    if (deadline.signal.aborted) onAbort();
    else deadline.signal.addEventListener("abort", onAbort, { once: true });
  });
}

/**
 * Read a response body with the byte ceiling enforced while streaming.
 * Content-Length is advisory (and absent for chunked responses), so the
 * limit is enforced on the bytes actually read, on success and error paths
 * alike. Never retried: an oversized body is a protocol violation.
 */
async function readBodyBounded(response: Response, deadline: Deadline): Promise<string> {
  const reader = response.body?.getReader();
  if (!reader) return "";
  const chunks: Uint8Array[] = [];
  let total = 0;
  // One abort watcher for the whole read, not one per chunk: a fragmented body
  // must not accumulate listeners and closures while it streams.
  let onAbort!: () => void;
  const aborted = new Promise<never>((_, reject) => {
    onAbort = () =>
      reject(
        deadline.timedOut()
          ? new Error(`Jev request exceeded the ${REQUEST_TIMEOUT_MS}ms deadline while reading the response.`)
          : deadline.signal.reason,
      );
  });
  aborted.catch(() => {}); // stays handled when a read wins every race
  deadline.signal.addEventListener("abort", onAbort, { once: true });
  try {
    if (deadline.signal.aborted) onAbort();
    for (;;) {
      const { done, value } = await Promise.race([reader.read(), aborted]);
      if (done) break;
      total += value.byteLength;
      if (total > MAX_RESPONSE_BYTES) {
        throw new Error(`Response exceeded ${MAX_RESPONSE_BYTES} bytes after reading ${total}; aborting the read.`);
      }
      chunks.push(value);
    }
  } catch (error) {
    // The body reader races our watcher to the same abort and may reject
    // first with its raw AbortError; translate, exactly as the fetch catch
    // does, so deadline expiry reads as a deadline, not "operation aborted".
    if (deadline.signal.aborted) {
      throw deadline.timedOut()
        ? new Error(`Jev request exceeded the ${REQUEST_TIMEOUT_MS}ms deadline while reading the response.`)
        : deadline.signal.reason;
    }
    throw error;
  } finally {
    deadline.signal.removeEventListener("abort", onAbort);
    // On the success path the reader is already done; on throw this releases
    // the connection instead of leaking it.
    await reader.cancel().catch(() => {});
    try {
      reader.releaseLock();
    } catch {
      // Already released by cancel on some runtimes.
    }
  }
  const bytes = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    bytes.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return new TextDecoder().decode(bytes);
}

/**
 * Fetch with bounded, jittered retries on the 408/409/429/5xx allowlist only.
 * A status cannot prove the request was not processed, but that allowlist is
 * the standard not-processed signal set and the only retry trigger. Ambiguous
 * network-level failures (connection reset mid-response, TLS errors) never
 * retry: without an idempotency key, re-sending after an ambiguous failure can
 * double-process a paid call. Caller aborts and deadline expiry surface
 * immediately, cutting any backoff short, and never retry.
 */
async function fetchWithResilience(url: string, init: RequestInit, deadline: Deadline): Promise<Response> {
  for (let attempt = 1; ; attempt++) {
    let response: Response;
    try {
      response = await fetch(url, { ...init, signal: deadline.signal });
    } catch (error) {
      if (deadline.timedOut()) {
        throw new Error(`Jev request exceeded the ${REQUEST_TIMEOUT_MS}ms deadline.`);
      }
      throw error; // caller cancellation or network failure: never re-sent
    }
    if (isRetryableStatus(response.status) && attempt < MAX_ATTEMPTS) {
      // Drain and release the connection before backing off.
      await response.body?.cancel().catch(() => {});
      await backoffDelay(attempt, deadline);
      continue;
    }
    return response;
  }
}

function resolve(env: NodeJS.ProcessEnv): JevProvider {
  if (env.JEV_PROVIDER !== "compatible") {
    throw new Error('JEV_PROVIDER must be set to "compatible".');
  }
  const missing = ["JEV_API_KEY", "JEV_API_BASE_URL"].filter((name) => !env[name]);
  if (missing.length > 0) {
    throw new Error(
      `JEV_PROVIDER=compatible but ${missing.join(" and ")} ${missing.length > 1 ? "are" : "is"} not set. ` +
        "JEV_MCP_MODEL is optional and defaults to jev-latest.",
    );
  }
  return "compatible";
}

export async function askJev(
  state: unknown,
  questions: Record<string, unknown>,
  model: string,
  signal?: AbortSignal,
): Promise<AskResult> {
  const provider = resolve(process.env);

  const deadline = deadlineSignal(signal, REQUEST_TIMEOUT_MS);
  try {
    const response = await fetchWithResilience(process.env.JEV_API_BASE_URL!, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${process.env.JEV_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ model, state, questions }),
    }, deadline);
    const bodyText = await readBodyBounded(response, deadline);
    if (!response.ok) {
      const apiKey = process.env.JEV_API_KEY ?? "";
      // Redact the key before the body becomes MCP-visible error text; a
      // proxy that reflects the request would otherwise echo it back.
      const body = redactSecret(bodyText, apiKey).slice(0, 200);
      throw new Error(`Jev-compatible endpoint ${response.status}: ${body}`);
    }
    let body: unknown;
    try {
      body = JSON.parse(bodyText);
    } catch {
      body = null; // parse failures never retry; surface as invalid response
    }
      const invalid = (why: string) => new Error(`Jev-compatible endpoint returned an invalid response: ${why}`);
      if (!isRecord(body)) throw invalid("expected a JSON object.");
      if (!isRecord(body.answers)) throw invalid("expected an answers object.");
      // Envelope shape is validated here; per-question answer validity is the
      // tools' job. Each tool fails closed under its invalid_response contract,
      // so a missing or malformed answer can never reach tool-level defaults.
      let inputTokens = 0;
      let outputTokens = 0;
      if (body.usage !== undefined && body.usage !== null) {
    const tokenCount = (v: unknown): v is number => typeof v === "number" && Number.isFinite(v) && v >= 0;
    if (!isRecord(body.usage) || !tokenCount(body.usage.input_tokens) || !tokenCount(body.usage.output_tokens)) {
      throw invalid("usage must report finite non-negative input_tokens and output_tokens.");
    }
    inputTokens = body.usage.input_tokens;
    outputTokens = body.usage.output_tokens;
      }
      if (body.model !== undefined && body.model !== null && typeof body.model !== "string") {
    throw invalid("model must be absent or a string.");
      }
    return {
      answers: body.answers,
      usage: { input_tokens: inputTokens, output_tokens: outputTokens },
      provider,
      model: typeof body.model === "string" ? body.model : model,
    };
  } finally {
    deadline.dispose();
  }
}

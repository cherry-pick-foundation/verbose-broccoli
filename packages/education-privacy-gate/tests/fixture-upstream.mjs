// Test-only wrapper: import the locked public entry after replacing fetch.
// No delegation to the native fetch function, and no files written per call.
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';

const [entry, mode = 'normal'] = process.argv.slice(2);
assert(entry.startsWith('/') && entry.endsWith('/@jkudish/jev-mcp/dist/index.js'));
const attempts = new Map();
// Only this test wrapper uses upstream's supported test controls.
if (mode === 'deadline') process.env.JEV_MCP_REQUEST_TIMEOUT_MS = '25';
if (mode === 'retry-six') process.env.JEV_MCP_MAX_ATTEMPTS = '99';
if (mode === 'retry-one') process.env.JEV_MCP_MAX_ATTEMPTS = '1';
const deadlines = [];
const nativeSetTimeout = globalThis.setTimeout;
globalThis.setTimeout = (callback, delay, ...args) => {
  if (delay === 60_000 || (mode === 'deadline' && delay === 25)) deadlines.push(delay);
  return nativeSetTimeout(callback, delay, ...args);
};
globalThis.fetch = async (url, init) => {
  assert.equal(String(url), 'https://openrouter.ai/api/alpha/decisions');
  const request = JSON.parse(init.body);
  assert.equal(request.model, 'typesafe/jev-1.13');
  const attempt = (attempts.get(init.body) ?? 0) + 1;
  attempts.set(init.body, attempt);
  if (mode === 'deadline') return new Promise((_, reject) => {
    init.signal.addEventListener('abort', () => reject(init.signal.reason), {once: true});
  });
  if (mode === 'retry-one' && attempt === 1) return new Response('{}', {status: 429});
  if (mode === 'retry-six' && attempt < 6) return new Response('{}', {status: 429});
  if (mode === 'oversize') return new Response('x'.repeat(1_000_001));
  if (mode === 'retry' && attempt < 3) return new Response('{}', {status: 429});
  const answers = Object.fromEntries(Object.entries(request.questions).map(([id, question]) => {
    if (question.type === 'noul') return [id, {type: 'noul', noul: 0.9}];
    const keys = Array.isArray(question.criteria) ? question.criteria.map((_, i) => String(i)) : Object.keys(question.criteria);
    const selected = question.type === 'score' && /correctness|spec_match/.test(id) ? keys.at(-1) : keys[0];
    const probabilities = Object.fromEntries(keys.map(key => [key, key === selected ? 1 : 0]));
    return [id, {type: question.type, ...(question.type === 'score' ? {score: Number(selected)} : {choice: selected}), probabilities, confidence: 0.99}];
  }));
  return new Response(JSON.stringify({answers, usage: {
    input_tokens: {deadlines, request, url: String(url), attempt, external_network_requests: 0, env_keys: Object.keys(process.env).sort(), cwd: process.cwd(), entry},
    output_tokens: JSON.stringify({echo: request.state}),
  }}), {status: 200, headers: {'Content-Type': 'application/json'}});
};
await import(pathToFileURL(entry).href);

import {parse} from '@std/toml';

type JsonObject = Record<string, unknown>;

interface ThinkingPaths {
  content_path?: string;
  token_path?: string;
}

interface Profile {
  name: string;
  base_url: string;
  model: string;
  credential: string;
  rate_limit_per_second?: number;
  request: JsonObject;
  thinking: ThinkingPaths;
}

interface ProbeSummary {
  label: string;
  status: number | null;
  model?: string;
  thinking_content_non_empty?: boolean;
  thinking_tokens?: number | null;
  prompt_tokens?: number;
  completion_tokens?: number;
  total_tokens?: number;
  finish_reason?: string;
  elapsed_ms: number;
}

function object(value: unknown): JsonObject {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
    ? (value as JsonObject)
    : {};
}

function isObject(value: unknown): boolean {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function hasUnknownKeys(value: JsonObject, allowed: string[]): boolean {
  return Object.keys(value).some(key => !allowed.includes(key));
}

function valueAtPath(value: unknown, path: string): unknown {
  for (const key of path.split('.')) value = object(value)[key];
  return value;
}

export function selectProfile(
  value: unknown,
  providerOverride?: string,
): Profile {
  const config = object(value);
  if (hasUnknownKeys(config, ['provider', 'providers'])) throw new Error();
  if (
    config.provider !== undefined &&
    (typeof config.provider !== 'string' ||
      !/^[a-z0-9-]+$/.test(config.provider))
  )
    throw new Error();
  const name = providerOverride ?? config.provider;
  const providers = object(config.providers);
  if (
    typeof name !== 'string' ||
    !/^[a-z0-9-]+$/.test(name) ||
    !isObject(config.providers) ||
    !Object.hasOwn(providers, name)
  )
    throw new Error();

  const profile = object(providers[name]);
  const thinking = object(profile.thinking);
  const request = profile.request === undefined ? {} : object(profile.request);
  const path = (value: unknown) =>
    typeof value === 'string' &&
    value.length > 0 &&
    value.split('.').every(part => part.length > 0);
  const statuses = object(profile.statuses);

  if (
    hasUnknownKeys(profile, [
      'api',
      'base_url',
      'model',
      'credential',
      'rate_limit_per_second',
      'request',
      'thinking',
      'statuses',
    ]) ||
    profile.api !== 'openai' ||
    typeof profile.base_url !== 'string' ||
    profile.base_url.length === 0 ||
    typeof profile.model !== 'string' ||
    profile.model.length === 0 ||
    typeof profile.credential !== 'string' ||
    !/^[A-Z_][A-Z0-9_]*$/.test(profile.credential) ||
    (profile.request !== undefined && !isObject(profile.request)) ||
    !isObject(profile.thinking) ||
    hasUnknownKeys(thinking, ['requested', 'content_path', 'token_path']) ||
    (thinking.requested !== 'on' && thinking.requested !== 'off') ||
    ['model', 'messages', 'stream', 'n'].some(key => key in request) ||
    (thinking.content_path !== undefined && !path(thinking.content_path)) ||
    (thinking.token_path !== undefined && !path(thinking.token_path)) ||
    (thinking.requested === 'on' &&
      thinking.content_path === undefined &&
      thinking.token_path === undefined) ||
    (thinking.requested === 'off' &&
      (thinking.content_path !== undefined ||
        thinking.token_path !== undefined)) ||
    (profile.rate_limit_per_second !== undefined &&
      (typeof profile.rate_limit_per_second !== 'number' ||
        !Number.isFinite(profile.rate_limit_per_second) ||
        profile.rate_limit_per_second < 0)) ||
    (profile.statuses !== undefined &&
      (!isObject(profile.statuses) ||
        Object.entries(statuses).some(
          ([status, meaning]) =>
            !/^\d+$/.test(status) ||
            Number(status) < 100 ||
            Number(status) > 599 ||
            ![
              'credential_rejected',
              'balance_exhausted',
              'request_rejected',
              'rate_limited',
            ].includes(String(meaning)),
        )))
  )
    throw new Error();

  return {
    name,
    base_url: profile.base_url,
    model: profile.model,
    credential: profile.credential,
    ...(typeof profile.rate_limit_per_second === 'number'
      ? {rate_limit_per_second: profile.rate_limit_per_second}
      : {}),
    request,
    thinking: {
      ...(typeof thinking.content_path === 'string'
        ? {content_path: thinking.content_path}
        : {}),
      ...(typeof thinking.token_path === 'string'
        ? {token_path: thinking.token_path}
        : {}),
    },
  };
}

export function summarize(
  label: string,
  status: number | null,
  body: unknown,
  elapsedMs: number,
  thinking: ThinkingPaths,
): ProbeSummary {
  const response = object(body);
  const choice = object(
    Array.isArray(response.choices) ? response.choices[0] : null,
  );
  const usage = object(response.usage);
  const message = object(choice.message);
  const summary: ProbeSummary = {
    label,
    status,
    elapsed_ms: Math.round(elapsedMs),
  };

  if (typeof response.model === 'string') summary.model = response.model;
  if (thinking.content_path) {
    const content = valueAtPath(message, thinking.content_path);
    summary.thinking_content_non_empty =
      typeof content === 'string' && content.trim().length > 0;
  }
  if (thinking.token_path) {
    const tokens = valueAtPath(usage, thinking.token_path);
    summary.thinking_tokens = typeof tokens === 'number' ? tokens : null;
  }
  for (const key of [
    'prompt_tokens',
    'completion_tokens',
    'total_tokens',
  ] as const) {
    if (typeof usage[key] === 'number') summary[key] = usage[key];
  }
  if (typeof choice.finish_reason === 'string') {
    summary.finish_reason = choice.finish_reason;
  }
  return summary;
}

export function burstSize(rateLimit?: number): number | null {
  return rateLimit === undefined ? null : Math.floor(rateLimit) + 1;
}

export function burstNotApplicable() {
  return {
    label: 'burst',
    status: null,
    not_applicable: 'profile has no rate_limit_per_second',
  };
}

async function request(
  label: string,
  apiKey: string,
  profile: Profile,
  model: string,
  fields: JsonObject,
  endpoint: string,
): Promise<ProbeSummary> {
  const started = performance.now();
  let status: number | null = null;
  let body: unknown;
  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ...fields,
        model,
        messages: [{role: 'user', content: 'Return a small JSON object.'}],
      }),
      signal: AbortSignal.timeout(30000),
    });
    status = response.status;
    if (response.status === 200) {
      try {
        body = await response.json();
      } catch {
        body = undefined;
      }
    }
  } catch {
    // Keep transport errors out of the probe output.
  }
  return summarize(
    label,
    status,
    body,
    performance.now() - started,
    profile.thinking,
  );
}

async function main() {
  let source: string | URL = new URL(
    '../backfire_backend/config.toml',
    import.meta.url,
  );
  let providerOverride: string | undefined;
  for (let i = 0; i < Deno.args.length; i++) {
    if (Deno.args[i] === '--config' && Deno.args[i + 1]) {
      source = Deno.args[++i];
    } else if (
      Deno.args[i].startsWith('--') ||
      providerOverride !== undefined
    ) {
      throw new Error();
    } else {
      providerOverride = Deno.args[i];
    }
  }
  const profile = selectProfile(
    parse(await Deno.readTextFile(source)),
    providerOverride,
  );
  const home = Deno.env.get('HOME');
  const configHome =
    Deno.env.get('XDG_CONFIG_HOME') ?? (home ? `${home}/.config` : undefined);
  if (!configHome) throw new Error();
  const credentials = await Deno.readTextFile(
    `${configHome}/verbose-broccoli/backfire/${profile.name}.env`,
  );
  const apiKey = credentials
    .split(/\r?\n/)
    .find(line => line.startsWith(`${profile.credential}=`))
    ?.slice(profile.credential.length + 1)
    .trim();
  if (!apiKey) throw new Error();

  const endpoint = `${profile.base_url.replace(/\/+$/, '')}/chat/completions`;
  const results: Array<ProbeSummary | ReturnType<typeof burstNotApplicable>> = [
    await request(
      'settings',
      apiKey,
      profile,
      profile.model,
      profile.request,
      endpoint,
    ),
    await request(
      'invalid key',
      'not-a-valid-api-key-for-probe',
      profile,
      profile.model,
      profile.request,
      endpoint,
    ),
    await request(
      'unknown model',
      apiKey,
      profile,
      'verbose-broccoli/unknown-model-for-probe',
      profile.request,
      endpoint,
    ),
  ];
  const count = burstSize(profile.rate_limit_per_second);
  if (count === null) {
    results.push(burstNotApplicable());
  } else {
    const burstFields = {...profile.request, max_tokens: 1};
    results.push(
      ...(await Promise.all(
        Array.from({length: count}, (_, index) =>
          request(
            `burst-${index + 1}`,
            apiKey,
            profile,
            profile.model,
            burstFields,
            endpoint,
          ),
        ),
      )),
    );
  }
  for (const result of results) console.log(JSON.stringify(result));
}

if (import.meta.main) {
  main().catch(() => {
    console.error('Probe could not start.');
    Deno.exitCode = 1;
  });
}

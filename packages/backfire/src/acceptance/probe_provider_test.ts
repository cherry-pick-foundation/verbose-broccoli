import {assert, assertEquals, assertThrows} from '@std/assert';
import {
  burstNotApplicable,
  burstSize,
  selectProfile,
  summarize,
} from './probe_provider.ts';

function config() {
  return {
    provider: 'alpha',
    providers: {
      alpha: {
        api: 'openai',
        base_url: 'https://example.test/v1',
        model: 'model-for-test',
        credential: 'API_KEY',
        request: {},
        thinking: {requested: 'on', content_path: 'reasoning_content'},
      },
    },
  };
}

Deno.test('probe summary prints only approved fields and omits request and response content', () => {
  const output = JSON.stringify(
    summarize(
      'settings',
      200,
      {
        model: 'model-for-probe',
        choices: [
          {
            message: {
              reasoning_content: 'private thinking marker',
              content: 'private response marker',
            },
            finish_reason: 'stop',
          },
        ],
        usage: {
          completion_tokens_details: {reasoning_tokens: 4},
          prompt_tokens: 8,
          completion_tokens: 10,
          total_tokens: 18,
        },
        error: 'private error marker',
        request: 'private request marker',
      },
      17.6,
      {
        content_path: 'reasoning_content',
        token_path: 'completion_tokens_details.reasoning_tokens',
      },
    ),
  );

  assertEquals(
    output,
    '{"label":"settings","status":200,"elapsed_ms":18,"model":"model-for-probe","thinking_content_non_empty":true,"thinking_tokens":4,"prompt_tokens":8,"completion_tokens":10,"total_tokens":18,"finish_reason":"stop"}',
  );
  for (const marker of [
    'private thinking marker',
    'private response marker',
    'private error marker',
    'private request marker',
  ])
    assert(!output.includes(marker));
});

Deno.test('selected table without a rate limit skips the burst with its reason', () => {
  const profile = selectProfile(config());
  assertEquals(burstSize(profile.rate_limit_per_second), null);
  assertEquals(
    selectProfile({...config(), provider: 'missing'}, 'alpha').name,
    'alpha',
  );
  assertEquals(
    JSON.stringify(burstNotApplicable()),
    '{"label":"burst","status":null,"not_applicable":"profile has no rate_limit_per_second"}',
  );
  assertEquals(burstSize(5), 6);
});

Deno.test('selection rejects a missing table and unknown top-level key', () => {
  assertThrows(() => selectProfile({provider: 'alpha', providers: {}}));
  assertThrows(() => selectProfile({...config(), unexpected: true}));
});

Deno.test('selected table rejects unknown keys and forbidden request fields', () => {
  assertThrows(() =>
    selectProfile({
      ...config(),
      providers: {alpha: {...config().providers.alpha, name: 'alpha'}},
    }),
  );
  assertThrows(() =>
    selectProfile({
      ...config(),
      providers: {
        alpha: {...config().providers.alpha, request: {model: 'other'}},
      },
    }),
  );
});

import {test} from 'node:test';
import assert from 'node:assert/strict';
import {spawnSync} from 'node:child_process';
import {
  copyFileSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from 'node:fs';
import {tmpdir} from 'node:os';
import {join, resolve} from 'node:path';

const config = JSON.parse(
  readFileSync('.config/coordinator-context.json', 'utf8'),
);

void test('both client hooks restore context and isolate coordinator thresholds', () => {
  const scratch = mkdtempSync(join(tmpdir(), 'coordinator-context-'));
  try {
    const root = join(scratch, 'feature-example');
    const stateHome = join(scratch, 'state');
    const state = join(
      stateHome,
      config.stateDirectory,
      'feature-example',
      config.stateFile,
    );
    const transcript = join(scratch, 'transcript.jsonl');
    const notification = join(scratch, 'notification.txt');
    mkdirSync(join(root, 'scripts'), {recursive: true});
    mkdirSync(join(root, '.config'));
    mkdirSync(resolve(state, '..'), {recursive: true});
    copyFileSync(
      'scripts/coordinator-context.ts',
      join(root, 'scripts/coordinator-context.ts'),
    );
    const notes =
      'START\n' +
      'complete standing note\n'.repeat(2000) +
      'MIDDLE\n' +
      'rule\n'.repeat(3000) +
      'END';
    writeFileSync(join(root, 'notes.md'), notes);
    const testConfig = {...config, notes: ['notes.md']};
    const configure = () =>
      writeFileSync(
        join(root, '.config/coordinator-context.json'),
        JSON.stringify(testConfig),
      );
    configure();
    writeFileSync(
      join(scratch, 'notify-send'),
      '#!/bin/sh\nprintf "%s\\n" "$@" > "$NOTIFICATION_LOG"\n',
      {mode: 0o700},
    );
    const run = (client: string, source = 'compact', session = 'current') => {
      const result = spawnSync(
        process.execPath,
        [
          '--disable-warning=MODULE_TYPELESS_PACKAGE_JSON',
          '--permission',
          '--allow-fs-read=*',
          '--allow-child-process',
          join(root, 'scripts/coordinator-context.ts'),
          client,
        ],
        {
          input: JSON.stringify({
            hook_event_name: 'SessionStart',
            source,
            session_id: session,
            transcript_path: transcript,
            cwd: join(root, 'scripts'),
          }),
          encoding: 'utf8',
          env: {
            ...process.env,
            XDG_STATE_HOME: stateHome,
            PATH: scratch,
            NOTIFICATION_LOG: notification,
          },
        },
      );
      assert.equal(result.status, 0, result.stderr);
      const output = JSON.parse(result.stdout);
      assert.equal(output.hookSpecificOutput.hookEventName, 'SessionStart');
      return output.hookSpecificOutput.additionalContext as string;
    };
    for (const client of ['codex', 'claude']) {
      const owner = `Coordinator session: ${client}/current\nDecisions: retain this decision.\n`;
      writeFileSync(state, owner);
      const records = (count: number, session = 'current') =>
        client === 'codex'
          ? [
              {type: 'session_meta', payload: {id: session}},
              ...Array.from({length: count}, () => ({
                type: 'compacted',
                payload: {message: 'summary'},
              })),
              {type: 'event_msg', payload: {type: 'context_compacted'}},
            ]
          : [
              ...Array.from({length: count}, (_, i) => ({
                type: 'system',
                subtype: 'compact_boundary',
                sessionId: session,
                uuid: `boundary-${i}`,
              })),
              {
                type: 'user',
                sessionId: session,
                message: 'compact_boundary mention',
              },
            ];
      const saveTranscript = (count: number, session = 'current') =>
        writeFileSync(
          transcript,
          records(count, session)
            .map(record => JSON.stringify(record))
            .join('\n') + '\n',
        );
      saveTranscript(1);
      let context = run(client);
      assert.ok(context.includes(notes));
      assert.ok(context.includes(owner));
      assert.ok(!context.includes('Start no new work'));
      assert.ok(!context.includes('Notification failed'));
      assert.throws(() => readFileSync(notification));
      saveTranscript(2);
      if (client === 'claude') {
        const original = readFileSync(transcript, 'utf8');
        writeFileSync(
          transcript,
          original +
            JSON.stringify(records(1)[0]) +
            '\n' +
            JSON.stringify({
              type: 'system',
              subtype: 'compact_boundary',
              sessionId: 'other',
              uuid: 'other',
            }) +
            '\n',
        );
      }
      const before = readFileSync(transcript, 'utf8');
      context = run(client);
      assert.ok(context.includes('Start no new work'));
      assert.ok(context.includes('2 compactions'));
      assert.ok(
        readFileSync(notification, 'utf8').includes(
          'Start a fresh coordinator',
        ),
      );
      assert.ok(
        !readFileSync(notification, 'utf8').includes('retain this decision'),
      );
      assert.equal(readFileSync(state, 'utf8'), owner);
      assert.equal(readFileSync(transcript, 'utf8'), before);
      assert.equal(readFileSync(join(root, 'notes.md'), 'utf8'), notes);
      rmSync(notification);
      assert.ok(
        !run(client, 'compact', 'worker').includes('Start no new work'),
      );
      assert.throws(() => readFileSync(notification));
      writeFileSync(state, owner.replace('/current', '/replacement'));
      saveTranscript(1, 'replacement');
      assert.ok(
        !run(client, 'compact', 'replacement').includes('Start no new work'),
      );
      writeFileSync(state, owner);
      saveTranscript(2, 'other');
      assert.ok(!run(client).includes('Start no new work'));
      for (const source of ['startup', 'resume', 'clear']) {
        saveTranscript(0);
        context = run(client, source);
        assert.ok(context.includes(notes));
        assert.ok(context.includes(owner));
        assert.ok(context.includes(`Coordinator session: ${client}/current`));
        assert.ok(context.includes('Narrow workers must not claim'));
        assert.ok(!context.includes('Start no new work'));
      }
      saveTranscript(2);
      rmSync(join(scratch, 'notify-send'));
      assert.ok(run(client).includes('Notification failed'));
      writeFileSync(
        join(scratch, 'notify-send'),
        '#!/bin/sh\nprintf "%s\\n" "$@" > "$NOTIFICATION_LOG"\n',
        {mode: 0o700},
      );
      rmSync(notification, {force: true});
      writeFileSync(transcript, '{broken}\n');
      assert.ok(run(client).includes('Compaction count unavailable'));
      rmSync(transcript);
      assert.ok(run(client).includes('Compaction count unavailable'));
      rmSync(state);
      assert.ok(run(client).includes('Unavailable source:'));
      assert.throws(() => readFileSync(state));
    }
    writeFileSync(state, 'Coordinator session: codex/current\n');
    writeFileSync(
      transcript,
      '{"type":"session_meta","payload":{"id":"current"}}\n{"type":"compacted"}\n',
    );
    for (const role of ['main', 'develop']) {
      testConfig.worktreeAliases['feature-example'] = role;
      configure();
      const roleState = join(
        stateHome,
        config.stateDirectory,
        role,
        config.stateFile,
      );
      mkdirSync(resolve(roleState, '..'), {recursive: true});
      writeFileSync(roleState, 'Coordinator session: codex/current\n');
      const context = run('codex');
      assert.equal(context.includes('Start no new work'), role === 'main');
    }
    testConfig.maxContextBytes = 50;
    configure();
    const fallback = run('codex', 'startup');
    assert.ok(fallback.includes('Read every source in full'));
    assert.ok(fallback.includes(join(root, 'notes.md')));
    assert.ok(!fallback.includes('MIDDLE'));
  } finally {
    rmSync(scratch, {recursive: true, force: true});
  }
});

void test('hook definitions preserve Ponytail and match all required sources', () => {
  for (const [client, path] of [
    ['codex', '.codex/hooks.json'],
    ['claude', '.claude/settings.json'],
  ]) {
    const settings = JSON.parse(readFileSync(path, 'utf8'));
    const entry = settings.hooks.SessionStart.find(
      (item: {hooks: {command: string}[]}) =>
        item.hooks.some(hook =>
          hook.command.includes('scripts/coordinator-context.ts'),
        ),
    );
    assert.ok(entry);
    for (const source of ['startup', 'resume', 'clear', 'compact'])
      assert.ok(new RegExp(entry.matcher).test(source));
    assert.ok(entry.hooks[0].command.endsWith(client));
    if (client === 'codex') {
      assert.ok(
        entry.hooks[0].additionalContextLimit >= config.maxContextBytes,
      );
      assert.ok(
        settings.hooks.SessionStart.some((item: {hooks: {command: string}[]}) =>
          item.hooks.some(hook =>
            hook.command.includes('ponytail-activate.js'),
          ),
        ),
      );
    }
  }
});

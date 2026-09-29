import {spawnSync} from 'node:child_process';
import {test} from 'node:test';
import {copyFile, mkdir, mkdtemp, rm, writeFile} from 'node:fs/promises';
import {assert, assertMatch} from '@std/assert';
import {fromFileUrl, join} from '@std/path';

const root = fromFileUrl(new URL('../', import.meta.url));
const project = join(root, 'tools/ruff');
const config = join(root, 'ruff.toml');

function ruff(args: string[], cwd = root) {
  const result = spawnSync(
    'uv',
    [
      'run',
      '--project',
      project,
      '--frozen',
      '--offline',
      '--no-sync',
      'ruff',
      ...args,
    ],
    {cwd, stdio: ['ignore', 'pipe', 'pipe']},
  );
  if (result.error) throw result.error;
  return {
    success: result.status === 0,
    stdout: result.stdout ?? Buffer.alloc(0),
    stderr: result.stderr ?? Buffer.alloc(0),
  };
}

function output(result: ReturnType<typeof ruff>) {
  return (
    new TextDecoder().decode(result.stdout) +
    new TextDecoder().decode(result.stderr)
  );
}

test('Ruff config enforces style, formatting, boundaries and vendor exclusions', async () => {
  const temp = await mkdtemp('/tmp/ruff-test-');
  try {
    const publicFunction = join(temp, 'public_api.py');
    await writeFile(
      publicFunction,
      '"""Synthetic module."""\n\ndef public_api():\n    return None\n',
    );
    const missingDoc = await ruff([
      'check',
      '--no-cache',
      '--config',
      config,
      publicFunction,
    ]);
    assert(!missingDoc.success);
    assertMatch(output(missingDoc), /D103/);

    const dummyArguments = join(temp, 'dummy_arguments.py');
    await writeFile(
      dummyArguments,
      '"""Synthetic module."""\n\n' +
        'def _allows(unused_value):\n    return None\n\n' +
        'def _fails(_value):\n    return None\n',
    );
    const dummyArgumentsResult = await ruff([
      'check',
      '--no-cache',
      '--config',
      config,
      dummyArguments,
    ]);
    const dummyArgumentsOutput = output(dummyArgumentsResult);
    assert(!dummyArgumentsResult.success);
    assert(!dummyArgumentsOutput.includes('unused_value'));
    assertMatch(dummyArgumentsOutput, /ARG001.*_value/);

    const lineAtLimit = join(temp, 'line_at_limit.py');
    const lineOverLimit = join(temp, 'line_over_limit.py');
    const line = (length: number) => '# ' + 'x'.repeat(length - 2) + '\n';
    await writeFile(lineAtLimit, '"""Synthetic module."""\n' + line(80));
    await writeFile(lineOverLimit, '"""Synthetic module."""\n' + line(81));
    const boundaryPass = await ruff([
      'check',
      '--no-cache',
      '--config',
      config,
      lineAtLimit,
    ]);
    assert(boundaryPass.success, output(boundaryPass));
    const boundaryFail = await ruff([
      'check',
      '--no-cache',
      '--config',
      config,
      lineOverLimit,
    ]);
    assert(!boundaryFail.success);
    assertMatch(output(boundaryFail), /E501/);

    const testFunction = join(temp, 'test_example.py');
    await writeFile(testFunction, 'def test_example():\n    assert True\n');
    const testPass = await ruff([
      'check',
      '--no-cache',
      '--config',
      config,
      testFunction,
    ]);
    assert(testPass.success, output(testPass));

    const unsortedImports = join(temp, 'unsorted_imports.py');
    await writeFile(unsortedImports, 'import os\nimport json\n');
    const importOrderFail = await ruff([
      'check',
      '--no-cache',
      '--config',
      config,
      unsortedImports,
    ]);
    assert(!importOrderFail.success);
    assertMatch(output(importOrderFail), /I001/);

    const unformatted = join(temp, 'unformatted.py');
    await writeFile(unformatted, 'value=[1,2]\n');
    const formatFail = await ruff([
      'format',
      '--check',
      '--no-cache',
      '--config',
      config,
      unformatted,
    ]);
    assert(!formatFail.success);

    const formatAtLimit = join(temp, 'format_at_limit.py');
    const formatOverLimit = join(temp, 'format_over_limit.py');
    const call = (length: number) =>
      `result = function("${'x'.repeat(length - 21)}")\n`;
    await writeFile(formatAtLimit, call(80));
    await writeFile(formatOverLimit, call(81));
    const formatBoundaryPass = await ruff([
      'format',
      '--check',
      '--no-cache',
      '--config',
      config,
      formatAtLimit,
    ]);
    assert(formatBoundaryPass.success, output(formatBoundaryPass));
    const formatBoundaryFail = await ruff([
      'format',
      '--check',
      '--no-cache',
      '--config',
      config,
      formatOverLimit,
    ]);
    assert(!formatBoundaryFail.success);

    const isolatedConfig = join(temp, 'ruff.toml');
    const vendor = join(temp, '.specify/extensions');
    const vendorFile = join(vendor, 'synthetic.py');
    const specifyScript = join(temp, '.specify/scripts/synthetic.py');
    const repositoryFile = join(temp, 'synthetic.py');
    await copyFile(config, isolatedConfig);
    await mkdir(vendor, {recursive: true});
    await mkdir(join(temp, '.specify/scripts'), {recursive: true});
    await writeFile(vendorFile, 'def vendor_api():\n    return None\n');
    await writeFile(
      specifyScript,
      'def repository_owned():\n    return None\n',
    );
    await writeFile(repositoryFile, 'def repository_api():\n    return None\n');
    const shownFiles = await ruff(
      ['check', '--show-files', '--no-cache', '--config', isolatedConfig, '.'],
      temp,
    );
    assert(shownFiles.success, output(shownFiles));
    assert(!output(shownFiles).includes(vendorFile));
    assert(output(shownFiles).includes(specifyScript), output(shownFiles));
    assert(output(shownFiles).includes(repositoryFile), output(shownFiles));
  } finally {
    await rm(temp, {recursive: true});
  }
});

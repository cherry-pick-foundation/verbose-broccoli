import { assert, assertMatch } from '@std/assert';
import { fromFileUrl, join } from '@std/path';

const root = fromFileUrl(new URL('../', import.meta.url));
const project = join(root, 'tools/ruff');
const config = join(root, 'ruff.toml');

async function ruff(args: string[], cwd = root) {
  return await new Deno.Command('uv', {
    args: [
      'run',
      '--project',
      project,
      '--frozen',
      '--offline',
      '--no-sync',
      'ruff',
      ...args,
    ],
    cwd,
    stdout: 'piped',
    stderr: 'piped',
  }).output();
}

function output(result: Deno.CommandOutput) {
  return new TextDecoder().decode(result.stdout) +
    new TextDecoder().decode(result.stderr);
}

Deno.test('Ruff config enforces style, formatting, boundaries and vendor exclusions', async () => {
  const temp = await Deno.makeTempDir({
    dir: '/tmp',
    prefix: 'ruff-test-',
  });
  try {
    const publicFunction = join(temp, 'public_api.py');
    await Deno.writeTextFile(
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

    const lineAtLimit = join(temp, 'line_at_limit.py');
    const lineOverLimit = join(temp, 'line_over_limit.py');
    const line = (length: number) => '# ' + 'x'.repeat(length - 2) + '\n';
    await Deno.writeTextFile(
      lineAtLimit,
      '"""Synthetic module."""\n' + line(80),
    );
    await Deno.writeTextFile(
      lineOverLimit,
      '"""Synthetic module."""\n' + line(81),
    );
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
    await Deno.writeTextFile(
      testFunction,
      'def test_example():\n    assert True\n',
    );
    const testPass = await ruff([
      'check',
      '--no-cache',
      '--config',
      config,
      testFunction,
    ]);
    assert(testPass.success, output(testPass));

    const unformatted = join(temp, 'unformatted.py');
    await Deno.writeTextFile(unformatted, 'value=[1,2]\n');
    const formatFail = await ruff([
      'format',
      '--check',
      '--no-cache',
      '--config',
      config,
      unformatted,
    ]);
    assert(!formatFail.success);

    const isolatedConfig = join(temp, 'ruff.toml');
    const vendor = join(temp, '.specify');
    const vendorFile = join(vendor, 'synthetic.py');
    await Deno.copyFile(config, isolatedConfig);
    await Deno.mkdir(vendor);
    await Deno.writeTextFile(
      vendorFile,
      'def vendor_api():\n    return None\n',
    );
    const shownFiles = await ruff([
      'check',
      '--show-files',
      '--no-cache',
      '--config',
      isolatedConfig,
      '.',
    ], temp);
    assert(shownFiles.success, output(shownFiles));
    assert(!output(shownFiles).includes(vendorFile));
  } finally {
    await Deno.remove(temp, { recursive: true });
  }
});
